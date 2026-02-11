# app/services/plan_executor.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from asyncpg import Connection
import time

import os, json, hashlib
from pathlib import Path

from app.services.context_loader import load_context_light
from app.services.quota import get_quota_status
from app.tools.web_search import WebSearchTool
from app.agents.response_writer import ResponseWriterAgent
from app.agents.node_registry import NODE_TYPE_WHITELIST
from app.core.chat_logger import chat_logger


SAFE_FALLBACK_ANSWER = "Désolé — j’ai eu un souci technique. Réessaie dans quelques secondes."
MAX_ANSWER_CHARS = 4000  # garde-fou anti pavé (ajuste si besoin)
DOCS_CHUNKS_MAX = 5
DOCS_SCOPES_MAX = 5

DEBUG_PIPELINE = os.getenv("DEBUG_PIPELINE", "0") == "1"
DEBUG_DUMP_PROMPTS = os.getenv("DEBUG_DUMP_PROMPTS", "0") == "1"
DEBUG_DUMP_DIR = Path(os.getenv("DEBUG_DUMP_DIR", ".debug"))

def _sha256(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]

def _preview(obj: Any, max_chars: int = 500) -> Any:
    """
    Compacte pour logs: évite les pavés + évite les données sensibles par défaut.
    """
    try:
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            s = str(obj)
            return s if len(s) <= max_chars else (s[: max_chars - 1] + "…")
        if isinstance(obj, dict):
            out = {}
            for k, v in list(obj.items())[:30]:
                # masque soft sur clés classiques
                lk = str(k).lower()
                if any(x in lk for x in ["token", "key", "secret", "password", "authorization"]):
                    out[k] = "***"
                else:
                    out[k] = _preview(v, max_chars=180)
            return out
        if isinstance(obj, list):
            return [_preview(x, max_chars=180) for x in obj[:20]]
        # fallback
        s = str(obj)
        return s if len(s) <= max_chars else (s[: max_chars - 1] + "…")
    except Exception:
        return {"_preview_error": True}

