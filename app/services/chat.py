# app/services/chat.py

import json
from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.agents.orchestrator import OrchestratorAgent
from app.services.plan_executor import PlanExecutor
from app.services.context_loader import load_context_light

from app.core.chat_logger import chat_logger
from app.integrations.n8n_userfacts import fire_userfact_webhook
from app.services.message_flags import extract_and_clean_message_flags
from app.services.intent_routing.state_resolver import resolve_state
from app.services.intent_routing.gates import apply_gates
from app.services.onboarding_state import apply_onboarding_state
from app.llm.runtime import LLMCallError

SAFE_FALLBACK_ANSWER = "Désolé — je n’ai pas réussi à générer une réponse. Réessaie."

class ChatError(Exception):
    pass


async def _get_public_user_id_from_auth(conn: Connection, auth_user_id: str) -> str | None:
    row = await conn.fetchrow(
        "select id from public.users where auth_user_id = $1",
        auth_user_id,
    )
    return row["id"] if row else None


async def _get_user_message(conn: Connection, conversation_id: str, user_message_id: str):
    return await conn.fetchrow(
        """
        select id, conversation_id, user_id, content, metadata
        from public.conversation_messages
        where id = $1 and conversation_id = $2
        """,
        user_message_id,
        conversation_id,
    )


async def _get_assistant_message(conn: Connection, assistant_message_id: str):
    return await conn.fetchrow(
        """
        select id, content, sent_at
        from public.conversation_messages
        where id = $1
        """,
        assistant_message_id,
    )

def _pick_discovery_doc_scopes(ctx: dict) -> list[str]:
    """
    Retourne exactement 2 scopes:
    1) discovery.value_proposition (toujours)
    2) discovery.<agent_key> si match ET unique agent actif, sinon discovery.default_all_profiles
    """
    base = "discovery.value_proposition"
    fallback = "discovery.default_all_profiles"

    scopes_all = []
    try:
        scopes_all = ((ctx or {}).get("docs") or {}).get("scopes_all") or []
    except Exception:
        scopes_all = []
    scopes_all = [str(s) for s in scopes_all if isinstance(s, str) and s.strip()]

    # active agent keys
    active_keys = []
    try:
        active_keys = ((ctx or {}).get("action_state") or {}).get("active_agent_keys") or []
    except Exception:
        active_keys = []
    active_keys = [str(k) for k in active_keys if isinstance(k, str) and k.strip()]

    # règle : si plusieurs agents actifs => fallback
    second = fallback
    if len(active_keys) == 1:
        candidate = f"discovery.{active_keys[0]}"
        if candidate in scopes_all:
            second = candidate
        else:
            second = fallback

    # base doit exister, sinon on ne bloque pas : on envoie quand même base+fallback
    return [base, second]


def _build_failsafe_light_plan(*, ctx: dict, state_decision, soft_paywall_warning: bool) -> dict:
    """
    Plan minimal: charge contexte light puis ResponseWriter.
    Aucun playbook/docs chunks => prompt ultra light.
    """
    language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"
    forced_state = str(getattr(state_decision, "state", "") or "normal")

    nodes = [
        {
            "id": "A",
            "type": "tool.db_load_context",
            "parallel_group": "P1",
            "inputs": {"level": "light"},
        },
        {
            "id": "D",
            "type": "agent.response_writer",
            "depends_on": ["A"],
            "inputs": {
                "intent": "",                     # pas d'overlay intent
                "mode": forced_state,             # state = mode
                "route_source": "failsafe",       # traçable
                "runtime_state": forced_state,    # source de vérité RW
                "state": forced_state,            # idem
                "language": language,
                "tone": "warm",
                "need_web": False,
                "soft_paywall_warning": bool(soft_paywall_warning),
                "transition_window": bool(getattr(state_decision, "transition_window", False)),
                "transition_reason": getattr(state_decision, "transition_reason", None),
                "smalltalk_target_key": ((ctx or {}).get("gates") or {}).get("smalltalk_target_key"),
            },
        },
    ]
    return {"nodes": nodes}



