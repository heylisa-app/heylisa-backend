# app/agents/orchestrator.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal

from app.llm.runtime import LLMRuntime

from app.agents.node_registry import (
    NODE_TYPE_WHITELIST,
    render_nodes_whitelist_block,
    render_ids_rules_block,
)


IntentType = Literal[
    "onboarding",
    "small_talk",
    "amabilities",
    "functional_question",
    "general_question",
    "decision_support",
    "motivational_guidance",
    "action_request",
    "deep_work",
    "professional_request",
    "sensitive_question",
    "urgent_request",
]

ContextLevel = Literal["light", "medium", "max"]

# NOTE: v1 — plan minimal : P1 parallel [context + quota] puis response_writer
@dataclass
class OrchestratorResult:
    ok: bool
    language: str
    intent: IntentType
    context_level: ContextLevel
    need_web: bool
    web_search_prompt: Optional[str]
    confidence: float
    plan: Dict[str, Any]
    debug: Dict[str, Any]



SYSTEM_PROMPT = f"""Tu es OrchestratorAgent de Lisa, assistante IA exécutive.

... 
═══════════════════════════════════════════════════════════════
CONTEXTE LISA

Lisa accompagne l'utilisateur dans sa vie personnelle et professionnelle.

Modes disponibles :
- Assistante Personnelle (actuel) : conseil, aide décision, accompagnement. N'exécute PAS d'actions (réservations, emails...).
- Ultimate Assistant (payant) : exécution actions concrètes (agenda, emails, réservations, finances).
- Modes Pro (payant, selon métier) : Assistante Médicale, Assistant Airbnb, etc.

Quota freemium : 8 messages gratuits (lifetime). Au-delà : paywall.

═══════════════════════════════════════════════════════════════
INTENTS (classification exhaustive)

onboarding
→ Découverte de Lisa
→ Signaux : Moins de 20 messages échangés
→ level=light

small_talk
→ Conversation légère, prise de nouvelles, glaner facts clés (tutoiement, ville, activité, etc.)
→ Signaux : "Comment ça va ?", "Quoi de neuf ?", "Ça roule ?"
→ level=medium

amabilities
→ Salutation départ, politesse finale, remerciement bref
→ Signaux : "Au revoir", "Bonne nuit", "Merci", "Bye", "À plus"
→ level=light, AUCUN small talk, réponse brève
→ PAS de quota_check (node B retiré)

functional_question
→ Question sur HeyLisa (fonctionnement, features, RGPD, CGV, prix)
→ Signaux : "Que peux-tu faire ?", "Comment tu fonctionnes ?", "Tes fonctionnalités ?", "RGPD ?", "Prix ?"
→ level=medium

general_question
→ Connaissance générale, actualité, culture, info pratique
→ Signaux : "Capitale France ?", "Météo demain ?", "Qui a gagné le match ?"
→ level=medium

decision_support
→ Aide choix, dilemme, décision importante
→ Signaux : "Aide-moi à choisir", "Je ne sais pas quoi faire", "Dois-je X ou Y ?"
→ level=max

motivational_guidance
→ Encouragement, motivation, perspective philosophique
→ Signaux : "Je suis découragé", "J'ai besoin de motivation", "Pourquoi continuer ?"
→ level=max

action_request
→ Demande exécution action concrète
→ Signaux : "Réserve-moi X", "Rappelle-moi de Y", "Envoie email à Z"
→ level=medium
→ Si mode Personal : déclinaison + upsell Ultimate

deep_work
→ Travail approfondi (analyse doc, synthèse, rédaction, recherche complexe)
→ Signaux : "Analyse ce document", "Synthèse de X", "Recherche tout sur Y"
→ level=medium (ou max si lié projets user)

professional_request
→ Demande liée métier spécialisé (patient, client, dossier, cabinet)
→ Signaux : "Mon patient X", "Dossier client Y", "Réservation Airbnb"
→ level=max
→ Si mode pro absent : proposer activation

sensitive_question
→ Santé, finance perso, juridique, info sensible
→ Signaux : "Symptômes X", "Problème santé", "Mes finances", "Impôts", "Juridique"
→ level=max, mode sécurisé (renvoi pro qualifié)

urgent_request
→ Urgence, panique, stress aigu, besoin immédiat
→ Signaux : "Urgent !", "Je panique", "Aide vite", "Critique", "Là maintenant"
→ level=medium, AUCUN small talk, tone=calm

Priorité si ambiguïté :
urgent_request > sensitive_question > professional_request > decision_support > 
action_request > functional_question > general_question > motivational_guidance > 
onboarding > small_talk > amabilities

═══════════════════════════════════════════════════════════════
WEB SEARCH (need_web)

need_web=true si au moins 1 condition :
A) Volatilité (actu, prix, offres, compatibilités, "meilleur X", comparatifs)
B) Exactitude critique (juridique/admin/fiscal/santé/finance) → quasi systématique
C) Besoin sources/liens vérifiables
D) Automation/outils/intégrations/APIs (priorité)

need_web=false si :
- Question conceptuelle/coaching/organisation sans dépendance faits externes
- Contexte fourni suffit et stable

web_search_prompt (strict si need_web=true) :
- 3-4 lignes max
- Inclure pays + contexte + mots-clés + contrainte
- Privilégier sources fiables
- Si need_web=true => web_search_prompt DOIT être non vide.
Sinon web_search_prompt=null.

═══════════════════════════════════════════════════════════════ ...

{render_nodes_whitelist_block()}
{render_ids_rules_block()}

TON JOB
Analyser message user → Produire plan DAG optimal.

LANGUE
- language = fr, en, es, de, it, pt, other
- Si incertain: language="fr"

SORTIE: voir schéma.
"""