def _dump_text(*, conversation_id: str, node_id: str, name: str, text: str) -> str:
    """
    Sauvegarde le texte complet en fichier (local) et retourne le path.
    """
    DEBUG_DUMP_DIR.mkdir(parents=True, exist_ok=True)
    folder = DEBUG_DUMP_DIR / str(conversation_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{node_id}_{name}.txt"
    path.write_text(text or "", encoding="utf-8")
    return str(path)

def _extract_fact_keys(ctx: Any) -> List[str]:
    """
    Extrait des fact_keys de manière robuste.
    Supporte :
    - ctx["facts_store"]["items"] = [{fact_key, ...}, ...]
    - ctx["facts_store"]["keys"] = [...]
    - ctx["user_facts"] (si jamais un jour devient une liste)
    - autres schémas legacy éventuels
    """
    if not isinstance(ctx, dict):
        return []

    keys: List[str] = []

    # ✅ Nouveau: facts_store (ton schéma actuel)
    fs = ctx.get("facts_store")
    if isinstance(fs, dict):
        # 1) keys déjà pré-calculées
        if isinstance(fs.get("keys"), list):
            for k in fs.get("keys")[:200]:
                if isinstance(k, str) and k:
                    keys.append(k)

        # 2) items complets
        items = fs.get("items")
        if isinstance(items, list):
            for f in items[:200]:
                if isinstance(f, dict):
                    k = f.get("fact_key") or f.get("key")
                    if isinstance(k, str) and k:
                        keys.append(k)

    # Legacy candidates (si un jour tu changes le format)
    candidates = [
        ctx.get("user_facts"),
        ctx.get("facts"),
        (ctx.get("user") or {}).get("facts"),
        (ctx.get("memory") or {}).get("facts"),
        (ctx.get("profile") or {}).get("facts"),
    ]

    for c in candidates:
        if isinstance(c, list):
            for f in c[:200]:
                if isinstance(f, dict):
                    k = f.get("fact_key") or f.get("key")
                    if isinstance(k, str) and k:
                        keys.append(k)

    return sorted(set(keys))


def _ctx_summary(ctx: Any, *, level: str) -> Dict[str, Any]:
    """
    Résumé safe pour logs (pas de valeurs, que des métadonnées).
    """
    top_keys = list(ctx.keys())[:30] if isinstance(ctx, dict) else []

    scopes_count = 0
    if isinstance(ctx, dict):
        scopes = ((ctx.get("docs") or {}).get("scopes_all") if isinstance(ctx.get("docs"), dict) else None)
        if isinstance(scopes, list):
            scopes_count = len(scopes)

    fact_keys = _extract_fact_keys(ctx)

    facts_store_count = 0
    facts_store_has_any_value = False

    if isinstance(ctx, dict):
        fs = ctx.get("facts_store")
        if isinstance(fs, dict):
            facts_store_count = int(fs.get("count") or 0)
            items = fs.get("items")
            if isinstance(items, list):
                # indicateur booléen, sans logguer les valeurs
                for it in items[:50]:
                    if isinstance(it, dict) and it.get("value") not in (None, "", [] , {}):
                        facts_store_has_any_value = True
                        break

    return {
        "ctx_level": level,
        "ctx_keys_top": top_keys[:20],
        "facts_count": len(fact_keys),
        "facts_keys_sample": fact_keys[:12],
        "facts_store_count": facts_store_count,
        "facts_store_has_any_value": facts_store_has_any_value,
        "docs_scopes_count": scopes_count,
    }

def _normalize_answer(x: Any) -> str:
    """
    Verrou: retourne toujours une string "safe" (answer only).
    - jamais None
    - jamais vide
    - jamais trop longue
    """
    try:
        s = str(x or "").strip()
    except Exception:
        s = ""

    if not s:
        return SAFE_FALLBACK_ANSWER

    # Anti-crash front / anti pavé
    if len(s) > MAX_ANSWER_CHARS:
        s = s[: MAX_ANSWER_CHARS - 1].rstrip() + "…"

    return s


class PlanExecutionError(RuntimeError):
    pass


class PlanExecutor:
    """
    Exécute un plan DAG renvoyé par l'Orchestrator.
    v0: exécution séquentielle (on ignore parallel_group pour l'instant, mais on respecte depends_on).
    """

    def __init__(
        self,
        *,
        conn: Connection,
        llm: Any,  # LLMRuntime
        public_user_id: str,
        conversation_id: str,
        user_message: str,
    ) -> None:
        self.conn = conn
        self.llm = llm
        self.public_user_id = public_user_id
        self.conversation_id = conversation_id
        self.user_message = user_message

        # tools/agents
        self.web_search_tool = WebSearchTool(llm)
        self.response_writer = ResponseWriterAgent(llm)

        # node outputs
        self.out: Dict[str, Any] = {}

    async def run(self, *, plan: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(plan, dict):
            raise PlanExecutionError("PLAN_NOT_A_DICT")

        exec_start = time.perf_counter()

        nodes = plan.get("nodes")
        if not isinstance(nodes, list) or not nodes:
            raise PlanExecutionError("PLAN_NODES_MISSING")

        chat_logger.info(
            "chat.executor.run_start",
            conversation_id=str(self.conversation_id),
            public_user_id=str(self.public_user_id),
            nodes_count=len(nodes),
            node_ids=[str(n.get("id")) for n in nodes if isinstance(n, dict) and n.get("id")][:12],
        )

        # Exécution topo très simple : tant qu'il reste des nodes exécutables
        pending: Dict[str, Dict[str, Any]] = {}
        for n in nodes:
            if isinstance(n, dict) and n.get("id"):
                pending[str(n["id"])] = n

        executed: set[str] = set()

        while pending:
            progressed = False

            for node_id, node in list(pending.items()):
                deps = node.get("depends_on") or []
                if isinstance(deps, list) and all(d in executed for d in deps):
                    node_type = str((node or {}).get("type") or "")
                    node_inputs = (node or {}).get("inputs") or {}
                    if not isinstance(node_inputs, dict):
                        node_inputs = {}

                    t0 = time.perf_counter()
                    chat_logger.info(
                        "chat.node.start",
                        conversation_id=str(self.conversation_id),
                        public_user_id=str(self.public_user_id),
                        node_id=str(node_id),
                        node_type=node_type,
                        depends_on=deps,
                        inputs_keys=list(node_inputs.keys())[:20],
                        inputs_preview=_preview(node_inputs) if DEBUG_PIPELINE else None,
                    )

                    try:
                        res = await self._run_one(node)
                    except Exception as e:
                        chat_logger.error(
                            "chat.node.error",
                            conversation_id=str(self.conversation_id),
                            public_user_id=str(self.public_user_id),
                            node_id=str(node_id),
                            node_type=node_type,
                            error=str(e)[:300],
                            duration_ms=int((time.perf_counter() - t0) * 1000),
                            exc_info=True,
                        )
                        raise

                    # mini extraction ok/error
                    ok_val = None
                    err_val = None
                    if isinstance(res, dict):
                        ok_val = res.get("ok")
                        err_val = res.get("error")

                    out_preview = _preview(res) if DEBUG_PIPELINE else None

                    chat_logger.info(
                        "chat.node.end",
                        conversation_id=str(self.conversation_id),
                        public_user_id=str(self.public_user_id),
                        node_id=str(node_id),
                        node_type=node_type,
                        ok=ok_val,
                        error=err_val,
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        output_preview=out_preview,
                    )

                    self.out[node_id] = res
                    executed.add(node_id)
                    del pending[node_id]
                    progressed = True

            if not progressed:
                chat_logger.error(
                    "chat.executor.stuck",
                    conversation_id=str(self.conversation_id),
                    public_user_id=str(self.public_user_id),
                    pending_ids=list(pending.keys())[:20],
                )
                # cycle ou deps manquantes
                raise PlanExecutionError(f"PLAN_STUCK_UNRESOLVED_DEPS: {list(pending.keys())}")

        # Convention: la réponse finale doit être dans la sortie du node response_writer
        # On prend le dernier node de type agent.response_writer si possible.
        final = None
        for n in nodes[::-1]:
            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                final = self.out.get(str(n.get("id")))
                break

        # Convention: la réponse finale doit être dans la sortie du node response_writer
        # Verrou: "answer only" => on sort TOUJOURS une string safe.
        answer_raw = None
        if isinstance(final, dict):
            answer_raw = final.get("answer")

        answer = _normalize_answer(answer_raw)

        debug_pack = {
            "node_outputs": self._debug_compact_outputs(),
        }

        # Indicateurs utiles pour diagnostiquer sans casser le front
        if answer == SAFE_FALLBACK_ANSWER:
            debug_pack["answer_fallback_used"] = True
            debug_pack["answer_raw_type"] = type(answer_raw).__name__ if answer_raw is not None else "None"
        if isinstance(answer_raw, str) and len(answer_raw.strip()) > MAX_ANSWER_CHARS:
            debug_pack["answer_truncated"] = True
            debug_pack["answer_raw_len"] = len(answer_raw.strip())

        chat_logger.info(
            "chat.executor.run_end",
            conversation_id=str(self.conversation_id),
            public_user_id=str(self.public_user_id),
            duration_ms=int((time.perf_counter() - exec_start) * 1000),
            answer_len=len(answer or ""),
        )

        return {
            "answer": answer,
            "debug": debug_pack,
        }

    async def _run_one(self, node: Dict[str, Any]) -> Dict[str, Any]:
        ntype = node.get("type")

        if ntype not in NODE_TYPE_WHITELIST:
            return {"ok": False, "error": "NODE_TYPE_NOT_ALLOWED", "type": str(ntype)}
        inputs = node.get("inputs") or {}
        if not isinstance(inputs, dict):
            inputs = {}

        if ntype == "tool.db_load_context":
            # v0: on utilise load_context_light pour tous les niveaux (on enrichira après)
            level = str(inputs.get("level") or "medium")
            ctx = await load_context_light(self.conn, str(self.public_user_id), self.conversation_id)

            # ✅ LOG SAFE (pas de valeurs, juste métadonnées)
            try:
                summary = _ctx_summary(ctx, level=level)
                chat_logger.info(
                    "chat.ctx.summary",
                    conversation_id=str(self.conversation_id),
                    public_user_id=str(self.public_user_id),
                    **summary,
                )
            except Exception as _e:
                chat_logger.info(
                    "chat.ctx.summary",
                    conversation_id=str(self.conversation_id),
                    public_user_id=str(self.public_user_id),
                    ctx_level=level,
                    ctx_summary_error=True,
                )

            return {"ok": True, "level": level, "context": ctx}

        if ntype == "tool.quota_check":
            status = await get_quota_status(self.conn, str(self.public_user_id))
            return {
                "ok": True,
                "is_pro": bool(status.is_pro),
                "used": int(status.used),
                "limit": int(status.limit),
                "state": str(status.state),
                "paywall_should_show": (not status.is_pro) and (status.used >= status.limit),
            }

        if ntype == "tool.web_search":
            prompt = inputs.get("prompt")
            language = str(inputs.get("language") or "fr")
            res = await self.web_search_tool.run(prompt=str(prompt or ""), language=language)
            return res

        if ntype == "tool.docs_chunks":
            scopes = inputs.get("scopes") or []
            if not isinstance(scopes, list):
                scopes = []
            scopes = [s.strip() for s in scopes if isinstance(s, str) and s.strip()][:DOCS_SCOPES_MAX]

            if not scopes:
                return {"ok": True, "scopes": [], "chunks": []}

            # ✅ DB as source of truth (avoid ctx mismatch)
            rows = await self.conn.fetch(
                """
                select doc_scope, chunk_title, chunk_content
                from public.lisa_service_docs
                where doc_scope = any($1::text[])
                order by order_key asc
                limit 50
                """,
                scopes,
            )

            chunks: List[Dict[str, Any]] = []
            for r in rows:
                txt = (r["chunk_content"] or "").strip()
                if not txt:
                    continue
                chunks.append({
                    "scope": r["doc_scope"],
                    "title": r["chunk_title"],
                    "text": txt,
                    "source": "lisa_service_docs",
                })

            chat_logger.info(
                "chat.docs_chunks.db",
                conversation_id=str(self.conversation_id),
                public_user_id=str(self.public_user_id),
                requested_scopes=scopes,
                rows_count=len(rows),
                chunks_count=len(chunks),
            )

            return {"ok": True, "scopes": scopes, "chunks": chunks[:DOCS_CHUNKS_MAX]}

        if ntype == "agent.response_writer":
            # On injecte automatiquement ctx/quota/web si présents
            ctx_node_id = self._find_first_node_id("tool.db_load_context")
            quota_node_id = self._find_first_node_id("tool.quota_check")
            web_node_id = self._find_first_node_id("tool.web_search")
            docs_node_id = self._find_first_node_id("tool.docs_chunks")

            ctx = (self.out.get(ctx_node_id) or {}).get("context") if ctx_node_id else None
            quota = self.out.get(quota_node_id) if quota_node_id else None
            web = self.out.get(web_node_id) if web_node_id else None
            docs_chunks = self.out.get(docs_node_id) if docs_node_id else None

            # Pass-through des inputs orchestrateur (mode, gates, eligibility, etc.)
            rw_inputs = dict(
                user_message=self.user_message,
                intent=str(inputs.get("intent") or "general_question"),
                mode=str(inputs.get("mode") or "normal"),
                language=str(inputs.get("language") or "fr"),
                tone=str(inputs.get("tone") or "warm"),
                need_web=bool(inputs.get("need_web") or False),
                docs_chunks=docs_chunks or {},

                smalltalk_target_key=inputs.get("smalltalk_target_key"),
                intent_eligible=bool(inputs.get("intent_eligible", True)),
                intent_block_reason=inputs.get("intent_block_reason"),
                transition_window=bool(inputs.get("transition_window", False)),
                transition_reason=inputs.get("transition_reason"),

                context=ctx or {},
                quota=quota or {},
                web=web or {},
            )

            # logs preview inputs (sans le message complet si tu veux)
            # ctx meta (safe)
            ctx_level = str((self.out.get(ctx_node_id) or {}).get("level") or "unknown") if ctx_node_id else "none"
            ctx_summary = _ctx_summary(rw_inputs["context"], level=ctx_level) if rw_inputs.get("context") else {"facts_count": 0}

            chat_logger.info(
                "chat.response_writer.call",
                conversation_id=str(self.conversation_id),
                public_user_id=str(self.public_user_id),
                node_id=str(node.get("id") or "D"),
                intent=rw_inputs["intent"],
                mode=rw_inputs["mode"],
                language=rw_inputs["language"],
                need_web=rw_inputs["need_web"],
                transition_window=bool(rw_inputs.get("transition_window", False)),
                transition_reason=rw_inputs.get("transition_reason"),
                ctx_level=ctx_level,
                facts_count=int(ctx_summary.get("facts_count", 0)),
                facts_keys_sample=ctx_summary.get("facts_keys_sample", [])[:12],
                has_ctx=bool(rw_inputs["context"]),
                has_quota=bool(rw_inputs["quota"]),
                has_web=bool(rw_inputs["web"]),
                has_docs=bool(docs_chunks and isinstance(docs_chunks, dict) and docs_chunks.get("chunks")),
            )

            res = await self.response_writer.run(**rw_inputs)

            # option: dump prompts complets si ResponseWriter les expose en debug (voir note plus bas)
            return res

        # Unknown node
        return {"ok": False, "error": "UNKNOWN_NODE_TYPE", "type": str(ntype)}

    def _find_first_node_id(self, node_type: str) -> Optional[str]:
        # node_outputs dict only has executed nodes; we infer by looking at stored outputs keys + their node types not stored
        # simplest: rely on common ids A/B/C/D — fallback to those
        if node_type == "tool.db_load_context":
            return "A" if "A" in self.out else None
        if node_type == "tool.quota_check":
            return "B" if "B" in self.out else None
        if node_type == "tool.web_search":
            return "C" if "C" in self.out else None
        if node_type == "tool.docs_chunks":
            return "S" if "S" in self.out else None
        return None

    def _debug_compact_outputs(self) -> Dict[str, Any]:
        # évite d'exploser les logs: on garde ok/error + quelques champs
        compact: Dict[str, Any] = {}
        for k, v in self.out.items():
            if not isinstance(v, dict):
                compact[k] = {"type": type(v).__name__}
                continue
            keep = {}
            for key in ("ok", "error", "duration_ms", "provider", "model", "state", "paywall_should_show"):
                if key in v:
                    keep[key] = v[key]
            compact[k] = keep
        return compact