async def handle_chat_message(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    auth_user_id: str | None,
) -> dict:
    # 1) Load user message
    msg = await _get_user_message(conn, conversation_id, user_message_id)
    if not msg:
        raise ChatError("User message not found for this conversation")

    chat_logger.info(
        "chat.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        auth_user_id=str(auth_user_id) if auth_user_id else None,
        public_user_id=str(msg["user_id"]) if msg.get("user_id") else None,
        user_content=(msg["content"] or "")[:200],
    )

    public_user_id = msg["user_id"]

    # 2) Ownership check (best effort)
    # If auth_user_id exists => ensure msg.user_id belongs to auth_user_id
    if auth_user_id:
        expected_public_user_id = await _get_public_user_id_from_auth(conn, auth_user_id)
        if not expected_public_user_id:
            raise ChatError("No public user linked to this auth user")
        if str(expected_public_user_id) != str(public_user_id):
            raise ChatError("Message does not belong to authenticated user")

    # 3) Idempotence: if already processed, return existing assistant msg
    meta = msg["metadata"] or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}

    existing_assistant_id = meta.get("assistant_message_id")
    if existing_assistant_id:
        existing = await _get_assistant_message(conn, existing_assistant_id)
        if existing:
            chat_logger.info(
                "chat.cache_hit",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                assistant_message_id=str(existing_assistant_id),
            )
            return {
                "ok": True,
                "assistant_message": {
                    "id": str(existing["id"]),
                    "sent_at": existing["sent_at"].isoformat(),
                    "content": existing["content"],
                },
                "provider": {"primary": "cache", "fallback_used": False},
            }

    # 4) Routing start
    llm = LLMRuntime()

    chat_logger.info(
        "chat.routing.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )

    # 4bis) Load context (light) for routing (state_resolver + orchestrator)
    ctx = await load_context_light(
        conn,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
    )

    # -------------------------------------------------
    # 🧭 APPLY ONBOARDING STATE (Approche A)
    # -------------------------------------------------

    onboarding_result = await apply_onboarding_state(
        conn=conn,
        ctx=ctx,
        public_user_id=str(public_user_id),
        is_user_message=True,
    )

    # injecte le résultat dans ctx pour le resolver
    ctx["onboarding_runtime"] = onboarding_result

    chat_logger.info(
        "chat.ctx.loaded",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        has_user=bool((ctx or {}).get("user")),
        locale=((ctx or {}).get("settings") or {}).get("locale_main"),
        timezone=((ctx or {}).get("settings") or {}).get("timezone"),
        free_quota_used=((ctx or {}).get("user_status") or {}).get("free_quota_used"),
        free_quota_limit=((ctx or {}).get("user_status") or {}).get("free_quota_limit"),
        intro_smalltalk_turns=((ctx or {}).get("gates") or {}).get("user_messages_count"),
        intro_smalltalk_done=((ctx or {}).get("gates") or {}).get("smalltalk_done_derived"),
        last_messages_count=len((ctx or {}).get("messages") or []),
    )

    state_decision = resolve_state(ctx=ctx or {})

    gates_decision = apply_gates(ctx=ctx or {})
    soft_paywall_warning = bool(gates_decision.get("soft_paywall_warning"))

    # -------------------------------------------------
    # 🧪 STATE DEBUG SNAPSHOT (source of truth inputs)
    # -------------------------------------------------
    try:
        user_status_ctx = (ctx or {}).get("user_status") or {}
        settings_ctx = (ctx or {}).get("settings") or {}
        gates_ctx = (ctx or {}).get("gates") or {}
        action_ctx = (ctx or {}).get("action_state") or {}
        onboarding_runtime = (ctx or {}).get("onboarding_runtime") or {}

        chat_logger.info(
            "chat.state.inputs_snapshot",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),

            # ABONNEMENT (DB truth)
            db_is_pro=bool(user_status_ctx.get("is_pro")),

            # QUOTA
            quota_state=str(user_status_ctx.get("state")),
            quota_used=int(user_status_ctx.get("free_quota_used") or 0),
            quota_limit=int(user_status_ctx.get("free_quota_limit") or 0),

            # DISCOVERY
            discovery_status=str(settings_ctx.get("discovery_status")),

            # SMALLTALK
            smalltalk_done=bool(gates_ctx.get("smalltalk_done_derived")),
            user_messages_count=int(gates_ctx.get("user_messages_count") or 0),

            # AGENTS
            active_agent_keys=action_ctx.get("active_agent_keys"),

            # ONBOARDING
            onboarding_active=bool(onboarding_runtime.get("active")),
            onboarding_target=str(onboarding_runtime.get("target")),

            # FINAL STATE DECISION
            resolved_state=str(getattr(state_decision, "state", "")),
        )
    except Exception:
        pass

    chat_logger.info(
        "chat.fastpath.decision",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        state=str(getattr(state_decision, "state", "")),
        fastpath_allowed=bool(getattr(state_decision, "fastpath_allowed", False)),
        soft_paywall_warning=soft_paywall_warning,
    )

    chat_logger.info(
        "chat.state_decision",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        state=str(getattr(state_decision, "state", "")),
        fastpath_allowed=bool(getattr(state_decision, "fastpath_allowed", False)),
        soft_paywall_warning=soft_paywall_warning,
        transition_window=bool(getattr(state_decision, "transition_window", False)),
        transition_reason=str(getattr(state_decision, "transition_reason", "") or "")[:80],
    )

    # --- FASTPATH (v0) : smalltalk_intro / quota_blocked ---
    if bool(getattr(state_decision, "fastpath_allowed", False)) is True:
        language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"

        # FASTPATH = STATE ONLY (no intent overlay)
        intent = ""  # important: RW ignorera l'intent en fastpath (et même sans ça on n'en veut pas)
        mode = str(getattr(state_decision, "state", "normal") or "normal")


        chat_logger.info(
            "chat.fastpath.enter",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            state=str(state_decision.state),
            intent=str(intent),
            mode=str(mode),
        )

        nodes = [
            {
                "id": "A",
                "type": "tool.db_load_context",
                "parallel_group": "P1",
                "inputs": {"level": "light"},
            },
        ]

        # ✅ discovery_pending => docs_chunks obligatoire (AHA message)
        if state_decision.state == "discovery_pending":
            scopes = _pick_discovery_doc_scopes(ctx or {})
            chat_logger.info(
                "chat.discovery.docs_selected",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                scopes=scopes,
            )
            nodes.append(
                {
                    "id": "S",
                    "type": "tool.docs_chunks",
                    "depends_on": ["A"],
                    "inputs": {"scopes": scopes},
                }
            )

        # response writer
        deps = ["A"] + (["S"] if state_decision.state == "discovery_pending" else [])

        nodes.append(
            {
                "id": "D",
                "type": "agent.response_writer",
                "depends_on": deps,
                "inputs": {
                    "intent": intent,
                    "mode": mode,
                    "route_source": "fastpath",
                    "runtime_state": str(state_decision.state),
                    "language": language,
                    "tone": "warm",
                    "need_web": False,
                    "soft_paywall_warning": soft_paywall_warning,
                    "transition_window": bool(getattr(state_decision, "transition_window", False)),
                    "transition_reason": getattr(state_decision, "transition_reason", None),
                    "smalltalk_target_key": ((ctx or {}).get("gates") or {}).get("smalltalk_target_key"),
                },
            }
        )

        plan = {"nodes": nodes}

        orch = type("OrchStub", (), {})()
        orch.ok = True
        orch.intent = intent
        orch.language = language
        orch.need_web = False
        orch.confidence = 1.0
        orch.plan = plan
        orch.debug = {
            "intent_final": intent,
            "mode": mode,
            "meta": {"provider": "fastpath"},
            "state_decision": {
                "state": state_decision.state,
                "fastpath_allowed": state_decision.fastpath_allowed,
                "quota_blocked": getattr(state_decision, "quota_blocked", False),
                "soft_paywall_warning": getattr(state_decision, "soft_paywall_warning", False),
                "transition_window": getattr(state_decision, "transition_window", False),
            },
        }

    else:
        chat_logger.info(
            "chat.orchestrator.start",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
        )

        orchestrator = OrchestratorAgent(llm)

        try:
            orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)

        except Exception as e:
            # ✅ FAIL-SAFE : on ne laisse jamais le chat crasher si l'orchestrator tombe
            chat_logger.error(
                "chat.orchestrator.failsafe_triggered",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                error_type=type(e).__name__,
                error=str(e)[:240],
                exc_info=True,
            )

            # Plan minimal RW (light)
            plan = _build_failsafe_light_plan(
                ctx=ctx or {},
                state_decision=state_decision,
                soft_paywall_warning=soft_paywall_warning,
            )

            # Stub orch compatible avec le reste du pipeline
            orch = type("OrchStub", (), {})()
            orch.ok = False
            orch.intent = ""
            orch.language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"
            orch.need_web = False
            orch.confidence = 0.0
            orch.plan = plan
            orch.debug = {
                "intent_final": "",
                "mode": str(getattr(state_decision, "state", "") or "normal"),
                "meta": {"provider": "failsafe"},
                "error_type": type(e).__name__,
            }

        # Ensure route_source + FORCE runtime_state/state for ResponseWriter
        try:
            forced_state = str(getattr(state_decision, "state", "") or "")
            if isinstance(getattr(orch, "plan", None), dict):
                for n in orch.plan.get("nodes", []):
                    if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                        inputs = n.get("inputs") or {}
                        if isinstance(inputs, dict):
                            inputs["route_source"] = "orchestrator"
                            inputs["runtime_state"] = forced_state
                            inputs["state"] = forced_state
                            inputs["soft_paywall_warning"] = soft_paywall_warning
                            inputs["transition_window"] = bool(getattr(state_decision, "transition_window", False))
                            inputs["transition_reason"] = getattr(state_decision, "transition_reason", None)
                            n["inputs"] = inputs
        except Exception:
            pass

        try:
            rw_inputs = None
            if isinstance(getattr(orch, "plan", None), dict):
                for n in orch.plan.get("nodes", []):
                    if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                        rw_inputs = n.get("inputs") or {}
                        break

            chat_logger.info(
                "chat.orchestrator.rw_inputs_after_patch",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                forced_state=str(getattr(state_decision, "state", "") or ""),
                rw_runtime_state=str((rw_inputs or {}).get("runtime_state") or ""),
                rw_state=str((rw_inputs or {}).get("state") or ""),
                rw_route_source=str((rw_inputs or {}).get("route_source") or ""),
                rw_intent=str((rw_inputs or {}).get("intent") or ""),
                rw_mode=str((rw_inputs or {}).get("mode") or ""),
            )
        except Exception:
            pass

        # --- Force intent discovery_pending si status=pending (non-fastpath) ---
        try:
            settings = (ctx or {}).get("settings") or {}
            discovery_status = str(settings.get("discovery_status") or "").strip().lower()

            if getattr(state_decision, "state", None) == "discovery" and discovery_status == "pending":
                # 1) force orch.intent
                try:
                    orch.intent = "discovery_pending"
                except Exception:
                    pass

                # 2) patch plan: docs_chunks + deps + intent input
                if isinstance(getattr(orch, "plan", None), dict):
                    plan = orch.plan
                    nodes = plan.get("nodes") or []
                    if isinstance(nodes, list):
                        has_docs_node = any(
                            isinstance(n, dict) and n.get("type") == "tool.docs_chunks"
                            for n in nodes
                        )

                        if not has_docs_node:
                            scopes = _pick_discovery_doc_scopes(ctx or {})
                            docs_node = {
                                "id": "S",
                                "type": "tool.docs_chunks",
                                "depends_on": ["A"],
                                "inputs": {"scopes": scopes},
                            }

                            # insert docs node before response_writer if possible
                            inserted = False
                            for i, n in enumerate(nodes):
                                if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                                    nodes.insert(i, docs_node)
                                    inserted = True
                                    break
                            if not inserted:
                                nodes.append(docs_node)

                        # ensure response_writer depends on S and intent is discovery_pending
                        for n in nodes:
                            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                                deps = n.get("depends_on") or []
                                if not isinstance(deps, list):
                                    deps = []
                                if "S" not in deps:
                                    deps.append("S")
                                n["depends_on"] = deps

                                inputs = n.get("inputs") or {}
                                if isinstance(inputs, dict):
                                    inputs["intent"] = "discovery_pending"
                                    n["inputs"] = inputs

                        plan["nodes"] = nodes
                        orch.plan = plan

                        chat_logger.info(
                            "chat.discovery.pending_forced",
                            conversation_id=str(conversation_id),
                            user_message_id=str(user_message_id),
                        )
        except Exception as _e:
            chat_logger.info("chat.discovery.pending_force_error", error=str(_e)[:180])

    # 5) Execute plan (tools + response_writer)
    executor = PlanExecutor(
        conn=conn,
        llm=llm,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
        user_message=str(msg["content"]),
    )

    # --- Inject docs scopes for discovery_pending (state-based, clean) ---
    try:
        needs_docs = (getattr(state_decision, "state", None) == "discovery_pending")

        # si fastpath, ton plan ajoute déjà S => rien à faire
        if bool(getattr(state_decision, "fastpath_allowed", False)):
            needs_docs = False

        if needs_docs and isinstance(getattr(orch, "plan", None), dict):
            plan = orch.plan
            nodes = plan.get("nodes") or []
            if isinstance(nodes, list):

                has_docs_node = any(
                    isinstance(n, dict) and n.get("type") == "tool.docs_chunks"
                    for n in nodes
                )

                if not has_docs_node:
                    scopes = _pick_discovery_doc_scopes(ctx or {})

                    chat_logger.info(
                        "chat.discovery.docs_injected",
                        conversation_id=str(conversation_id),
                        user_message_id=str(user_message_id),
                        scopes=scopes,
                    )

                    docs_node = {
                        "id": "S",
                        "type": "tool.docs_chunks",
                        "depends_on": ["A"],
                        "inputs": {"scopes": scopes},
                    }

                    inserted = False
                    for i, n in enumerate(nodes):
                        if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                            nodes.insert(i, docs_node)
                            inserted = True
                            break
                    if not inserted:
                        nodes.append(docs_node)

                    for n in nodes:
                        if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                            deps = n.get("depends_on") or []
                            if not isinstance(deps, list):
                                deps = []
                            if "S" not in deps:
                                deps.append("S")
                            n["depends_on"] = deps

                    plan["nodes"] = nodes
                    orch.plan = plan
    except Exception as _e:
        chat_logger.info("chat.discovery.docs_inject_error", error=str(_e)[:180])

    chat_logger.info(
        "chat.executor.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )
    try:
        exec_out = await executor.run(plan=orch.plan)

        # --- Escalation handling ---
        orch_provider = (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider")
        provider_primary = orch_provider or "orchestrated"

        if exec_out.get("escalate") is True:
            # ✅ On ne relance l’orchestrator QUE si on vient du fastpath
            if provider_primary == "fastpath":
                chat_logger.info(
                    "chat.fastpath.escalate_to_orchestrator",
                    conversation_id=str(conversation_id),
                    user_message_id=str(user_message_id),
                    reason=str(exec_out.get("escalate_reason") or "")[:120],
                )

                # --- Escalation hinting: force web/docs on orchestrator rerun (deterministic) ---
                try:
                    esc_reason = str(exec_out.get("escalate_reason") or "").strip().lower()

                    if not isinstance(ctx, dict):
                        ctx = {}

                    if not isinstance(ctx.get("gates"), dict):
                        ctx["gates"] = {}

                    if esc_reason == "need_web":
                        ctx["gates"]["force_need_web"] = True

                    if esc_reason == "need_docs":
                        ctx["gates"]["force_need_docs"] = True

                    chat_logger.info(
                        "chat.escalate.hint_applied",
                        conversation_id=str(conversation_id),
                        user_message_id=str(user_message_id),
                        esc_reason=esc_reason,
                        force_need_web=bool(ctx["gates"].get("force_need_web")),
                        force_need_docs=bool(ctx["gates"].get("force_need_docs")),
                    )
                except Exception:
                    pass

                orchestrator = OrchestratorAgent(llm)
                ctx = ctx or {}
                ctx["runtime_state"] = {"state": str(getattr(state_decision, "state", "") or "")}
                orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)

                # patch plan: enforce route_source orchestrator
                try:
                    if isinstance(getattr(orch, "plan", None), dict):
                        for n in orch.plan.get("nodes", []):
                            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                                inputs = n.get("inputs") or {}
                                if isinstance(inputs, dict):
                                    inputs["route_source"] = "orchestrator"
                                    inputs["runtime_state"] = str(getattr(state_decision, "state", "") or "")
                                    inputs["soft_paywall_warning"] = soft_paywall_warning
                                    inputs["transition_window"] = bool(getattr(state_decision, "transition_window", False))
                                    inputs["transition_reason"] = getattr(state_decision, "transition_reason", None)
                                    n["inputs"] = inputs
                except Exception:
                    pass

                exec_out = await executor.run(plan=orch.plan)

            else:
                # ✅ sinon on ignore : un plan orchestré ne doit pas ré-escalader ici
                chat_logger.info(
                    "chat.escalate.ignored_non_fastpath",
                    conversation_id=str(conversation_id),
                    user_message_id=str(user_message_id),
                    provider_primary=str(provider_primary),
                    reason=str(exec_out.get("escalate_reason") or "")[:120],
                )

        reply_text_raw = exec_out.get("answer") or SAFE_FALLBACK_ANSWER

        # ✅ Nettoyage des flags de fin de message (aha_moment / onboarding_abort)
        reply_text, flags = extract_and_clean_message_flags(reply_text_raw)

        orch_provider = (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider")
        provider_primary = orch_provider or "orchestrated"

        provider = {
            "primary": provider_primary,
            "fallback_used": (orch.ok is False),
            "orchestrator": {"provider": orch_provider},
        }

        # ✅ Ajoute les flags au provider/meta (pour debug et analytics)
        provider["flags"] = flags.to_metadata()
        chat_logger.info(
            "chat.executor.done",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            answer_len=len(reply_text or ""),
            provider_primary=provider.get("primary"),
            fallback_used=bool(provider.get("fallback_used")),
        )
        # tu peux aussi stocker exec_out["debug"] en metadata si tu veux
    except Exception as e:
        # filet de sécurité ultime
        reply_text = "Désolé — j’ai eu un souci technique. Réessaie dans quelques secondes."
        provider = {"primary": "error_fallback", "fallback_used": True, "error": str(e)[:160], "flags": {"aha_moment": False, "onboarding_abort": False}}

        chat_logger.error(
            "chat.executor.error",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            error=str(e)[:300],
            exc_info=True,
        )


    # 6) Insert assistant message (idempotent via dedupe_key)
    dedupe_key = f"a:{conversation_id}:{user_message_id}"

    # --- Persist orchestration decision into assistant metadata (for continuity) ---
    mode = None
    try:
        for n in (orch.plan or {}).get("nodes", []):
            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                mode = ((n.get("inputs") or {}) if isinstance(n.get("inputs"), dict) else {}).get("mode")
                break
    except Exception:
        mode = None

    # --- intent_final robuste (source: orch.debug.intent_final si dispo) ---
    intent_final = None
    try:
        dbg = getattr(orch, "debug", None)
        if isinstance(dbg, dict):
            intent_final = dbg.get("intent_final") or dbg.get("intent")  # fallback
    except Exception:
        intent_final = None

    if not intent_final:
        intent_final = getattr(orch, "intent", None)

    assistant_meta = {
        "event_type": "backend_chat",
        "provider": provider,

        # continuity keys
        "orch": {
            "intent_final": str(intent_final or ""),
            "mode": str(mode or ""),
            "need_web": bool(getattr(orch, "need_web", False)),
            "confidence": float(getattr(orch, "confidence", 0.0) or 0.0),
        }
    }

    inserted = await conn.fetchrow(
        """
        insert into public.conversation_messages
        (conversation_id, user_id, sender_type, role, content, metadata, dedupe_key)
        values
        ($1, $2::uuid, 'lisa', 'assistant', $3, $4::jsonb, $5)
        on conflict (dedupe_key) do update
        set content = excluded.content,
            metadata = excluded.metadata
        returning id, sent_at
        """,
        conversation_id,
        public_user_id,
        reply_text,
        json.dumps(assistant_meta, default=str),
        dedupe_key,
    )

    assistant_message_id = str(inserted["id"])

    # ✅ Post-actions (AHA request / AHA moment / abort) — best effort, ne casse pas le chat
    try:
        flags_meta = provider.get("flags", {}) or {}

        # 1) Dès que Lisa POSE la question de démo => on passe pending
        if flags_meta.get("aha_request") is True:
            await conn.execute(
                """
                update public.user_settings
                set discovery_status = 'pending'
                where user_id = $1
                and coalesce(discovery_status, 'to_do') in ('to_do', '')
                """,
                public_user_id,
            )

        # 2) Si user dit OUI (aha_moment) => complete
        if flags_meta.get("aha_moment") is True:
            await conn.execute(
                """
                update public.user_settings
                set discovery_status = 'complete',
                    discovery_completed_at = now()
                where user_id = $1
                """,
                public_user_id,
            )

        # 3) Si user dit NON (abort) => aborted (sauf si déjà complete)
        elif flags_meta.get("onboarding_abort") is True:
            await conn.execute(
                """
                update public.user_settings
                set discovery_status = 'aborted'
                where user_id = $1
                and coalesce(discovery_status,'pending') <> 'complete'
                """,
                public_user_id,
            )

    except Exception as _e:
        chat_logger.info("chat.flags.persist_error", error=str(_e)[:180])

    chat_logger.info(
        "chat.persisted",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        assistant_message_id=str(assistant_message_id),
    )

    # ✅ Persist smalltalk state (business rule)
    smalltalk_done_derived = False
    user_messages_count = 0
    discovery_status_now = ""

    # ✅ Onboarding progression (DB-side deterministic)
    try:
        onboarding_ctx = (ctx or {}).get("onboarding") or {}
        action_ctx = (ctx or {}).get("action_state") or {}

        has_paid_active = bool(((ctx or {}).get("user_status") or {}).get("is_pro"))
        discovery_status_now = str(
            ((ctx or {}).get("settings") or {}).get("discovery_status") or ""
        ).strip().lower()

        await conn.execute(
            "select public.fn_update_onboarding_progress($1, $2, $3)",
            public_user_id,
            has_paid_active,
            discovery_status_now,
        )

    except Exception as _e:
        chat_logger.info("chat.onboarding.progress_error", error=str(_e)[:180])

    try:
        gates = (ctx or {}).get("gates") or {}
        smalltalk_done_derived = bool(gates.get("smalltalk_done_derived"))
        user_messages_count = int(gates.get("user_messages_count") or 0)
        discovery_status_now = str(gates.get("discovery_status") or "").strip().lower()

        await conn.execute(
            """
            update public.user_settings
            set intro_smalltalk_done = $2,
                intro_smalltalk_turns = greatest(coalesce(intro_smalltalk_turns, 0), $3)
            where user_id = $1
            """,
            public_user_id,
            smalltalk_done_derived,
            user_messages_count,
        )
    except Exception as _e:
        chat_logger.info("chat.smalltalk.persist_error", error=str(_e)[:180])

    # ✅ Safety net : au 15e message user, si discovery pas démarré => pending forcé
    try:
        if smalltalk_done_derived and user_messages_count >= 15 and discovery_status_now in ("to_do", "", "null", "none"):
            await conn.execute(
                """
                update public.user_settings
                set discovery_status = 'pending'
                where user_id = $1
                and coalesce(discovery_status, 'to_do') in ('to_do', '')
                """,
                public_user_id,
            )
    except Exception as _e:
        chat_logger.info("chat.discovery.force_pending_error", error=str(_e)[:180])


    # 6bis) Fire-and-forget user facts catcher (must not impact chat latency)
    chat_logger.info("userfacts.hook.before", conversation_id=str(conversation_id), user_message_id=str(user_message_id))

    try:
        payload = {
            "public_user_id": str(public_user_id),
            "conversation_id": str(conversation_id),
            "user_message_id": str(user_message_id),
            "assistant_message_id": str(assistant_message_id),
            "user_text": (msg["content"] or ""),
            "locale": ((ctx or {}).get("settings") or {}).get("locale_main"),
            "timezone": ((ctx or {}).get("settings") or {}).get("timezone"),
        }

        chat_logger.info("userfacts.hook.payload_ready", public_user_id=str(public_user_id))

        # ✅ IMPORTANT : si fire_userfact_webhook est async -> create_task
        import asyncio
        asyncio.create_task(fire_userfact_webhook(payload))

        chat_logger.info("userfacts.hook.task_scheduled")

    except Exception as e:
        chat_logger.info("userfacts.webhook.call_error", error=str(e)[:180])

    # 7) Update user msg metadata with assistant id (idempotence marker)
    # We merge existing metadata (best effort)
    await conn.execute(
        """
        update public.conversation_messages
        set metadata = coalesce(metadata, '{}'::jsonb) ||
        jsonb_build_object(
            'processed_by_backend', true,
            'assistant_message_id', $2::uuid
        )
        where id = $1::uuid
        """,
        user_message_id,
        assistant_message_id,
    )

    chat_logger.info(
        "chat.end",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        assistant_message_id=str(assistant_message_id),
    )

    return {
        "ok": True,
        "assistant_message": {
            "id": assistant_message_id,
            "sent_at": inserted["sent_at"].isoformat(),
            "content": reply_text,
        },
        "provider": provider,
    }