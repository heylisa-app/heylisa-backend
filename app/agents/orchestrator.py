# app/agents/orchestrator.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal
from difflib import SequenceMatcher

from app.llm.runtime import LLMRuntime
from app.core.llm_prompt_logger import log_llm_messages

from app.agents.node_registry import (
    NODE_TYPE_WHITELIST,
    render_nodes_whitelist_block,
    render_ids_rules_block,
)


IntentType = Literal[
    "amabilities",
    "medical_assistance",
    "patient_case_assistance",
    "cabinet_assistance",
    "product_support",
    "task_execution",
    "emotional_support",
    "out_of_scope",
]

StateType = Literal[
    "smalltalk_onboarding",
    "discovery_capabilities",
    "normal_run",
]

ContextLevel = Literal["light", "medium", "max", "billing"]
MANDATORY_DISCOVERY_SCOPE = "discovery.medical_assistant"
DOCS_SCOPES_MAX = 5



# NOTE: v1 — plan minimal : P1 parallel [context + quota] puis response_writer
@dataclass
class OrchestratorResult:
    ok: bool
    language: str
    state: StateType
    intent: IntentType
    primary_brain_key: Optional[str]
    secondary_brain_key: Optional[str]
    secondary_brain_reason: Optional[str]
    resume_loop_id: Optional[str]
    keep_warm_topic: bool
    context_level: ContextLevel
    task_execution_context: Optional[Dict[str, Any]]
    need_web: bool
    web_search_prompt: Optional[str]
    confidence: float
    plan: Dict[str, Any]
    debug: Dict[str, Any]
    



SYSTEM_PROMPT = f"""Tu es OrchestratorAgent de Lisa, assistante médicale d’un cabinet.

Ton rôle :
- analyser le message utilisateur
- choisir UN intent
- produire un JSON STRICT conforme au schéma attendu
- préparer les bons signaux pour le backend

Tu ne réponds jamais à l’utilisateur.
Tu ne fais QUE du routing + structuration.

═══════════════════════════════════════════════════════════════
SORTIE JSON — CONTRAT STRICT (PRIORITÉ ABSOLUE)

Tu dois produire un JSON VALIDE et respecter STRICTEMENT :

- intent = string parmi la liste autorisée
- context_level = light | medium | max | billing
- task_execution_context = objet SI intent = task_execution, sinon null
- task_detected = bool strict (true/false)
- task_key = string canonique OU null
- scopes_selected = liste de strings EXACTES depuis la liste fournie
- Tu n’inventes JAMAIS une clé
- Tu ne modifies JAMAIS un nom

INTERDIT :
- mettre une string dans task_detected
- reformuler un scope
- inventer une task_key

SI TU HÉSITES :
- task_key = null
- scopes_selected = []

EXEMPLE SÉLECTION TASK

❌ Mauvais :
"task_detected": "read_recent_emails"

✅ Bon :
"task_detected": true,
"task_key": "email_read"

EXEMPLE SÉLECTION DOCS

Si la liste des scopes disponibles est :

- capabilities.email.protocol
- capabilities.tasks.chat
- capabilities.appointments.overview

Et que la demande concerne les mails :

❌ Mauvais (scope inventé ou modifié) :
"scopes_selected": ["capabilities.emails.read_recent_emails"]

❌ Mauvais (mauvaise clé, même si proche) :
"scopes_selected": ["email.protocol"]

❌ Mauvais (approximation) :
"scopes_selected": ["capabilities.email"]

✅ Bon :
"scopes_selected": ["capabilities.email.protocol"]

RÈGLE :
Tu dois copier EXACTEMENT une valeur présente dans la liste.
Aucune transformation, aucune interprétation.

═══════════════════════════════════════════════════════════════
STATE (SOURCE DE VÉRITÉ BACKEND)

Le backend fournit :
ctx.runtime_state.state ∈
(smalltalk_onboarding, discovery_capabilities, normal_run)

RÈGLE :
- Tu ne choisis jamais le state
- Tu n’inventes jamais un état
- Tu adaptes uniquement intent + champs

═══════════════════════════════════════════════════════════════
INTENTS AUTORISÉS

- amabilities
- medical_assistance
- patient_case_assistance
- cabinet_assistance
- product_support
- task_execution
- emotional_support
- out_of_scope

═══════════════════════════════════════════════════════════════
PRIORITÉ DES INTENTS (STRICT)

1. product_support
2. task_execution
3. patient_case_assistance
4. medical_assistance
5. emotional_support
6. cabinet_assistance
7. out_of_scope
8. amabilities

RÈGLE CLÉ :
👉 Si une action concrète est demandée → task_execution

═══════════════════════════════════════════════════════════════
DÉFINITION DES INTENTS (VERSION COURTE)

amabilities  
→ politesse uniquement

out_of_scope  
→ aucun lien pro / cabinet / santé

medical_assistance  
→ question médicale générale (pas de patient précis)

patient_case_assistance  
→ cas patient concret

cabinet_assistance  
→ organisation / fonctionnement cabinet

product_support  
→ bug / setup / connecteurs

task_execution  
→ action concrète demandée  
(ex : lire mails, répondre, créer, vérifier)

emotional_support  
→ fatigue / surcharge

═══════════════════════════════════════════════════════════════
TASK EXECUTION — RÈGLES CRITIQUES

Si intent = task_execution :

- task_detected = true si une action plausible existe
- task_key = meilleure clé candidate (même approximative)
- sinon null

Tu DOIS remplir correctement :

- task_key
- task_status
- required_integrations
- missing_integrations
- can_execute_now

Tu ne mets JAMAIS la task dans task_detected.

═══════════════════════════════════════════════════════════════
DOCS SCOPES — RÈGLES STRICTES

Tu peux utiliser :
- scope_need = true/false
- scopes_selected = []

RÈGLES :
- Tu choisis UNIQUEMENT dans la liste fournie
- Tu copies EXACTEMENT les strings
- Tu n’inventes rien
- Tu ne simplifies rien

Si aucun scope ne matche :
→ scopes_selected = []

Cas :
- product_support → scopes obligatoires si dispo
- task_execution → scopes si lié produit
- discovery → toujours inclure discovery.medical_assistant

═══════════════════════════════════════════════════════════════
WEB SEARCH

need_web = true si :
- info médicale récente
- recommandations / guidelines
- besoin de sources fiables

Sinon false.

Si true :
→ web_search_prompt obligatoire, précis, orienté sources fiables

═══════════════════════════════════════════════════════════════
CONTINUITÉ CONVERSATIONNELLE

Tu dois tenir compte :
- ctx.history.messages
- CONVERSATION_LOOPS_ACTIVES

Si le message continue un sujet existant :
→ ne change pas d’intent inutilement

═══════════════════════════════════════════════════════════════
RÈGLES FINALES

- Un seul intent
- Pas d’invention
- Respect strict du JSON
- Priorité à l’action concrète
- Si doute → réponse conservative (null / [])

═══════════════════════════════════════════════════════════════
{render_nodes_whitelist_block()}
{render_ids_rules_block()}
"""