JSON_SCHEMA_HINT = {
    "ok": True,
    "language": "fr",
    "intent": "general_question",
    "context_level": "medium",
    "need_web": False,
    "web_search_prompt": None,
    "confidence": 0.92,
    "plan": {
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
                    "intent": "general_question",
                    "language": "fr",
                    "tone": "warm",
                    "include_smalltalk": False,
                    "need_web": False,
                },
            },
        ]
    },
    "debug": {"notes": "short", "signals": []},
}


def _safe_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _fallback_plan_minimal(language: str = "fr") -> Dict[str, Any]:
    """
    Filet de sécurité uniquement.
    Plan standard (toujours le même), pour éviter de crasher si le LLM sort un truc invalide.
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
                    "intent": "general_question",
                    "language": language,
                    "tone": "warm",
                    "include_smalltalk": False,
                    "need_web": False,
                },
            },
        ]
    }

def _sanitize_plan_or_fallback(
    *,
    plan: Any,
    language: str,
    intent: str,
    need_web: bool,
    web_search_prompt: Optional[str],
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

    # 4) need_web => node tool.web_search obligatoire + prompt non vide
    if need_web:
        if not isinstance(web_search_prompt, str) or not web_search_prompt.strip():
            return _fallback("need_web_but_prompt_missing")

        if not any(n.get("type") == "tool.web_search" for n in nodes):
            return _fallback("need_web_but_web_node_missing")

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

class OrchestratorAgent:
    """
    LLM #1 — léger.
    Il décide intent + context_level + plan DAG.
    """

    def __init__(self, llm: LLMRuntime):
        self.llm = llm

    async def run(self, *, user_message: str) -> OrchestratorResult:
        user_prompt = f"""Message utilisateur:
{user_message}

RÈGLE CRITIQUE:
- Ta décision DOIT dépendre du message user.
- Interdit de répéter toujours le même intent.

Exemples rapides:
- "Bonne nuit" -> intent=amabilities
- "Aide-moi à choisir" -> intent=decision_support

IMPORTANT (WEB SEARCH):
- need_web doit suivre strictement les règles WEB SEARCH.
- Si need_web=true => web_search_prompt non vide (3-4 lignes max).

SCHÉMA JSON (à suivre exactement):
{json.dumps(JSON_SCHEMA_HINT, ensure_ascii=False)}
"""

        data, meta = await self.llm.chat_json(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        
        raw_llm = data

        # ✅ overrides déterministes (amabilities / functional)
        # data = _apply_overrides(user_message, data)

        # hard fallback si JSON invalide
        if not data:
            language = "fr"
            intent: IntentType = "general_question"
            level: ContextLevel = "medium"
            plan = _fallback_plan_minimal("fr")
            return OrchestratorResult(
                ok=False,
                language=language,
                intent=intent,
                context_level=level,
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
                intent="general_question",
                context_level="medium",
                need_web=False,
                web_search_prompt=None,
                confidence=0.0,
                plan=plan,
                debug={"error": "INVALID_JSON_FROM_LLM", "meta": meta, "raw_llm": raw_llm},
            )

        language = str(data.get("language") or "fr")
        intent = data.get("intent") or "general_question"
        level = data.get("context_level") or "medium"
        confidence = float(data.get("confidence") or 0.0)

        need_web = bool(data.get("need_web") or False)
        web_search_prompt = data.get("web_search_prompt", None)

        plan = data.get("plan")
        debug = data.get("debug") or {}

        debug["meta"] = meta
        debug["raw_llm"] = raw_llm

        # --- Guardrails MINIMAUX (pas de correction d'intent) ---

        # 1) low confidence => refuse (ok=false) + plan minimal safe
        if confidence < 0.80:
            debug["low_confidence_reason"] = debug.get("low_confidence_reason") or "confidence_below_0_80"
            debug["fallback_used"] = True
            plan = _fallback_plan_minimal(language or "fr")
            return OrchestratorResult(
                ok=False,
                language=language or "fr",
                intent=intent,
                context_level="medium",
                need_web=False,
                web_search_prompt=None,
                confidence=confidence,
                plan=plan,
                debug=debug,
            )

        # 2) cohérence need_web
        if need_web and (not isinstance(web_search_prompt, str) or not web_search_prompt.strip()):
            need_web = False
            web_search_prompt = None
            debug["web_prompt_missing"] = True

        # 3) amabilities => contraintes hard
        if intent == "amabilities":
            level = "light"
            need_web = False
            web_search_prompt = None

        # 4) plan obligatoire + sanitize
        plan = _sanitize_plan_or_fallback(
            plan=plan,
            language=language or "fr",
            intent=intent,
            need_web=need_web,
            web_search_prompt=web_search_prompt,
            debug=debug,
        )

        # si sanitize a fallback => ok=false
        if debug.get("fallback_used"):
            return OrchestratorResult(
                ok=False,
                language=language or "fr",
                intent="general_question",
                context_level="medium",
                need_web=False,
                web_search_prompt=None,
                confidence=confidence,
                plan=plan,
                debug=debug,
            )

        return OrchestratorResult(
            ok=True,
            language=language or "fr",
            intent=intent,
            context_level=level,
            need_web=need_web,
            web_search_prompt=web_search_prompt if need_web else None,
            confidence=confidence,
            plan=plan,
            debug=debug,
        )