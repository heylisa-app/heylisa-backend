# app/services/plan_executor.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from asyncpg import Connection
import time

from app.services.context_loader import load_context_light
from app.services.quota import get_quota_status
from app.tools.web_search import WebSearchTool
from app.agents.response_writer import ResponseWriterAgent
from app.agents.node_registry import NODE_TYPE_WHITELIST
from app.core.chat_logger import chat_logger


SAFE_FALLBACK_ANSWER = "Désolé — j’ai eu un souci technique. Réessaie dans quelques secondes."
MAX_ANSWER_CHARS = 4000  # garde-fou anti pavé (ajuste si besoin)


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

                    chat_logger.info(
                        "chat.node.end",
                        conversation_id=str(self.conversation_id),
                        public_user_id=str(self.public_user_id),
                        node_id=str(node_id),
                        node_type=node_type,
                        ok=ok_val,
                        error=err_val,
                        duration_ms=int((time.perf_counter() - t0) * 1000),
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

        if ntype == "agent.response_writer":
            # On injecte automatiquement ctx/quota/web si présents
            ctx_node_id = self._find_first_node_id("tool.db_load_context")
            quota_node_id = self._find_first_node_id("tool.quota_check")
            web_node_id = self._find_first_node_id("tool.web_search")

            ctx = (self.out.get(ctx_node_id) or {}).get("context") if ctx_node_id else None
            quota = self.out.get(quota_node_id) if quota_node_id else None
            web = self.out.get(web_node_id) if web_node_id else None

            return await self.response_writer.run(
                user_message=self.user_message,
                intent=str(inputs.get("intent") or "general_question"),
                language=str(inputs.get("language") or "fr"),
                tone=str(inputs.get("tone") or "warm"),
                include_smalltalk=bool(inputs.get("include_smalltalk") or False),
                need_web=bool(inputs.get("need_web") or False),
                context=ctx or {},
                quota=quota or {},
                web=web or {},
            )

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