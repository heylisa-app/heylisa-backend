# app/agents/response_writer.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.llm.runtime import LLMRuntime
from app.prompts.loader import load_lisa_system_prompts
from app.prompts.user.loader import load_user_prompt_block, get_user_prompt_keys
from app.core.chat_logger import chat_logger
from app.core.llm_prompt_logger import log_llm_messages

from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

import logging

logger = logging.getLogger(__name__)



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
        raw_user_message: Optional[str] = None, 
        intent: str,
        language: str = "fr",
        tone: str = "warm",
        need_web: bool = False,
        mode: str = "normal",
        smalltalk_target_key: Optional[str] = None,
        transition_window: bool = False,
        transition_reason: Optional[str] = None,
        soft_paywall_warning: bool = False,
        intent_eligible: bool = True,
        intent_block_reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        quota: Optional[Dict[str, Any]] = None,
        web: Optional[Dict[str, Any]] = None,
        # compat: si un autre appel utilise encore web_search=
        web_search: Optional[Dict[str, Any]] = None,
        route_source: str = "orchestrator",  # "fastpath" | "orchestrator"
        runtime_state: Optional[str] = None, # état runtime (smalltalk_intro, discovery, ...)
        docs_chunks: Optional[Dict[str, Any]] = None,
        playbook: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_ts = time.time()

        ctx = context or {}
        history_msgs = ((ctx.get("history") or {}).get("messages") or [])
        # fallback legacy
        if not isinstance(history_msgs, list) or not history_msgs:
            history_msgs = (ctx.get("messages") or [])
        q = quota or {}
        # priorité: web= (PlanExecutor), sinon web_search= (compat)
        ws = web if isinstance(web, dict) and web else (web_search or {})

        is_fastpath = (route_source or "").strip().lower() == "fastpath"

        # ✅ Source de vérité immuable : runtime_state ne doit JAMAIS être altéré
        runtime_state_in = (runtime_state or "").strip()

        # state_key = clé de prompt "state" (peut être nettoyée par guardrails)
        state_key = runtime_state_in

        # ✅ Fastpath = STATE ONLY : on ignore complètement l’intent overlay
        intent_key = "" if is_fastpath else (intent or "").strip()

        fastpath_directive_block = ""
        if is_fastpath:
            fastpath_directive_block = """
FASTPATH DIRECTIVE (TRÈS IMPORTANT)
Tu es appelée en FASTPATH (réponse rapide, sans orchestrator).

Tu as DEUX options seulement :

1) Répondre directement au user si tu es sûre que c’est :
   - small_talk
   - amabilities
   - general_question
   - state = discovery
   - state = discovery_pending
   ET que :
   - tu n’as PAS besoin d’une recherche web
   - tu n’as PAS besoin de docs supplémentaires
   - l'historique fourni (10 derniers messages) est suffisant

2) Sinon : tu NE RÉPONDS PAS.
   Tu écris EXACTEMENT UN des tokens suivants (et rien d’autre) :

   - [[ESCALATE:WEB]]  => si tu as besoin d’une recherche web
   - [[ESCALATE:DOCS]] => si tu as besoin de docs internes supplémentaires
   - [[ESCALATE]]      => si c’est hors cadre / besoin orchestrator sans précision

IMPORTANT (DOCS)
- Si DOCS_CHUNKS ok=true ET qu'il y a au moins 1 chunk, tu n'as PAS le droit d'écrire [[ESCALATE:DOCS]].
- Dans ce cas tu DOIS répondre en t'appuyant sur DOCS_CHUNKS.

RÈGLES:
- Aucun autre texte que le token.
- Aucun emoji, aucune ponctuation, aucune explication.
""".strip()

        # --- Extract minimal user prefs from context (optional) ---
        settings = _pick(ctx, "settings", {}) or {}
        use_tu_raw = _pick(settings, "use_tu_form", None)
        use_tu_form = True if use_tu_raw is True else False if use_tu_raw is False else False
        use_tu_known = (use_tu_raw is True) or (use_tu_raw is False)
        user_name = _pick(_pick(ctx, "user", {}), "first_name", None)
        intro_smalltalk_turns = int(_pick(settings, "intro_smalltalk_turns", 0) or 0)
        intro_smalltalk_done = bool(_pick(settings, "intro_smalltalk_done", False))

        # --- Soft warning (signal déterministe venant du router) ---
        should_soft_warn = bool(soft_paywall_warning)

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

        docs_present = bool(dc_ok and isinstance(dc_chunks, list) and len(dc_chunks) > 0)

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

        # --- State + Intent prompt blocks (SAFE) ---
        state_keys = get_user_prompt_keys("state")
        intent_keys = get_user_prompt_keys("intent")

        # Guardrail 1: prevent mixing (state mistakenly set to an intent)
        if state_key and state_key in intent_keys:
            chat_logger.info(
                "chat.response_writer.guardrail.state_is_intent",
                state_key=state_key,
                intent_key=intent_key,
            )
            state_key = ""

        # Guardrail 2: prevent mixing (intent mistakenly set to a state)
        if intent_key and intent_key in state_keys:
            chat_logger.info(
                "chat.response_writer.guardrail.intent_is_state",
                state_key=state_key,
                intent_key=intent_key,
            )
            intent_key = ""

        # Guardrail 3: drop unknown keys (typos / future keys)
        if state_key and state_key not in state_keys:
            chat_logger.info(
                "chat.response_writer.guardrail.unknown_state_key",
                state_key=state_key,
                intent_key=intent_key,
            )
            state_key = ""

        if intent_key and intent_key not in intent_keys:
            chat_logger.info(
                "chat.response_writer.guardrail.unknown_intent_key",
                state_key=state_key,
                intent_key=intent_key,
            )
            intent_key = ""

        state_vars: Dict[str, str] = {}
        intent_vars: Dict[str, str] = {}

        # Vars communes (si utile)
        common_vars = {
            "transition_window": ("true" if transition_window else "false"),
            "transition_reason": (_safe_str(transition_reason)[:80] if transition_reason else "null"),
        }

        # --------------------
        # STATE VARS (dominant)
        # --------------------
        # ⚠️ Ici, tu mets UNIQUEMENT des vars nécessaires aux prompts de STATE.

        # state: smalltalk_intro
        if state_key == "smalltalk_intro":
            state_vars.update({
                "smalltalk_target_key": (_safe_str(smalltalk_target_key) if smalltalk_target_key else "null"),
            })

        # state: discovery / discovery_pending
        if state_key in ("discovery", "discovery_pending"):
            gates = _pick(ctx, "gates", {}) or {}
            state_vars.update({
                "discovery_forced": ("true" if bool(gates.get("discovery_forced")) else "false"),
                "discovery_status": (_safe_str(gates.get("discovery_status") or "null")),
            })

        state_vars.update(common_vars)

        # --------------------
        # INTENT VARS (overlay)
        # --------------------
        # ⚠️ Ici on garde TES infos utiles (connected_integrations, mapping, etc.)
        # et on n'ajoute des vars que si l'intent overlay en a besoin.

        # (Option) intents qui ont besoin d'éligibilité
        if intent_key in ("action_request", "professional_request", "deep_work"):
            intent_vars.update({
                "intent_eligible": ("true" if intent_eligible else "false"),
                "intent_block_reason": (_safe_str(intent_block_reason)[:80] if intent_block_reason else "null"),
            })

        # intent: action_request (on garde ton code existant quasi intact)
        if intent_key == "action_request":
            action_state = _pick(ctx, "action_state", {}) or {}
            action_req = action_state.get("action_required_integrations") or {}

            # Connected integrations (set)
            connected = set()
            ci = action_state.get("connected_integrations") or []
            if isinstance(ci, list):
                connected = {_safe_str(x).strip() for x in ci if isinstance(x, str) and x.strip()}

            # Compact map "action:integ+integ | ..."
            pairs = []
            if isinstance(action_req, dict):
                for k, v in list(action_req.items())[:50]:
                    if isinstance(v, list) and v:
                        pairs.append(f"{_safe_str(k)}:{'+'.join([_safe_str(x) for x in v[:6]])}")
                    else:
                        pairs.append(f"{_safe_str(k)}:none")
            action_map_compact = " | ".join(pairs) if pairs else "none"

            # Missing integrations per action (req - connected)
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

            # Union
            missing_all = sorted({x for v in missing_by_action.values() for x in (v or []) if isinstance(x, str) and x.strip()})

            # "email_read:gmail(missing) | todoist_add:none"
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
                "missing_integrations_all": ", ".join(missing_all[:50]) or "none",
                "missing_integrations_map": missing_map_compact,
            })

        intent_vars.update(common_vars)

        # --------------------
        # LOAD BLOCKS
        # --------------------
        state_block = ""
        if state_key:
            state_block = load_user_prompt_block(kind="state", key=state_key, vars=state_vars).strip()

        logger.info(
            f"[RW_STATE_BLOCK] state_key={state_key} "
            f"loaded={bool(state_block)} "
            f"len={len(state_block or '')}"
        )

        intent_block = ""
        if intent_key:
            intent_block = load_user_prompt_block(kind="intent", key=intent_key, vars=intent_vars).strip()

        # --- Paywall block (optional) ---
        paywall_block = ""
        if should_soft_warn:
            paywall_block = load_user_prompt_block(kind="misc", key="paywall_soft_warning", vars={}).strip()


        # --- Thread alert: short user message guardrail ---
        raw_msg = (raw_user_message or user_message or "").strip()

        def _word_count(txt: str) -> int:
            try:
                return len([w for w in (txt or "").strip().split() if w])
            except Exception:
                return 0

        wc = _word_count(raw_msg)
        is_short_user_msg = wc > 0 and wc < 6

        thread_alert_block = ""
        if is_short_user_msg:
            thread_alert_block = f"""
🚨 THREAD ALERT (message très court détecté: {wc} mots)

RÈGLES STRICTES (non négociables) :
- Tu NE DOIS PAS interpréter ce message comme un nouveau sujet.
- Tu DOIS te baser sur le contexte + le dernier échange pour comprendre à quoi l'utilisateur répond.
- Tu DOIS retrouver dans l'historique ce que TU avais proposé / demandé juste avant (le fil) (Source historique: ctx.history.messages (10 derniers).)
- Si c’est ambigu, tu poses une seule question de clarification, pas d’invention (Tu DOIS poser UNE question fermée (A/B ou oui/non) pour confirmer la direction.).
- Interdit: partir sur une nouvelle hypothèse ("rythme", "pression", etc.) si ce n’est pas explicitement confirmé dans le fil immédiat.
""".strip()


        # --- User prompt (clean params + blocks) ---
        user_prompt = f"""
MESSAGE UTILISATEUR:
{raw_msg}

{thread_alert_block}

PARAMÈTRES (pour répondre):
- language: {language}
- tone: {tone}
- tutoiement: {use_tu_form}
- tutoiement_known: {use_tu_known}
- user_name: {_safe_str(user_name) if user_name else "null"}

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

{fastpath_directive_block}

{paywall_block}

{state_block}

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

            # --- Playbook injection (venant du node tool.playbook_load) ---
            pb = playbook or {}
            pb_ok = bool(_pick(pb, "ok", False))
            pb_level = _safe_str(_pick(pb, "level", "")).strip()
            pb_text = _safe_str(_pick(pb, "playbook_text", "")).strip()
            pb_agent_key = _safe_str(_pick(pb, "agent_key", "")).strip()

            if pb_ok and pb_text:
                header = (
                    "\n\n"
                    "CONTEXTE PRODUIT (MODE PAYANT)\n"
                    f"- mode_actif: {pb_agent_key or 'unknown'}\n"
                    f"- playbook_level: {pb_level or 'light'}\n\n"
                    "INSTRUCTIONS STRICTES\n"
                    "- Tu es en mode payant : tu DOIS appliquer le playbook ci-dessous comme source de vérité métier.\n"
                    "- Tu n'inventes pas de procédures hors playbook si une section pertinente existe.\n"
                    "- Tu restes conversationnelle, mais tu exécutes le rôle du mode activé (pas 'assistant générique').\n\n"
                    "PLAYBOOK (SOURCE DE VÉRITÉ)\n"
                    f"{pb_text}\n"
                )
                system_prompt = system_prompt + header

            llm_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            log_llm_messages(
                event="llm.prompt.response_writer",
                messages=llm_messages,
                trace={"agent": "response_writer", "intent": intent, "mode": mode},
                extra={
                    "language": language,
                    "need_web": need_web,
                    "ws_ok": ws_ok,
                    "dc_ok": dc_ok,
                    "should_soft_warn": should_soft_warn,
                    "intro_smalltalk_done": intro_smalltalk_done,
                    "intro_smalltalk_turns": intro_smalltalk_turns,
                },
            )

            chat_logger.info("chat.response_writer.raw_user_message", raw_len=len(raw_msg), raw_preview=raw_msg[:80])
            chat_logger.info(
                "chat.response_writer.thread_alert",
                word_count=wc,
                is_short=is_short_user_msg,
            )

            text, meta = await self.llm.chat_text(
                messages=llm_messages,
                temperature=0.4,
                max_tokens=900,
                trace={
                    "agent": "response_writer",
                    "intent": intent,
                    "mode": mode,
                    "raw_user_message": raw_msg,

                    # ✅ pour router DeepSeek quand smalltalk_intro + fastpath
                    "route_source": route_source,
                    "runtime_state": runtime_state_in or "null",
                },
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


        # --- Fastpath escalation token (LLM-decided, robust) ---
        # Si un token apparaît N'IMPORTE OÙ => escalation immédiate
        if is_fastpath:
            txt = (answer or "")

            esc_reason = None
            if "[[ESCALATE:WEB]]" in txt:
                esc_reason = "need_web"
            elif "[[ESCALATE:DOCS]]" in txt:
                # Si docs déjà présents, ce token est interdit => on retry 1 fois
                if docs_present:
                    chat_logger.info(
                        "chat.response_writer.escalate_blocked",
                        reason="need_docs",
                        blocked_because="docs_present",
                        intent=intent,
                        runtime_state=(runtime_state or "null"),
                    )

                    # Retry 1 fois avec contrainte explicite
                    retry_suffix = """
            🚫 CONTRAINTE ABSOLUE (FASTPATH)
            DOCS_CHUNKS est déjà présent (ok=true, chunks>=1).
            Il est INTERDIT de répondre [[ESCALATE:DOCS]].
            Tu DOIS répondre maintenant en t'appuyant sur DOCS_CHUNKS.
            Si tu ne peux pas, répond [[ESCALATE]] (pas DOCS).
            """.strip()

                    # 🔁 Retry LLM avec contrainte explicite (inline, sans helper externe)
                    llm_messages_retry = [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": user_prompt + "\n\n" + retry_suffix,
                        },
                    ]

                    log_llm_messages(
                        event="llm.prompt.response_writer.retry",
                        messages=llm_messages_retry,
                        trace={
                            "agent": "response_writer",
                            "intent": intent,
                            "mode": mode,
                            "route_source": route_source,
                            "runtime_state": runtime_state_in or "null",
                            "retry": "fastpath_docs_escalate_blocked",
                        },
                    )

                    text2, meta2 = await self.llm.chat_text(
                        messages=llm_messages_retry,
                        temperature=0.2,   # plus strict au retry
                        max_tokens=900,
                        trace={
                            "agent": "response_writer",
                            "intent": intent,
                            "mode": mode,
                            "route_source": route_source,
                            "runtime_state": runtime_state_in or "null",
                            "retry": "fastpath_docs_escalate_blocked",
                        },
                    )
                    answer2 = (text2 or "").strip()

                    # si au retry il renvoie encore ESCALATE:DOCS => on escalade quand même (dernière sécurité)
                    if "[[ESCALATE:DOCS]]" in answer2:
                        esc_reason = "need_docs"
                    elif "[[ESCALATE:WEB]]" in answer2:
                        esc_reason = "need_web"
                    elif "[[ESCALATE]]" in answer2:
                        esc_reason = "out_of_scope"
                    else:
                        # succès: on prend la réponse retry
                        answer = answer2
                        meta = meta2
                        esc_reason = None
                else:
                    esc_reason = "need_docs"
            elif "[[ESCALATE]]" in txt:
                esc_reason = "out_of_scope"

            if esc_reason:
                chat_logger.info(
                    "chat.response_writer.escalate",
                    reason=esc_reason,
                    intent=intent,
                    runtime_state=(runtime_state_in or "null"),
                )
                return {
                    "ok": False,
                    "error": "ESCALATE_TO_ORCHESTRATOR",
                    "answer": "",
                    "reason": esc_reason,  # ✅ IMPORTANT: top-level
                    "debug": {
                        "intent": intent,
                        "route_source": "fastpath",
                        "runtime_state": runtime_state_in,
                        "escalate_reason": esc_reason,
                        "duration_ms": int((time.time() - start_ts) * 1000),
                    },
                }

        # hard cleanup (SAFE):
        # - remove markdown code fences (``` and ```lang) without touching inline content
        # - remove markdown headings ONLY when they are headings (line-start), not every '#'
        import re

        # 1) remove code-fence lines entirely (``` or ```python etc.)
        answer = re.sub(r"(?m)^\s*```.*\n?", "", answer)

        # 2) remove heading markers at line start only (#, ##, ###, ...)
        answer = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", answer)

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