JSON_SCHEMA_HINT = {
    "ok": True,
    "language": "fr",
    "intent": "cabinet_assistance",
    "primary_brain_key": "cabinet_assistance",
    "secondary_brain_key": None,
    "secondary_brain_reason": None,
    "resume_loop_id": None,
    "keep_warm_topic": False,
    "context_level": "medium",
    "task_execution_context": {
        "task_detected": False,
        "task_key": None,
        "task_label": None,
        "task_status": "unknown",
        "task_category": None,
        "required_integrations": [],
        "connected_integrations": [],
        "missing_integrations": [],
        "can_execute_now": False
    },
    "need_web": False,
    "web_search_prompt": None,
    "confidence": 0.92,
    "scope_need": False,
    "scopes_selected": [],
    "debug": {
        "notes": "short",
        "signals": []
    }
}


def _safe_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None

def _language_from_ctx(ctx: Optional[Dict[str, Any]]) -> str:
    """
    Source of truth: ctx.settings.locale_main
    Retourne une langue courte (fr, en, it, es, de, pt)
    """
    try:
        locale = (ctx or {}).get("settings", {}).get("locale_main")
        if isinstance(locale, str) and locale:
            return locale.split("-")[0].lower()
    except Exception:
        pass
    return "fr"

def _state_from_ctx(ctx: Optional[Dict[str, Any]]) -> str:
    try:
        s = ((ctx or {}).get("runtime_state") or {}).get("state")
        s = str(s or "").strip()
        return s
    except Exception:
        return ""

