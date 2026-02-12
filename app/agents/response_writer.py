# app/agents/response_writer.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.llm.runtime import LLMRuntime
from app.prompts.loader import load_lisa_system_prompts
from app.prompts.user.loader import load_user_prompt_block
from app.core.chat_logger import chat_logger

from uuid import UUID
from datetime import datetime, date
from decimal import Decimal



SYSTEM_RESPONSE_WRITER_PROMPT = """
Tu es Lisa, l'assistante IA exécutive de HeyLisa.

OBJECTIF
- Produire une réponse utile, humaine, claire, actionnable.
- Ton = conversationnel, direct, naturel. Zéro blabla.

"""

SOURCES_BLOCK_HEADER = "📌 Sources"


def _safe_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return ""

def _json_safe(v):
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dict):
        return {k: _json_safe(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_json_safe(x) for x in v]
    return v

def _pick(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def _compact_context(ctx: Dict[str, Any], max_chars: int = 3500) -> str:
    if not isinstance(ctx, dict):
        return "{}"
    import json

    s = json.dumps(_json_safe(ctx), ensure_ascii=False)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."


def _domain_from_url(url: str) -> str:
    # mini extraction domaine (stable, sans libs)
    try:
        u = (url or "").strip()
        if not u:
            return ""
        u = u.replace("https://", "").replace("http://", "")
        u = u.split("/")[0]
        return u.lower()
    except Exception:
        return ""


class ResponseWriterAgent:
    """
    Agent: response_writer (Lisa)

    Input expected (from execution engine):
      - user_message: str
      - intent: str
      - language: str
      - tone: str ("warm"|"neutral"|"calm"...)
      - need_web: bool
      - context: dict (from tool.db_load_context)
      - quota: dict (from tool.quota_check) optional
      - web: dict (from tool.web_search) optional
          { ok, answer, sources:[{title,url}], ... }

    Output:
      { ok: bool, answer: str, debug: dict }
    """

    def __init__(self, llm: LLMRuntime):
        self.llm = llm

    async def run(
        self,
        *,
        user_message: str,
        intent: str,
        language: str = "fr",
        tone: str = "warm",
        need_web: bool = False,
        mode: str = "normal",
        smalltalk_target_key: Optional[str] = None,
        transition_window: bool = False,
        transition_reason: Optional[str] = None,
        intent_eligible: bool = True,
        intent_block_reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        quota: Optional[Dict[str, Any]] = None,
        web: Optional[Dict[str, Any]] = None,
        # compat: si un autre appel utilise encore web_search=
        web_search: Optional[Dict[str, Any]] = None,
        docs_chunks: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_ts = time.time()

        ctx = context or {}
        q = quota or {}
        # priorité: web= (PlanExecutor), sinon web_search= (compat)
        ws = web if isinstance(web, dict) and web else (web_search or {})

        # --- Extract minimal user prefs from context (optional) ---
        settings = _pick(ctx, "settings", {}) or {}
        use_tu_raw = _pick(settings, "use_tu_form", None)
        use_tu_form = True if use_tu_raw is True else False if use_tu_raw is False else False
        use_tu_known = (use_tu_raw is True) or (use_tu_raw is False)
        user_name = _pick(_pick(ctx, "user", {}), "first_name", None)
        intro_smalltalk_turns = int(_pick(settings, "intro_smalltalk_turns", 0) or 0)
        intro_smalltalk_done = bool(_pick(settings, "intro_smalltalk_done", False))

        # --- Quota info (optional) ---
        paywall_should_show = bool(_pick(q, "paywall_should_show", False))
        quota_state = _pick(q, "state", None)
        quota_used = _pick(q, "used", None)
        quota_limit = _pick(q, "limit", None)
        is_pro = bool(_pick(q, "is_pro", False))

        # --- Soft warning: last free message (only if non-pro) ---
        should_soft_warn = (
            (not is_pro)
            and (quota_used is not None)
            and (quota_limit is not None)
            and (int(quota_used) == int(quota_limit) - 1)
        )

        # --- Web search block (optional) ---
        ws_ok = bool(_pick(ws, "ok", False))
        ws_answer = _pick(ws, "answer", "")
        ws_sources = _pick(ws, "sources", [])
        if not isinstance(ws_sources, list):
            ws_sources = []

        # compact ctx
        ctx_text = _compact_context(ctx)

        # --- Build “sources digest” (titles + domains only) ---
        sources_digest_lines = []
        for s in ws_sources[:5]:
            if not isinstance(s, dict):
                continue
            title = _safe_str(s.get("title") or "").strip()
            url = _safe_str(s.get("url") or "").strip()
            dom = _domain_from_url(url)
            if title:
                sources_digest_lines.append(f"- {title} — {dom}" if dom else f"- {title}")
        sources_digest = "\n".join(sources_digest_lines) if sources_digest_lines else "(none)"

        dc = docs_chunks or {}
        dc_ok = bool(_pick(dc, "ok", False))
        dc_scopes = _pick(dc, "scopes", [])
        dc_chunks = _pick(dc, "chunks", [])
        chat_logger.info(
            "chat.response_writer.docs_chunks",
            dc_ok=dc_ok,
            dc_scopes=dc_scopes[:3] if isinstance(dc_scopes, list) else [],
            dc_chunks_count=len(dc_chunks) if isinstance(dc_chunks, list) else -1,
            dc_first_preview=(_safe_str((dc_chunks[0] or {}).get("text") if isinstance(dc_chunks, list) and dc_chunks else "")[:220]),
        )

        if not isinstance(dc_scopes, list):
            dc_scopes = []
        if not isinstance(dc_chunks, list):
            dc_chunks = []

        docs_snippets = []
        for ch in dc_chunks[:8]:
            if not isinstance(ch, dict):
                continue
            txt = _safe_str(ch.get("text") or ch.get("content") or "").strip()
            if not txt:
                continue
            # hard cap par chunk
            if len(txt) > 600:
                txt = txt[:599] + "…"
            docs_snippets.append(f"- {txt}")

        docs_block = "\n".join(docs_snippets) if docs_snippets else "(none)"

        # --- Intent prompt block (ONE mechanism for ALL intents) ---
        # On injecte uniquement les variables nécessaires au bloc d'intent.
        # Si l'intent n'a pas de bloc dans le registry, load_user_prompt_block doit renvoyer "" (ou fallback safe).
        intent_vars: Dict[str, str] = {}

        # Vars communes qui peuvent servir à plusieurs intents
        intent_vars.update({
            "transition_window": ("true" if transition_window else "false"),
            "transition_reason": (_safe_str(transition_reason)[:80] if transition_reason else "null"),
        })

        # Vars par intent (clean)
        if intent == "smalltalk_intro":
            intent_vars.update({
                "smalltalk_target_key": (_safe_str(smalltalk_target_key) if smalltalk_target_key else "null"),
            })

        if intent == "discovery":
            gates = _pick(ctx, "gates", {}) or {}
            intent_vars.update({
                "discovery_forced": ("true" if bool(gates.get("discovery_forced")) else "false"),
                "discovery_status": (_safe_str(gates.get("discovery_status") or "null")),
            })

        # (Option) si tu as des intents qui doivent afficher l'éligibilité
        if intent in ("action_request", "professional_request", "deep_work"):
            intent_vars.update({
                "intent_eligible": ("true" if intent_eligible else "false"),
                "intent_block_reason": (_safe_str(intent_block_reason)[:80] if intent_block_reason else "null"),
            })

        if intent == "action_request":
            action_state = _pick(ctx, "action_state", {}) or {}
            action_req = action_state.get("action_required_integrations") or {}

            # Connected integrations (set)
            connected = set()
            ci = action_state.get("connected_integrations") or []
            if isinstance(ci, list):
                connected = { _safe_str(x).strip() for x in ci if isinstance(x, str) and x.strip() }

            # Compact map "action:integ+integ | ..."
            pairs = []
            if isinstance(action_req, dict):
                for k, v in list(action_req.items())[:50]:
                    if isinstance(v, list) and v:
                        pairs.append(f"{_safe_str(k)}:{'+'.join([_safe_str(x) for x in v[:6]])}")
                    else:
                        pairs.append(f"{_safe_str(k)}:none")
            action_map_compact = " | ".join(pairs) if pairs else "none"

            # ✅ Missing integrations per action (req - connected)
            missing_by_action = {}
            if isinstance(action_req, dict):
                for ak, reqs in action_req.items():
                    akey = _safe_str(ak).strip()
                    if not akey:
                        continue
                    req_list = []
                    if isinstance(reqs, list):
                        req_list = [_safe_str(x).strip() for x in reqs if isinstance(x, str) and x.strip()]
                    missing = [x for x in req_list if x not in connected]
                    missing_by_action[akey] = missing

            # ✅ Union (useful for "connect X now")
            missing_all = sorted({x for v in missing_by_action.values() for x in (v or []) if isinstance(x, str) and x.strip()})

            # "email_read:gmail(missing) ; todoist_add:none"
            missing_compact_parts = []
            for ak, miss in list(missing_by_action.items())[:50]:
                if miss:
                    missing_compact_parts.append(f"{ak}:{'+'.join(miss[:6])}")
                else:
                    missing_compact_parts.append(f"{ak}:none")
            missing_map_compact = " | ".join(missing_compact_parts) if missing_compact_parts else "none"

            intent_vars.update({
                "has_paid_agent": ("true" if bool(action_state.get("has_paid_agent")) else "false"),
                "can_action_request": ("true" if bool(action_state.get("can_action_request")) else "false"),
                "executable_actions": ", ".join([_safe_str(x) for x in (action_state.get("executable_actions") or [])[:80]]) or "none",
                "connected_integrations": ", ".join(sorted(list(connected))[:50]) or "none",
                "required_integrations": ", ".join([_safe_str(x) for x in (action_state.get("required_integrations") or [])[:50]]) or "none",
                "action_required_integrations_map": action_map_compact,

                # ✅ new vars
                "missing_integrations_all": ", ".join(missing_all[:50]) or "none",
                "missing_integrations_map": missing_map_compact,
            })

        # Vars spécifiques smalltalk_intro (si intent déclenché)
        intent_vars.update({
            "smalltalk_target_key": (_safe_str(smalltalk_target_key) if smalltalk_target_key else "null"),
        })

        # Vars spécifiques discovery (si intent déclenché)
        gates = _pick(ctx, "gates", {}) or {}
        intent_vars.update({
            "discovery_forced": ("true" if bool(gates.get("discovery_forced")) else "false"),
            "discovery_status": (_safe_str(gates.get("discovery_status") or "null")),
        })

        # ✅ Injection : un seul bloc, activé uniquement si intent connu du registry
        intent_block = load_user_prompt_block(intent=intent, vars=intent_vars).strip()

        # --- Paywall block (optional) ---
        paywall_block = ""
        if should_soft_warn:
            paywall_block = load_user_prompt_block(intent="paywall_soft_warning", vars={}).strip()

        chat_logger.info(
            "chat.response_writer.prompt_flags",
            intent=intent,
            mode=mode,
            quota_used=quota_used,
            quota_limit=quota_limit,
            quota_state=quota_state,
            is_pro=is_pro,
            should_soft_warn=should_soft_warn,
            paywall_should_show=paywall_should_show,
        )

        # --- User prompt (clean params + blocks) ---
        user_prompt = f"""
MESSAGE UTILISATEUR:
{user_message}

PARAMÈTRES (pour répondre):
- language: {language}
- tone: {tone}
- tutoiement: {use_tu_form}
- tutoiement_known: {use_tu_known}
- user_name: {_safe_str(user_name) if user_name else "null"}

QUOTA (si présent):
- is_pro: {is_pro}
- state: {_safe_str(quota_state)}
- used: {_safe_str(quota_used)}
- limit: {_safe_str(quota_limit)}
- paywall_should_show: {paywall_should_show}

DOCS_CHUNKS (si présent):
- ok: {dc_ok}
- scopes: {", ".join([_safe_str(s) for s in dc_scopes[:3]]) if dc_scopes else "[]"}
- chunks (extraits):
{docs_block}

WEB_SEARCH (si présent):
- ok: {ws_ok}
- answer: {_safe_str(ws_answer)[:1800]}
- sources (titles + domains only):
{sources_digest}

CONTEXTE (JSON compact, référence):
{ctx_text}

INSTRUCTIONS DE RÉPONSE:
- Réponds dans la langue "{language}".
- Si tutoiement=true, tutoie. Sinon vouvoie.
- Respecte strictement les CONVENTIONS UI.
- Si web_search ok=true, utilise ses faits en priorité.
- Si tu ajoutes des sources, utilise seulement le bloc "{SOURCES_BLOCK_HEADER}" et 1 à 3 puces sans URL.
- Si DOCS_CHUNKS ok=true et chunks non vides, utilise ces extraits comme source prioritaire (avant le contexte compact).

{paywall_block}

{intent_block}
""".strip()

        try:
            # --- Compose system prompt (versionné) ---
            p = load_lisa_system_prompts()  # version via env LISA_SIGNATURE_VERSION
            system_prompt = (
                SYSTEM_RESPONSE_WRITER_PROMPT.strip()
                + "\n\n"
                + f"{p['signature']}\n\n"
                + f"{p['format']}\n\n"
                + f"(Prompts version: {p['version']})"
            )

            # --- Pro mode playbook injection (system prompt) ---
            ob = _pick(ctx, "onboarding", {}) or {}
            ob_status = _safe_str(ob.get("status") or "").strip().lower()  # started|complete|""
            ob_pro = bool(ob.get("pro_mode"))
            ob_agent_key = _safe_str(ob.get("primary_agent_key") or "").strip()
            ob_playbook = _safe_str(ob.get("playbook_full") or "").strip()

            if ob_pro and ob_playbook:
                # phrase contextuelle + règles strictes (pas de doc brut balancé)
                header = (
                    "\n\n"
                    "CONTEXTE PRODUIT (MODE PAYANT)\n"
                    f"- mode_actif: {ob_agent_key or 'unknown'}\n"
                    f"- onboarding_status: {ob_status or 'null'}\n\n"
                    "INSTRUCTIONS STRICTES\n"
                    "- Tu es en mode payant : tu DOIS appliquer le playbook ci-dessous comme source de vérité métier.\n"
                    "- Tu n'inventes pas de procédures hors playbook si une section pertinente existe.\n"
                    "- Tu restes conversationnelle, mais tu exécutes le rôle du mode activé (pas 'assistant générique').\n"
                )

                if ob_status == "started":
                    header += (
                        "- L'onboarding est EN COURS : ta priorité est de guider le setup, vérifier les prérequis, "
                        "poser les questions manquantes, et proposer une checklist courte.\n"
                        "- Tant que l'utilisateur n'a pas terminé le setup ou n'a pas lancé une première action utile, "
                        "tu restes dans la logique onboarding.\n"
                    )
                else:
                    header += (
                        "- L'onboarding n'est pas en cours : tu utilises le playbook comme manuel d'exécution du mode, "
                        "sans lancer une séquence onboarding lourde si ce n'est pas demandé.\n"
                    )

                system_prompt = system_prompt + "\n\n" + header + "\n\nPLAYBOOK (FULL) — MODE ACTIF\n" + ob_playbook

            text, meta = await self.llm.chat_text(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=900,
                trace={"agent": "response_writer", "intent": intent, "mode": mode},
            )
        except Exception as e:
            return {
                "ok": False,
                "error": "RESPONSE_WRITER_LLM_ERROR",
                "answer": "",
                "debug": {
                    "exception": _safe_str(e),
                    "duration_ms": int((time.time() - start_ts) * 1000),
                },
            }

        answer = (text or "").strip()

        # hard cleanup: refuse code fences + markdown headings
        answer = answer.replace("```", "").replace("###", "").replace("##", "").replace("#", "")

        if intent == "amabilities" and len(answer) > 260:
            answer = answer[:257] + "..."

         # --- Force soft warning (do NOT rely on LLM obedience) ---
        def _pick_soft_warn(language: str, use_tu: bool) -> str:
            lang = (language or "fr").lower().strip()
            is_en = lang.startswith("en")

            if is_en:
                # EN
                return (
                    "By the way: to keep chatting without interruptions after this message, activate your free trial."
                    if use_tu
                    else "By the way: to keep chatting without interruptions after this message, activate your free trial."
                )

            # FR (default)
            return (
                "Au fait juste pour te prévenir : pour qu’on puisse continuer la discussion sans coupure, il faudra activer l’essai gratuit."
                if use_tu
                else "Au fait : pour continuer la discussion sans coupure après ce message, pensez à activer votre essai gratuit."
            )

        def _already_has_soft_warn(text: str) -> bool:
            low = (text or "").lower()
            # heuristiques simples (anti-doublon)
            if "free trial" in low or "trial" in low:
                return True
            if "essai gratuit" in low or ("essai" in low and "activer" in low):
                return True
            return False

        if should_soft_warn and not _already_has_soft_warn(answer):
            soft = _pick_soft_warn(language=language, use_tu=use_tu_form)

            answer = (answer or "").rstrip()

            # séparation clean
            if answer and answer[-1] not in ".!?":
                answer += "."

            answer += " " + soft

            chat_logger.info(
                "chat.paywall.soft_warn.appended",
                language=language,
                use_tu_form=use_tu_form,
                should_soft_warn=should_soft_warn,
            )

        return {
            "ok": True,
            "answer": answer,
            "debug": {
                "provider": meta.get("provider"),
                "model": meta.get("model"),
                "duration_ms": int((time.time() - start_ts) * 1000),
                "intent": intent,
                "need_web": need_web,
                "web_search_used": ws_ok,
            },
        }