def _compact_conversation_loops(ctx: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    loops = (((ctx or {}).get("loops") or {}).get("conversation_loops") or [])
    if not isinstance(loops, list):
        return []

    out: List[Dict[str, Any]] = []

    for loop in loops[:5]:
        if not isinstance(loop, dict):
            continue

        out.append(
            {
                "id": loop.get("id"),
                "loop_type": loop.get("loop_type"),
                "title": loop.get("title"),
                "summary": loop.get("summary"),
                "priority": loop.get("priority"),
                "score": loop.get("score"),
                "resume_brain_key": loop.get("resume_brain_key"),
                "origin_brain_key": loop.get("origin_brain_key"),
                "why_now": loop.get("why_now"),
                "updated_at": loop.get("updated_at"),
            }
        )

    return out

def _trial_feedback_active_from_ctx(ctx: Optional[Dict[str, Any]]) -> bool:
    try:
        flags = (ctx or {}).get("conversation_flags") or {}
        return bool(flags.get("trial_feedback_active") is True)
    except Exception:
        return False

def _normalize_state(s: str) -> StateType:
    s = (s or "").strip()
    if s in {"smalltalk_onboarding", "discovery_capabilities", "normal_run"}:
        return s  # type: ignore
    return "normal_run"

def _render_docs_scopes_block(ctx: Optional[Dict[str, Any]]) -> str:
    """
    Injecte la liste des docs scopes dans le SYSTEM PROMPT.
    Source de vérité: ctx.docs.scopes_all
    """
    scopes = []
    try:
        docs = (ctx or {}).get("docs") or {}
        scopes = docs.get("scopes_all") or []
    except Exception:
        scopes = []

    # nettoyage + limite soft
    clean: List[str] = []
    for s in (scopes or [])[:200]:
        if isinstance(s, str):
            ss = s.strip()
            if ss:
                clean.append(ss)

    if not clean:
        return (
            "\n═══════════════════════════════════════════════════════════════\n"
            "DOCUMENTATION DISPONIBLE (SCOPES)\n"
            "AUCUN SCOPE DISPONIBLE.\n"
            "Tu ne dois pas inventer de scopes.\n"
        )

    lines = "\n".join(f"- {s}" for s in clean)

    return (
        "\n═══════════════════════════════════════════════════════════════\n"
        "DOCUMENTATION DISPONIBLE (SCOPES EXACTS)\n"
        "Tu ne peux sélectionner QUE des scopes présents dans cette liste. Tu n'en inventes jamais.\n"
        "Liste:\n"
        f"{lines}\n"
    )


def _get_available_doc_scopes(ctx: Optional[Dict[str, Any]]) -> List[str]:
    scopes = []
    try:
        docs = (ctx or {}).get("docs") or {}
        scopes = docs.get("scopes_all") or []
    except Exception:
        scopes = []

    clean: List[str] = []
    for s in scopes[:500]:
        if isinstance(s, str):
            ss = s.strip()
            if ss:
                clean.append(ss)

    # dédoublonnage en gardant l’ordre
    seen = set()
    out: List[str] = []
    for s in clean:
        if s not in seen:
            out.append(s)
            seen.add(s)

    return out


def _filter_scopes_selected_exact(
    raw_scopes: Any,
    available_scopes: List[str],
    *,
    max_len: int = DOCS_SCOPES_MAX,
) -> Dict[str, Any]:
    """
    Garde UNIQUEMENT les scopes exacts présents dans available_scopes.
    Aucun renommage, aucune approximation, aucune invention.
    """
    valid_set = set(available_scopes)
    requested_raw: List[str] = []
    kept: List[str] = []
    rejected: List[str] = []

    if isinstance(raw_scopes, list):
        for s in raw_scopes[: max_len * 5]:
            if not isinstance(s, str):
                continue
            ss = s.strip()
            if not ss:
                continue

            requested_raw.append(ss)

            if ss in valid_set:
                if ss not in kept:
                    kept.append(ss)
            else:
                rejected.append(ss)

    return {
        "requested_raw": requested_raw,
        "kept": kept[:max_len],
        "rejected": rejected,
    }


def _normalize_catalog_key(s: Any) -> str:
    s = str(s or "").strip().lower()
    if not s:
        return ""
    # normalisation légère, purement structurelle
    s = s.replace("-", "_").replace(" ", "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("._")


def _tokenize_catalog_key(s: Any) -> List[str]:
    norm = _normalize_catalog_key(s)
    if not norm:
        return []
    parts: List[str] = []
    for chunk in norm.replace(".", "_").split("_"):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    return parts


def _score_catalog_key_match(candidate: str, target: str) -> float:
    """
    Score déterministe entre 0 et 1.
    On compare UNE clé candidate à UNE clé réelle du catalogue.
    Aucun raisonnement sur la langue utilisateur ici.
    """
    c = _normalize_catalog_key(candidate)
    t = _normalize_catalog_key(target)

    if not c or not t:
        return 0.0

    if c == t:
        return 1.0

    base_ratio = SequenceMatcher(None, c, t).ratio()

    c_tokens = set(_tokenize_catalog_key(c))
    t_tokens = set(_tokenize_catalog_key(t))

    token_overlap = 0.0
    if c_tokens and t_tokens:
        inter = len(c_tokens & t_tokens)
        union = len(c_tokens | t_tokens)
        if union > 0:
            token_overlap = inter / union

    prefix_bonus = 0.0
    if t.startswith(c) or c.startswith(t):
        prefix_bonus = 0.12

    contains_bonus = 0.0
    if c in t or t in c:
        contains_bonus = 0.08

    score = (base_ratio * 0.72) + (token_overlap * 0.20) + prefix_bonus + contains_bonus
    return min(score, 1.0)


def _resolve_best_catalog_key(
    *,
    candidate: Any,
    available_keys: List[str],
    min_score: float = 0.72,
) -> Dict[str, Any]:
    """
    Résout UNE clé candidate vers UNE clé canonique du catalogue.
    """
    candidate_norm = _normalize_catalog_key(candidate)

    if not candidate_norm:
        return {
            "requested_raw": str(candidate or ""),
            "requested_norm": "",
            "matched": None,
            "score": 0.0,
            "accepted": False,
        }

    clean_available = []
    for x in available_keys or []:
        if isinstance(x, str) and x.strip():
            clean_available.append(x.strip())

    if not clean_available:
        return {
            "requested_raw": str(candidate or ""),
            "requested_norm": candidate_norm,
            "matched": None,
            "score": 0.0,
            "accepted": False,
        }

    # exact match d'abord
    for key in clean_available:
        if _normalize_catalog_key(key) == candidate_norm:
            return {
                "requested_raw": str(candidate or ""),
                "requested_norm": candidate_norm,
                "matched": key,
                "score": 1.0,
                "accepted": True,
            }

    best_key = None
    best_score = 0.0

    for key in clean_available:
        score = _score_catalog_key_match(candidate_norm, key)
        if score > best_score:
            best_score = score
            best_key = key

    return {
        "requested_raw": str(candidate or ""),
        "requested_norm": candidate_norm,
        "matched": best_key if best_score >= min_score else None,
        "score": round(best_score, 4),
        "accepted": bool(best_score >= min_score and best_key),
    }


def _resolve_catalog_keys(
    *,
    candidates: List[str],
    available_keys: List[str],
    max_len: int,
    min_score: float = 0.72,
) -> Dict[str, Any]:
    """
    Résout une liste de clés candidates vers le catalogue réel.
    Retourne :
    - kept : clés canoniques retenues
    - rejected : candidates rejetées
    - details : debug fin
    """
    kept: List[str] = []
    rejected: List[str] = []
    details: List[Dict[str, Any]] = []

    seen = set()

    for candidate in candidates[:max_len]:
        res = _resolve_best_catalog_key(
            candidate=candidate,
            available_keys=available_keys,
            min_score=min_score,
        )
        details.append(res)

        matched = res.get("matched")
        accepted = bool(res.get("accepted") is True)

        if accepted and isinstance(matched, str) and matched not in seen:
            kept.append(matched)
            seen.add(matched)
        else:
            rejected.append(str(candidate))

    return {
        "requested_raw": [str(x) for x in candidates[:max_len]],
        "kept": kept[:max_len],
        "rejected": rejected,
        "details": details,
    }


def _fallback_plan_minimal(language: str = "fr") -> Dict[str, Any]:
    """
    Filet de sécurité uniquement.
    """
    return {
        "nodes": [
            {
                "id": "A",
                "type": "tool.db_load_context",
                "parallel_group": "P1",
                "inputs": {"level": "medium"},
            },
            {"id": "B", "type": "tool.quota_check", "parallel_group": "P1"},
            {
                "id": "D",
                "type": "agent.response_writer",
                "depends_on": ["A", "B"],
                "inputs": {
                    "intent": "cabinet_assistance",
                    "primary_brain_key": "cabinet_assistance",
                    "secondary_brain_key": None,
                    "secondary_brain_reason": None,
                    "resume_loop_id": None,
                    "keep_warm_topic": False,
                    "task_execution_context": None,
                    "language": language,
                    "tone": "warm",
                    "need_web": False,
                },
            },
        ]
    }

def _is_short_ack(text: str) -> bool:
    """
    Heuristique ultra simple pour identifier un "ack" (ok/merci/go...).
    Sert uniquement à éviter de sortir du smalltalk_intro sur un message vide/accusé.
    Ce n'est PAS un mécanisme de forçage d'intent.
    """
    t = (text or "").strip().lower()
    if not t:
        return True

    # réponses ultra courtes
    if len(t) <= 3:
        return True

    # petites confirmations fréquentes (FR/EN)
    return t in {
        "ok", "okay", "oui", "non", "d'accord", "dac", "ça marche", "c'est bon",
        "nickel", "parfait", "merci", "super", "top", "go", "vas-y", "yes", "no", "thanks",
    }

def _ensure_mandatory_scope(scopes: List[str], mandatory: str, max_len: int) -> List[str]:
    clean: List[str] = []
    for s in (scopes or []):
        if isinstance(s, str):
            ss = s.strip()
            if ss:
                clean.append(ss)

    # dédoublonnage en gardant l'ordre
    seen = set()
    dedup = []
    for s in clean:
        if s not in seen:
            dedup.append(s)
            seen.add(s)

    if mandatory not in seen:
        dedup = [mandatory] + dedup

    return dedup[:max_len]

def _compute_smalltalk_intro_gate(ctx: Dict[str, Any]) -> Dict[str, Any]:
    gates = (ctx or {}).get("gates") or {}
    eligible = bool(gates.get("smalltalk_intro_eligible"))
    target = gates.get("smalltalk_target_key")
    missing = gates.get("missing_required") or []
    return {
        "smalltalk_intro_eligible": eligible,
        "smalltalk_target_key": target,
        "missing_required": missing,
    }

def _compute_capabilities(ctx: Dict[str, Any]) -> Dict[str, Any]:
    caps = (ctx or {}).get("capabilities") or {}
    # fallback si pas présent
    return {
        "has_paid_agent": bool(caps.get("has_paid_agent", False)),
        "can_action_request": bool(caps.get("can_action_request", False)),
        "can_deep_work": bool(caps.get("can_deep_work", False)),
        "can_professional_request": bool(caps.get("can_professional_request", False)),
    }


def _apply_business_gates(
    *,
    llm_intent: str,
    user_message: str,
    ctx: Dict[str, Any],
    confidence: float,
) -> Dict[str, Any]:
    gate = _compute_smalltalk_intro_gate(ctx)
    caps = _compute_capabilities(ctx)

    eligible_intro = bool(gate["smalltalk_intro_eligible"])
    short_ack = _is_short_ack(user_message)

    intent = (llm_intent or "cabinet_assistance").strip()

    allowed = {
        "amabilities",
        "medical_assistance",
        "patient_case_assistance",
        "cabinet_assistance",
        "product_support",
        "task_execution",
        "emotional_support",
        "out_of_scope",
    }
    if intent not in allowed:
        intent = "cabinet_assistance"

    strong_intents = {
        "medical_assistance",
        "patient_case_assistance",
        "cabinet_assistance",
        "product_support",
        "task_execution",
        "emotional_support",
    }

    if eligible_intro:
        if intent in strong_intents and confidence >= 0.85 and not short_ack:
            intent_final = intent
        else:
            intent_final = "amabilities"
    else:
        intent_final = intent

    intent_eligible = True
    block_reason = None

    if intent_final == "task_execution":
        if not caps.get("has_paid_agent"):
            intent_eligible = False
            block_reason = "AGENT_NOT_ACTIVE"

    return {
        "intent_final": intent_final,
        "intent_eligible": intent_eligible,
        "intent_block_reason": block_reason,
        "gates": gate,
        "capabilities": caps,
        "signals": {"short_ack": short_ack},
    }


def _build_plan_minimal(
    *,
    language: str,
    state: StateType,
    intent: str,
    primary_brain_key: Optional[str],
    secondary_brain_key: Optional[str],
    secondary_brain_reason: Optional[str],
    resume_loop_id: Optional[str],
    keep_warm_topic: bool,
    mode: str,
    task_execution_context: Optional[Dict[str, Any]],
    need_web: bool,
    web_search_prompt: Optional[str],
    context_level: str,
    gates: Dict[str, Any],
    intent_eligible: bool,
    intent_block_reason: Optional[str],
    transition_window: bool,
    transition_reason: Optional[str],
    scope_need: bool,
    scopes_selected: List[str],
    trial_feedback_prompt_enabled: bool,
) -> Dict[str, Any]:
    """
    Plan stable, peu risqué.
    """
    context_loader_level = context_level or "medium"

    nodes = [
        {
            "id": "A",
            "type": "tool.db_load_context",
            "parallel_group": "P1",
            "inputs": {"level": context_loader_level},
        },
    ]

    # amabilities en mode normal => pas de quota_check
    if not (mode == "normal" and intent == "amabilities"):
        nodes.append(
            {
                "id": "B",
                "type": "tool.quota_check",
                "parallel_group": "P1",
            }
        )

    is_medical_intent = intent in {
        "medical_assistance",
        "patient_case_assistance",
    }

    if need_web:
        web_tool_type = (
            "tool.web_search_medical"
            if is_medical_intent
            else "tool.web_search"
        )

        nodes.append(
            {
                "id": "C",
                "type": web_tool_type,
                "depends_on": ["A", "B"] if any(n["id"] == "B" for n in nodes) else ["A"],
                "inputs": {
                    "prompt": web_search_prompt,
                    "language": language,
                },
            }
        )

    if scope_need:
        nodes.append(
            {
                "id": "S",
                "type": "tool.docs_chunks",
                "depends_on": ["A"],
                "inputs": {
                    "scopes": scopes_selected[:DOCS_SCOPES_MAX],
                },
            }
        )

    deps = ["A"]

    if any(n["id"] == "B" for n in nodes):
        deps.append("B")

    if need_web:
        deps.append("C")

    if scope_need:
        deps.append("S")

    nodes.append(
        {
            "id": "D",
            "type": "agent.response_writer",
            "depends_on": deps,
            "inputs": {
                "state": state,
                "intent": intent,
                "primary_brain_key": primary_brain_key,
                "secondary_brain_key": secondary_brain_key,
                "secondary_brain_reason": secondary_brain_reason,
                "resume_loop_id": resume_loop_id,
                "keep_warm_topic": bool(keep_warm_topic),
                "task_execution_context": task_execution_context,
                "language": language,
                "tone": "warm",
                "need_web": need_web,
                "smalltalk_target_key": (gates or {}).get("smalltalk_target_key"),
                "intent_eligible": intent_eligible,
                "intent_block_reason": intent_block_reason,
                "transition_window": bool(transition_window),
                "transition_reason": transition_reason,
                "trial_feedback_prompt_enabled": bool(trial_feedback_prompt_enabled),
            },
        }
    )

    return {"nodes": nodes}

def _sanitize_plan_or_fallback(
    *,
    plan: Any,
    language: str,
    intent: str,
    need_web: bool,
    web_search_prompt: Optional[str],
    scope_need: bool,
    scopes_selected: List[str],
    debug: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Ne reconstruit PAS un plan "intelligent".
    Vérifie juste des invariants + cohérence. Sinon fallback minimal.
    Met un flag debug["fallback_used"]=True quand on fallback.
    """

    def _fallback(reason_key: str) -> Dict[str, Any]:
        debug[reason_key] = True
        debug["fallback_used"] = True
        return _fallback_plan_minimal(language)

    if (
        not isinstance(plan, dict)
        or not isinstance(plan.get("nodes"), list)
        or not plan["nodes"]
    ):
        return _fallback("plan_invalid_structure")

    nodes = plan["nodes"]

    # 1) IDs uniques + types non vides
    ids: List[str] = []
    for n in nodes:
        if not isinstance(n, dict) or not n.get("id") or not n.get("type"):
            return _fallback("plan_invalid_node")
        ids.append(str(n["id"]))

    if len(set(ids)) != len(ids):
        return _fallback("plan_duplicate_ids")

    # 2) node types autorisés (whitelist)
    invalid_types = []
    for n in nodes:
        t = n.get("type")
        if t and t not in NODE_TYPE_WHITELIST:
            invalid_types.append(t)
    if invalid_types:
        debug["plan_invalid_node_types"] = list(sorted(set(invalid_types)))
        return _fallback("plan_has_disallowed_node_types")

    # 3) response_writer obligatoire
    if not any(n.get("type") == "agent.response_writer" for n in nodes):
        return _fallback("plan_missing_response_writer")

    # 4) need_web => node web search obligatoire + prompt non vide
    if need_web:
        if not isinstance(web_search_prompt, str) or not web_search_prompt.strip():
            return _fallback("need_web_but_prompt_missing")

        if not any(
            n.get("type") in {"tool.web_search", "tool.web_search_medical"}
            for n in nodes
        ):
            return _fallback("need_web_but_web_node_missing")

    # 4bis) scope_need => node tool.docs_chunks obligatoire + scopes_selected non vide
    if scope_need:
        if not isinstance(scopes_selected, list) or len(scopes_selected) == 0:
            return _fallback("scope_need_but_scopes_missing")

        if not any(n.get("type") == "tool.docs_chunks" for n in nodes):
            return _fallback("scope_need_but_docs_node_missing")

    # 5) amabilities => pas de quota_check dans le plan
    if intent == "amabilities":
        if any(n.get("type") == "tool.quota_check" for n in nodes):
            return _fallback("amabilities_has_quota_check")

    # 6) depends_on doit référencer des IDs existants
    id_set = set(ids)
    for n in nodes:
        deps = n.get("depends_on")
        if deps is None:
            continue
        if not isinstance(deps, list) or any(str(d) not in id_set for d in deps):
            return _fallback("plan_invalid_dependencies")

    return plan

def _normalize_brain_key(x: Any) -> Optional[str]:
    s = str(x or "").strip()
    return s or None


def _state_covers_brain(state: str, brain_key: Optional[str]) -> bool:
    b = str(brain_key or "").strip()
    s = str(state or "").strip()

    if not b or not s:
        return False

    if b == s:
        return True

    if b == f"{s}_light":
        return True

    # cas important : discovery light déjà couverte par state discovery
    if s == "discovery_capabilities" and b == "discovery_capabilities_light":
        return True

    return False


def _pick_matching_loop(
    *,
    loops: List[Dict[str, Any]],
    user_message: str,
) -> Optional[Dict[str, Any]]:
    """
    Heuristique simple et robuste pour choisir UNE loop potentiellement pertinente.
    Pour l’instant :
    - on privilégie les loops qui ont un resume_brain_key
    - puis score décroissant
    - puis updated_at décroissant implicite si déjà trié en amont
    """
    if not isinstance(loops, list) or not loops:
        return None

    ranked: List[Dict[str, Any]] = []

    for loop in loops:
        if not isinstance(loop, dict):
            continue

        resume_brain_key = str(loop.get("resume_brain_key") or "").strip()
        score_raw = loop.get("score")
        try:
            score = float(score_raw or 0.0)
        except Exception:
            score = 0.0

        ranked.append(
            {
                **loop,
                "_has_resume_brain": bool(resume_brain_key),
                "_score_num": score,
            }
        )

    if not ranked:
        return None

    ranked.sort(
        key=lambda x: (
            1 if x.get("_has_resume_brain") else 0,
            x.get("_score_num", 0.0),
        ),
        reverse=True,
    )

    return ranked[0]


def _resolve_brain_strategy(
    *,
    state: str,
    intent_final: str,
    trial_feedback_prompt_enabled: bool,
    conversation_loops: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Règles :
    - primary_brain_key = intent_final
    - secondary_brain_key possible via loop active pertinente
    - pas de secondary si le state couvre déjà ce sujet
    - pas de secondary identique au primary
    - si trial feedback est actif et non couvert par state/primary,
      on peut l’utiliser comme secondary de repli
    """
    primary_brain_key = intent_final or None

    selected_loop = _pick_matching_loop(
        loops=conversation_loops,
        user_message="",
    )

    secondary_brain_key: Optional[str] = None
    secondary_brain_reason: Optional[str] = None
    resume_loop_id: Optional[str] = None
    keep_warm_topic = False

    if isinstance(selected_loop, dict):
        candidate = _normalize_brain_key(selected_loop.get("resume_brain_key"))

        if (
            candidate
            and candidate != primary_brain_key
            and not _state_covers_brain(state, candidate)
        ):
            secondary_brain_key = candidate
            secondary_brain_reason = "matched_active_loop"
            resume_loop_id = str(selected_loop.get("id") or "") or None
            keep_warm_topic = True

    # fallback trial feedback uniquement si rien d’autre n’a été retenu
    if (
        not secondary_brain_key
        and trial_feedback_prompt_enabled
        and primary_brain_key not in {"trial_feedback", "trial_feedback_light"}
        and not _state_covers_brain(state, "trial_feedback_light")
    ):
        secondary_brain_key = "trial_feedback_light"
        secondary_brain_reason = "trial_feedback_pending"
        resume_loop_id = None
        keep_warm_topic = True

    return {
        "primary_brain_key": primary_brain_key,
        "secondary_brain_key": secondary_brain_key,
        "secondary_brain_reason": secondary_brain_reason,
        "resume_loop_id": resume_loop_id,
        "keep_warm_topic": keep_warm_topic,
        "selected_loop": selected_loop,
    }

def _normalize_text(s: Any) -> str:
    return str(s or "").strip().lower()


def _extract_actions_catalog(ctx: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    actions = (((ctx or {}).get("actions") or {}).get("actions") or [])
    if not isinstance(actions, list):
        return []
    return [a for a in actions if isinstance(a, dict)]


def _extract_connected_integrations(ctx: Optional[Dict[str, Any]]) -> List[str]:
    integrations = (((ctx or {}).get("integrations") or {}).get("integrations") or [])
    if not isinstance(integrations, list):
        return []

    out: List[str] = []
    for item in integrations:
        if not isinstance(item, dict):
            continue
        if item.get("connected") is True:
            key = str(item.get("integration_key") or "").strip()
            if key:
                out.append(key)

    return out


def _resolve_task_execution_context(
    *,
    llm_task_key: Any,
    ctx: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Résolution déterministe :
    - prend UNE task_key candidate issue du LLM
    - la mappe vers la task_key canonique du catalogue
    - reconstruit le contexte d’exécution depuis la vraie action back
    """

    actions = _extract_actions_catalog(ctx)
    connected_integrations = _extract_connected_integrations(ctx)

    available_task_keys: List[str] = []
    actions_by_key: Dict[str, Dict[str, Any]] = {}

    for action in actions:
        if not isinstance(action, dict):
            continue

        task_key = str(action.get("task_key") or "").strip()
        if not task_key:
            continue

        if task_key not in actions_by_key:
            actions_by_key[task_key] = action
            available_task_keys.append(task_key)

    resolved = _resolve_best_catalog_key(
        candidate=llm_task_key,
        available_keys=available_task_keys,
        min_score=0.72,
    )

    matched_task_key = resolved.get("matched")
    if not resolved.get("accepted") or not matched_task_key:
        return {
            "task_detected": False,
            "task_key": None,
            "task_label": None,
            "task_status": "unknown",
            "task_category": None,
            "required_integrations": [],
            "connected_integrations": connected_integrations,
            "missing_integrations": [],
            "can_execute_now": False,
            "resolver": {
                "requested_raw": str(llm_task_key or ""),
                "requested_norm": resolved.get("requested_norm"),
                "matched": None,
                "score": float(resolved.get("score") or 0.0),
                "accepted": False,
            },
        }

    action = actions_by_key.get(matched_task_key) or {}

    required_integrations = action.get("required_integrations") or []
    if not isinstance(required_integrations, list):
        required_integrations = []

    required_integrations = [str(x).strip() for x in required_integrations if str(x).strip()]
    missing_integrations = [x for x in required_integrations if x not in connected_integrations]

    task_status = str(action.get("status") or "unknown").strip().lower()
    can_execute_now = task_status == "active" and len(missing_integrations) == 0

    return {
        "task_detected": True,
        "task_key": str(action.get("task_key") or "").strip() or None,
        "task_label": str(action.get("label") or "").strip() or None,
        "task_status": task_status,
        "task_category": str(action.get("category") or "").strip() or None,
        "required_integrations": required_integrations,
        "connected_integrations": connected_integrations,
        "missing_integrations": missing_integrations,
        "can_execute_now": can_execute_now,
        "resolver": {
            "requested_raw": str(llm_task_key or ""),
            "requested_norm": resolved.get("requested_norm"),
            "matched": matched_task_key,
            "score": float(resolved.get("score") or 0.0),
            "accepted": True,
        },
    }

class OrchestratorAgent:
    """
    LLM #1 — léger.
    Il décide intent + context_level + plan DAG.
    """

    def __init__(self, llm: LLMRuntime):
        self.llm = llm

    async def run(self, *, user_message: str, ctx: Optional[Dict[str, Any]] = None) -> OrchestratorResult:
        conversation_loops = _compact_conversation_loops(ctx or {})
        has_conversation_loops = len(conversation_loops) > 0

        ctx_json = json.dumps(ctx or {}, ensure_ascii=False, default=str)

        loops_block = f"""CONVERSATION_LOOPS_ACTIVES
    - has_conversation_loops: {has_conversation_loops}
    - loops_count: {len(conversation_loops)}
    - loops:
    {json.dumps(conversation_loops, ensure_ascii=False, indent=2)}
    """

        user_prompt = f"""Message utilisateur:
    {user_message}

    {loops_block}

    CONTEXTE (JSON, source de vérité): 
    {ctx_json}

    RÈGLES CRITIQUES:
    - Tu DOIS utiliser le CONTEXTE pour choisir intent.
    - Tu DOIS tenir compte des CONVERSATION_LOOPS_ACTIVES si elles existent.
    - Si le message utilisateur semble reprendre, approfondir, préciser ou déplacer légèrement un sujet déjà vivant dans une loop active,
      tu dois conserver le sujet de fond au lieu de reclasser trop vite sur un nouveau sujet superficiel.
    - Une conversation_loop active avec resume_brain_key pertinent est un signal fort de continuité conversationnelle.
    - transition_window et transition_reason viennent du CONTEXTE (ctx.gates). Tu ne les inventes jamais.
    - Tu peux les recopier tels quels dans ta sortie si tu les exposes, sinon ignore-les.

    SCHÉMA JSON (à suivre exactement):
    {json.dumps(JSON_SCHEMA_HINT, ensure_ascii=False)}
    """

        docs_block = _render_docs_scopes_block(ctx)
        system_prompt = SYSTEM_PROMPT + docs_block

        try:
            docs_ctx = (ctx or {}).get("docs") or {}
            docs_scopes_all = docs_ctx.get("scopes_all") or []
            if not isinstance(docs_scopes_all, list):
                docs_scopes_all = []

            from app.core.chat_logger import chat_logger
            chat_logger.info(
                "chat.orchestrator.docs_scopes_input",
                docs_scopes_count=len(docs_scopes_all),
                docs_scopes_sample=docs_scopes_all[:10],
                docs_block_len=len(docs_block or ""),
            )
        except Exception:
            pass

        try:
            from app.core.chat_logger import chat_logger
            chat_logger.info(
                "chat.orchestrator.conversation_loops",
                has_conversation_loops=has_conversation_loops,
                loops_count=len(conversation_loops),
                loop_types=[str(x.get("loop_type") or "") for x in conversation_loops],
                resume_brain_keys=[str(x.get("resume_brain_key") or "") for x in conversation_loops],
            )
        except Exception:
            pass

        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # ✅ FULL PROMPT LOG (chunked) — Orchestrator
        # (Ton llm_prompt_logger.py gère déjà le chunking, donc pas de log_big.py)
        log_llm_messages(
            event="llm.prompt.orchestrator",
            messages=llm_messages,
            trace={"agent": "orchestrator", "phase": "intent+plan"},
        )

        data, meta = await self.llm.chat_json(
            messages=llm_messages,
            temperature=0.1,
            trace={"agent": "orchestrator", "phase": "intent+plan"},
        )
        
        raw_llm = data

        # ✅ overrides déterministes (amabilities / functional)
        # data = _apply_overrides(user_message, data)

        # hard fallback si JSON invalide
        if not data:
            language = "fr"
            intent: IntentType = "cabinet_assistance"
            level: ContextLevel = "medium"
            plan = _fallback_plan_minimal("fr")
            return OrchestratorResult(
                ok=False,
                language=language,
                state=_normalize_state(_state_from_ctx(ctx)),
                intent=intent,
                primary_brain_key=intent,
                secondary_brain_key=None,
                secondary_brain_reason=None,
                resume_loop_id=None,
                keep_warm_topic=False,
                context_level=level,
                task_execution_context=None,
                need_web=False,
                web_search_prompt=None,
                confidence=0.0,
                plan=plan,
                debug={
                    "meta": meta,
                    "raw_llm": raw_llm,
                    "after_overrides": data,
                },
            )

        if not isinstance(data, dict):
            plan = _fallback_plan_minimal("fr")
            return OrchestratorResult(
                ok=False,
                language="fr",
                state=_normalize_state(_state_from_ctx(ctx)),
                intent="cabinet_assistance",
                primary_brain_key="cabinet_assistance",
                secondary_brain_key=None,
                secondary_brain_reason=None,
                resume_loop_id=None,
                keep_warm_topic=False,
                context_level="medium",
                task_execution_context=None,
                need_web=False,
                web_search_prompt=None,
                confidence=0.0,
                plan=plan,
                debug={"error": "INVALID_JSON_FROM_LLM", "meta": meta, "raw_llm": raw_llm},
            )
        
        state = _normalize_state(_state_from_ctx(ctx))
        language = _language_from_ctx(ctx)
        trial_feedback_prompt_enabled = _trial_feedback_active_from_ctx(ctx)
        primary_agent_key = None
        try:
            ob = (ctx or {}).get("onboarding") or {}
            if isinstance(ob, dict):
                primary_agent_key = ob.get("primary_agent_key")
                if isinstance(primary_agent_key, str):
                    primary_agent_key = primary_agent_key.strip() or None
        except Exception:
            primary_agent_key = None
        intent = data.get("intent") or "cabinet_assistance"
        level = data.get("context_level") or "medium"
        confidence = float(data.get("confidence") or 0.0)
        primary_brain_key_llm = _normalize_brain_key(data.get("primary_brain_key"))
        secondary_brain_key_llm = _normalize_brain_key(data.get("secondary_brain_key"))
        secondary_brain_reason_llm = str(data.get("secondary_brain_reason") or "").strip() or None
        resume_loop_id_llm = str(data.get("resume_loop_id") or "").strip() or None
        keep_warm_topic_llm = bool(data.get("keep_warm_topic") is True)

        need_web = bool(data.get("need_web") or False)
        web_search_prompt = data.get("web_search_prompt", None)

        scope_need = bool(data.get("scope_need") or False)

        # --- Escalation hints from fastpath (deterministic override) ---
        try:
            g = (ctx or {}).get("gates") or {}
            force_need_web = bool(g.get("force_need_web") is True)
            force_need_docs = bool(g.get("force_need_docs") is True)

            if force_need_web:
                need_web = True
                # si pas de prompt, on le remplira plus bas via ton autofill guardrail

            if force_need_docs:
                scope_need = True
        except Exception:
            pass

        ob = (ctx or {}).get("onboarding") or {}
        ob_status = str(ob.get("status") or "").strip().lower()
        ob_pro_mode = bool(ob.get("pro_mode") is True)
        smalltalk_intro_eligible = bool(((ctx or {}).get("gates") or {}).get("smalltalk_intro_eligible"))

        available_scopes = _get_available_doc_scopes(ctx)

        raw_scopes = data.get("scopes_selected") or []
        if not isinstance(raw_scopes, list):
            raw_scopes = []

        raw_scopes_clean: List[str] = []
        for s in raw_scopes[:DOCS_SCOPES_MAX]:
            if isinstance(s, str) and s.strip():
                raw_scopes_clean.append(s.strip())

        scopes_filter = _resolve_catalog_keys(
            candidates=raw_scopes_clean,
            available_keys=available_scopes,
            max_len=DOCS_SCOPES_MAX,
            min_score=0.72,
        )
        scopes_selected: List[str] = scopes_filter["kept"]

        # --- LOG FILTRAGE SCOPES ---
        try:
            from app.core.chat_logger import chat_logger
            chat_logger.info(
                "chat.orchestrator.docs_scopes_filter",
                requested_raw=scopes_filter["requested_raw"],
                kept=scopes_filter["kept"],
                rejected=scopes_filter["rejected"],
                available_scopes_count=len(available_scopes),
            )
        except Exception:
            pass

    

        # --- Business gates déterministes ---
        gate_out = _apply_business_gates(
            llm_intent=str(intent),
            user_message=user_message,
            ctx=ctx or {},
            confidence=confidence,
        )

        intent_final = gate_out["intent_final"]

        # =====================================================
        # HARD RULES DOCS
        # =====================================================

        # jamais de docs pour ces intents
        if intent_final in {"emotional_support", "amabilities", "out_of_scope"}:
            scope_need = False
            scopes_selected = []

        if intent_final == "out_of_scope":
            level = "light"
            need_web = False
            web_search_prompt = None
            scope_need = False
            scopes_selected = []

        # product_support => docs obligatoires si scopes dispo
        elif intent_final == "product_support":
            if len(available_scopes) > 0:
                scope_need = True

        # task_execution => docs si déjà pressenties et scopes dispo
        elif intent_final == "task_execution":
            if scope_need and len(available_scopes) > 0:
                scope_need = True

        # cabinet_assistance => pas de forçage dur
        # medical_assistance => pas de forçage dur
        # patient_case_assistance => pas de forçage dur

        # si scope_need=false => scopes_selected=[]
        if not scope_need:
            scopes_selected = []

        # si scope_need=true mais aucun scope valide => off
        if scope_need and len(scopes_selected) == 0 and state != "discovery_capabilities":
            scope_need = False

        intent_final = gate_out["intent_final"]

        playbook_need = False
        playbook_level = None
            
        mode = state
        gates = gate_out["gates"]

        # --- Guardrail scopes: jamais pendant smalltalk_onboarding / amabilities ---
        if state == "smalltalk_onboarding" or intent_final == "amabilities":
            scope_need = False
            scopes_selected = []

        # --- Discovery capabilities: scope obligatoire ---
        if state == "discovery_capabilities":
            scope_need = True
            scopes_selected = _ensure_mandatory_scope(
                scopes_selected,
                MANDATORY_DISCOVERY_SCOPE,
                DOCS_SCOPES_MAX,
            )

        # --- Transition window: source de vérité = ctx.gates (calculé côté context_loader) ---
        ctx_gates = (ctx or {}).get("gates") or {}
        transition_window = bool(ctx_gates.get("transition_window"))
        transition_reason = ctx_gates.get("transition_reason")

        if transition_reason is not None:
            transition_reason = str(transition_reason)[:80]

        intent_eligible = gate_out["intent_eligible"]
        intent_block_reason = gate_out["intent_block_reason"]
        capabilities = gate_out["capabilities"]
        signals = gate_out["signals"]

        task_execution_context = None
        if intent_final == "task_execution":
            llm_task_key_candidate = None
            raw_task_ctx = data.get("task_execution_context") or {}
            if isinstance(raw_task_ctx, dict):
                llm_task_key_candidate = raw_task_ctx.get("task_key")

            task_execution_context = _resolve_task_execution_context(
                llm_task_key=llm_task_key_candidate,
                ctx=ctx,
            )

        try:
            from app.core.chat_logger import chat_logger
            chat_logger.info(
                "chat.orchestrator.task_key_resolution",
                llm_task_key_candidate=llm_task_key_candidate if intent_final == "task_execution" else None,
                resolved_task_key=(task_execution_context or {}).get("task_key"),
                task_detected=bool((task_execution_context or {}).get("task_detected")),
                task_status=(task_execution_context or {}).get("task_status"),
                resolver=((task_execution_context or {}).get("resolver") or {}),
            )
        except Exception:
            pass

        brain_strategy = _resolve_brain_strategy(
            state=state,
            intent_final=intent_final,
            trial_feedback_prompt_enabled=trial_feedback_prompt_enabled,
            conversation_loops=conversation_loops,
        )

        primary_brain_key = brain_strategy["primary_brain_key"]
        secondary_brain_key = brain_strategy["secondary_brain_key"]
        secondary_brain_reason = brain_strategy["secondary_brain_reason"]
        resume_loop_id = brain_strategy["resume_loop_id"]
        keep_warm_topic = brain_strategy["keep_warm_topic"]
        selected_loop = brain_strategy["selected_loop"]

        # Override très encadré du secondary brain proposé par le LLM :
        # autorisé seulement si
        # - il existe déjà un secondary candidat backend vide
        # - la clé LLM n'est pas couverte par le state
        # - la clé LLM n'est pas identique au primary
        # On ne laisse PAS le LLM changer le primary brain.
        if (
            not secondary_brain_key
            and secondary_brain_key_llm
            and secondary_brain_key_llm != primary_brain_key
            and not _state_covers_brain(state, secondary_brain_key_llm)
        ):
            secondary_brain_key = secondary_brain_key_llm
            secondary_brain_reason = secondary_brain_reason_llm or "llm_secondary_brain"
            resume_loop_id = resume_loop_id_llm or resume_loop_id
            keep_warm_topic = keep_warm_topic_llm or keep_warm_topic

        # --- Plan stable (on ignore le "plan" du LLM, trop risqué) ---
        plan = _build_plan_minimal(
            language=language or "fr",
            state=state,
            intent=intent_final,
            primary_brain_key=primary_brain_key,
            secondary_brain_key=secondary_brain_key,
            secondary_brain_reason=secondary_brain_reason,
            resume_loop_id=resume_loop_id,
            keep_warm_topic=keep_warm_topic,
            mode=mode,
            task_execution_context=task_execution_context,
            need_web=need_web,
            web_search_prompt=web_search_prompt if need_web else None,
            context_level=level or "medium",
            gates=gates,
            intent_eligible=intent_eligible,
            intent_block_reason=intent_block_reason,
            transition_window=transition_window,
            transition_reason=transition_reason,
            scope_need=scope_need,
            scopes_selected=scopes_selected,
            trial_feedback_prompt_enabled=trial_feedback_prompt_enabled,
        )

        debug = data.get("debug") or {}

        debug["meta"] = meta
        debug["raw_llm"] = raw_llm

        debug["gates"] = gates
        debug["capabilities"] = capabilities
        debug["signals"] = signals
        debug["mode"] = mode
        debug["intent_final"] = intent_final
        debug["intent_eligible"] = intent_eligible
        debug["intent_block_reason"] = intent_block_reason
        debug["scope_need"] = scope_need
        debug["scopes_selected"] = scopes_selected
        debug["docs_scopes_count"] = int(((ctx or {}).get("docs") or {}).get("scopes_count") or 0)
        debug["trial_feedback_prompt_enabled"] = trial_feedback_prompt_enabled
        debug["primary_brain_key"] = primary_brain_key
        debug["secondary_brain_key"] = secondary_brain_key
        debug["secondary_brain_reason"] = secondary_brain_reason
        debug["resume_loop_id"] = resume_loop_id
        debug["keep_warm_topic"] = keep_warm_topic
        debug["selected_loop"] = selected_loop
        debug["llm_primary_brain_key"] = primary_brain_key_llm
        debug["llm_secondary_brain_key"] = secondary_brain_key_llm
        debug["task_execution_context"] = task_execution_context
        debug["task_detected"] = bool((task_execution_context or {}).get("task_detected"))
        debug["task_key"] = (task_execution_context or {}).get("task_key")
        debug["task_status"] = (task_execution_context or {}).get("task_status")
        debug["task_can_execute_now"] = bool((task_execution_context or {}).get("can_execute_now"))
        debug["task_missing_integrations"] = (task_execution_context or {}).get("missing_integrations") or []
        debug["docs_available_scopes_count"] = len(available_scopes)
        debug["docs_requested_raw_scopes"] = scopes_filter["requested_raw"]
        debug["docs_rejected_scopes"] = scopes_filter["rejected"]
        debug["docs_kept_scopes"] = scopes_filter["kept"]

        # --- Guardrails MINIMAUX (pas de correction d'intent) ---

        # 1) low confidence => on NE tue PAS le plan.
        # On garde le plan déterministe construit (qui peut inclure web/docs).
        # On signale juste pour debug + éventuellement analytics.
        if confidence < 0.80:
            debug["low_confidence_reason"] = debug.get("low_confidence_reason") or "confidence_below_0_80"
            debug["low_confidence_soft"] = True

        # 2) cohérence need_web
        # Si need_web=true, on ne le désactive jamais ici.
        # On génère un prompt minimal déterministe si le LLM a oublié de le fournir.
        if need_web and (not isinstance(web_search_prompt, str) or not web_search_prompt.strip()):
            # pays via locale_main si dispo (ex: fr-FR -> FR)
            locale_main = ""
            try:
                locale_main = str(((ctx or {}).get("settings") or {}).get("locale_main") or "")
            except Exception:
                locale_main = ""
            country = (locale_main.split("-")[1] if "-" in locale_main else "").strip().upper()

            web_search_prompt = (
                f"{user_message}\n"
                f"Contexte: utilisateur en {country or 'EU'}.\n"
                f"Objectif: réponse exacte et à jour, avec sources fiables.\n"
                f"Priorité: sources officielles / docs éditeurs / organismes reconnus."
            )[:500]

            debug["web_prompt_missing_autofilled"] = True

        debug["web_final"] = {"need_web": need_web, "has_prompt": bool((web_search_prompt or "").strip())}

        # 3) amabilities => contraintes hard
        if intent_final == "amabilities":
            level = "light"
            need_web = False
            web_search_prompt = None

        # 4) plan obligatoire + sanitize
        plan = _sanitize_plan_or_fallback(
            plan=plan,
            language=language or "fr",
            intent=intent_final,
            need_web=need_web,
            web_search_prompt=web_search_prompt,
            scope_need=scope_need,
            scopes_selected=scopes_selected,
            debug=debug,
        )

        # si sanitize a fallback => ok=false
        if debug.get("fallback_used"):
            return OrchestratorResult(
                ok=False,
                language=language or "fr",
                state=state,
                intent="cabinet_assistance",
                primary_brain_key="cabinet_assistance",
                secondary_brain_key=None,
                secondary_brain_reason=None,
                resume_loop_id=None,
                keep_warm_topic=False,
                context_level="medium",
                task_execution_context=None,
                need_web=False,
                web_search_prompt=None,
                confidence=confidence,
                plan=plan,
                debug=debug,
            )

        return OrchestratorResult(
            ok=True,
            language=language or "fr",
            state=state,
            intent=intent_final,
            primary_brain_key=primary_brain_key,
            secondary_brain_key=secondary_brain_key,
            secondary_brain_reason=secondary_brain_reason,
            resume_loop_id=resume_loop_id,
            keep_warm_topic=keep_warm_topic,
            context_level=level,
            task_execution_context=task_execution_context,
            need_web=need_web,
            web_search_prompt=web_search_prompt if need_web else None,
            confidence=confidence,
            plan=plan,
            debug=debug,
        )