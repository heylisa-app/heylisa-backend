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
    "smalltalk_intro",
    "discovery",
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
MANDATORY_DISCOVERY_SCOPE = "discovery.value_proposition"
DOCS_SCOPES_MAX = 5

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

smalltalk_intro

→ Small talk de connexion strict pour collecter les facts minimum (tu/vous, prénom, ville, activité).
→ Actif seulement si quota OK ET facts minimum incomplets.
→ Au niveau orchestrator : tu actives le mode via inputs vers response_writer.
→ level=light

RÈGLE SMALLTALK_INTRO (DÉTERMINISTE)
Si ctx.user_status.is_pro = false
ET ctx.user_status.state != "blocked"
ET ctx.user_status.free_quota_used < ctx.user_status.free_quota_limit
ET ctx.user_facts.missing_required_count > 0
ALORS intent = smalltalk_intro
SAUF si le dernier message utilisateur est manifestement hors phase d’intro
(ex: question produit, demande urgente, sujet sensible, etc.).

⸻

discovery

→ Phase de découverte guidée (présentation + cadrage) : “qu’est-ce que Lisa peut faire pour moi ?”
→ level=light

RÈGLE PRIORITAIRE (DÉTERMINISTE — cas forcé)
Si ctx.gates.discovery_forced = true ET ctx.gates.discovery_status != "complete"
ALORS intent = discovery (peu importe le message utilisateur)
SAUF si l’intent doit être urgent_request ou sensitive_question.

RÈGLE NON CONTRAINTE (LIBRE ARBITRE — exploration du champ des possibles)
Même si ctx.gates.discovery_forced = false, tu peux choisir intent=discovery si :
	•	l’utilisateur explore de façon vague le champ des possibles (“tu peux faire quoi pour moi”, “comment tu peux m’aider”, “par où commencer”, “je veux voir ce que tu sais faire”),
	•	OU l’utilisateur poursuit naturellement la séquence de découverte initiée (ex: après une réponse discovery, il demande “ok et ensuite ?”, “donne-moi des exemples”, “quels cas d’usage ?”).

Distinction clé vs functional_question
	•	discovery = exploration large / intention floue / cadrage global / “quoi pour moi ? / gibberish/test clavier (“jhgfsghdjs”, “aaaaa”, etc.) ”
	•	functional_question = question précise sur une fonctionnalité, une règle, un pricing, un aspect RGPD/CGV, etc.

RÈGLES DOCUMENTATION (Discovery)
	•	scope_need = true
	•	Tu DOIS sélectionner 1 à 5 scopes max dans “DOCUMENTATION DISPONIBLE (SCOPES EXACTS)”
	•	scopes_selected = liste de strings
	•	Si aucun scope pertinent : scope_need=false et scopes_selected=[]
    •	Scope obligatoire dès que discovery actif ou toute question qui permet de chosiir la meilleure offre HeyLisa par profil = "discovery.value_proposition"

⸻

onboarding (critique payant)

→ Phase d’onboarding après activation d’un mode payant (Personal / Ultimate / Mode Pro).
→ Objectif : aider l’utilisateur à prendre la main sur le service qu’il vient de payer (setup, cadrage, premières actions, connexions).
→ level=medium (ou max si mode Pro sensible type médical)

Déclencheurs / Signaux forts
	•	Message proactif de Lisa post-paiement (“merci / bienvenue / on configure”)
	•	L’utilisateur demande “on commence”, “comment on setup”, “je veux connecter X”, “explique-moi le process”, “quelles infos tu as besoin”
	•	Les échanges sont centrés sur : setup, permissions, connexions, règles, préférences, workflow de démarrage, checklist.

RÈGLE DE CONTINUITÉ (dynamique)
Tant que la conversation reste dans la dynamique du 1er message post paiement (guidage setup), tu restes en onboarding.
Même si Lisa pose des questions (“combien de personnes”, “à qui je reporte”, etc.), ce n’est pas du smalltalk, c’est de l’onboarding.

Source de vérité (backend attendu)
Tu utilises ctx.onboarding (ou équivalent) dès qu’il existe.
	•	ctx.onboarding.status ∈ (pending,started,complete)
	•	ctx.onboarding.active_agent_mode (ex: ultimate, medical, airbnb)
	•	ctx.onboarding.started_at

Sortie déterministe “complete” (logique attendue côté backend)
	•	Si mode = personal_assistant : complete si l’utilisateur réécrit spontanément >48h après started_at.
	•	Si mode = ultimate ou pro : complete dès qu’au moins un des événements arrive après paiement :
	1.	une demande d’action réalisée (action_request)
	2.	une intégration connectée / permission validée

Tant que ctx.onboarding.status == started et pas complete, l’intent onboarding doit être fortement favorisé (sauf urgence/sensible).

⸻

small_talk

→ Conversation légère, prise de nouvelles, lien social, glaner facts non bloquants.
→ Signaux : “Comment ça va ?”, “Quoi de neuf ?”, “Ça roule ?”
→ level=medium

⚠️ Règle dynamique : si un thread est actif (deep_work / decision_support / onboarding / professional_request / action_request), un “ok / go / continue” n’est pas small_talk.

⸻

amabilities

→ Salutation départ, politesse finale, remerciement bref.
→ Signaux : “Au revoir”, “Bonne nuit”, “Merci”, “Bye”, “À plus”
→ level=light ; réponse brève ; aucun small talk
→ PAS de quota_check (node B retiré)

⚠️ Règle dynamique : si le message est un “merci/ok” dans un thread actif, ce n’est pas amabilities (continuité > politesse).

⸻

functional_question

→ Question sur HeyLisa : fonctionnement, features, RGPD, CGV, prix, limites, compatibilités.
→ Signaux : “Comment tu organises les mails ?”, “Je clique où pour ouvrir l'espace Deep Work ?”, “RGPD ?”, “Je veux supprimer mon compte”
→ level=medium

Distinction : si l’utilisateur est en exploration vague “quelles sont tes fonctionnalités ?”, c’est discovery, pas functional_question.

⸻

general_question

→ Connaissance générale, info pratique, culture, actualité.
→ Signaux : “Capitale…”, “Météo…”, “Qui a gagné…”, “C’est quoi…”
→ level=medium

⸻

decision_support

→ Aide au choix, à la décision / dilemme / arbitrage important.
→ Signaux : “Aide-moi à choisir”, “Dois-je X ou Y ?”, “Quelle option est la meilleure ?”
→ level=max

⸻

motivational_guidance

→ Motivation / soutien / perspective / recadrage.
→ Signaux : “Je suis découragé”, “J’ai besoin de motivation”, “Pourquoi continuer ?”
→ level=max

⸻

action_request

→ Demande d’exécution d’une action concrète.
→ Signaux : “Réserve…”, “Rappelle-moi…”, “Envoie un email…”, “Planifie…”
→ level=medium

⸻

deep_work

→ Travail approfondi : analyse, synthèse, dev, rédaction, recherche complexe.
→ Signaux : “Analyse ce document”, "travaillon sur mon mémoire", “Synthèse de…”, “Recherche tout sur…”, “écris / code…”
→ level=medium (ou max si lié aux projets/contraintes de l’utilisateur)

⸻

professional_request

→ Demande liée à un métier / cadre pro spécifique (dossier client/patient, cabinet, Airbnb ops).
→ Signaux : “Mon patient…”, “Dossier client…”, “Réservation Airbnb…”
→ level=max
→ Si mode pro absent : proposer activation du mode correspondant.

⸻

sensitive_question

→ Santé, finance perso, juridique, info sensible.
→ Signaux : symptômes, impôts, juridique, situation médicale, etc.
→ level=max 

⸻

urgent_request

→ Urgence, panique, stress aigu, besoin immédiat.
→ Signaux : “Urgent”, “Je panique”, “Là maintenant”, “Critique”
→ level=medium 

⸻

Priorité si ambiguïté

urgent_request > sensitive_question > onboarding > professional_request > decision_support >
action_request > functional_question > general_question > motivational_guidance >
discovery > small_talk > amabilities

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

═══════════════════════════════════════════════════════════════
RÈGLE CLÉ — DYNAMIQUE DE CONVERSATION (OBLIGATOIRE)

Tu ne classes JAMAIS l'intent uniquement sur le dernier message.
Tu dois d'abord analyser la dynamique des 10 derniers messages (ctx.history.messages) :

- Si une tâche est en cours (deep_work / decision_support / professional_request / action_request),
  alors un message court ("ok", "vas-y", "continue", "parfait", "merci") signifie très souvent :
  -> continuer le même intent (continuité de thread), pas "amabilities".

- Si le dernier intent assistant est disponible (metadata intent_final/mode), tu l'utilises comme signal fort
  pour interpréter le message utilisateur, sauf si le contexte global ne rend plus la conversation éligible à un intent donné (smalltalk_intro).

Le dernier message utilisateur sert surtout à ajuster :
- la priorité,
- need_web,
- les scopes docs,
- et le niveau de contexte.

TON JOB
Analyser message user dans son contexte (tenir compte des échanges précédents) → Produire plan DAG optimal pour répondre au dernier message user.

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

  "scope_need": False,
  "scopes_selected": [],

  "plan":  {
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

def _compute_discovery_gate(ctx: Dict[str, Any]) -> Dict[str, Any]:
    gates = (ctx or {}).get("gates") or {}
    return {
        "discovery_forced": bool(gates.get("discovery_forced")),
        "discovery_status": gates.get("discovery_status"),
        "transition_window": bool(gates.get("transition_window")),
        "transition_reason": gates.get("transition_reason"),
    }

def _compute_onboarding_gate(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ob = (ctx or {}).get("onboarding") or {}
    status = ob.get("status")  # started|complete|None
    pro_mode = bool(ob.get("pro_mode"))
    agent_key = ob.get("primary_agent_key")
    return {
        "onboarding_status": status,
        "pro_mode": pro_mode,
        "primary_agent_key": agent_key,
        "onboarding_active": (status == "started" and pro_mode),
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
    """
    Retourne:
      - intent_final
      - mode: "smalltalk_intro" | "normal"
      - intent_eligible bool
      - intent_block_reason str|None
      - gates/capabilities pass-through
    """
    gate = _compute_smalltalk_intro_gate(ctx)
    caps = _compute_capabilities(ctx)
    discvr = _compute_discovery_gate(ctx)
    discovery_forced = bool(discvr.get("discovery_forced"))
    obg = _compute_onboarding_gate(ctx)
    onboarding_active = bool(obg.get("onboarding_active"))

    eligible_intro = bool(gate["smalltalk_intro_eligible"])
    short_ack = _is_short_ack(user_message)

    # 1) Overrides qui cassent l'intro (si explicitement détectés)
    hard_overrides = {"urgent_request", "sensitive_question"}
    soft_overrides = {
        "functional_question",
        "general_question",
        "decision_support",
        "motivational_guidance",
        "professional_request",
        "action_request",
        "deep_work",
    }

    intent = (llm_intent or "general_question").strip()

    # 1) smalltalk_intro gate (prioritaire)
    if eligible_intro:
        if intent in hard_overrides:
            mode = "normal"
            intent_final = intent
        elif intent in soft_overrides and confidence >= 0.85 and not short_ack:
            mode = "normal"
            intent_final = intent
        else:
            mode = "smalltalk_intro"
            intent_final = "smalltalk_intro"
    else:
        mode = "normal"
        intent_final = intent

    # 2) Forced discovery (si discovery_forced et discovery pas complete)
    #    Sauf urgences / sensible
    if discovery_forced and intent_final not in {"urgent_request", "sensitive_question"}:
        mode = "discovery"
        intent_final = "discovery"

    # 2bis) Forced onboarding (payant) si started + pro_mode
    if onboarding_active and intent_final not in {"urgent_request", "sensitive_question"}:
        mode = "onboarding"
        intent_final = "onboarding"

    # 3) Pendant intro: absorb amabilities/small_talk
    if mode == "smalltalk_intro" and intent_final in {"amabilities", "small_talk"}:
        intent_final = "smalltalk_intro"

    # 4) Pendant discovery: absorb amabilities/small_talk aussi
    if mode == "discovery" and intent_final in {"amabilities", "small_talk"}:
        intent_final = "discovery"

    if mode == "onboarding" and intent_final in {"amabilities", "small_talk"}:
        intent_final = "onboarding"

    # 4bis) Capabilities gating
    intent_eligible = True
    block_reason = None
    if intent_final in {"action_request", "deep_work", "professional_request"}:
        # tu as dit: dispo seulement si agent payant actif au-delà de personal_assistant
        if not caps.get("has_paid_agent"):
            intent_eligible = False
            block_reason = "AGENT_NOT_ACTIVE"

    return {
        "intent_final": intent_final,
        "mode": mode,
        "intent_eligible": intent_eligible,
        "intent_block_reason": block_reason,
        "discovery": discvr,
        "gates": gate,
        "capabilities": caps,
        "signals": {"short_ack": short_ack},
    }


def _build_plan_minimal(
    *,
    language: str,
    intent: str,
    mode: str,
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
) -> Dict[str, Any]:
    """
    Plan stable, peu risqué.
    """
    nodes = [
        {
            "id": "A",
            "type": "tool.db_load_context",
            "parallel_group": "P1",
            "inputs": {"level": context_level or "medium"},
        },
    ]

    # amabilities en mode normal => pas de quota_check
    if not (mode == "normal" and intent == "amabilities"):
        nodes.append({"id": "B", "type": "tool.quota_check", "parallel_group": "P1"})

    if need_web:
        nodes.append(
            {
                "id": "C",
                "type": "tool.web_search",
                "depends_on": ["A"] if not any(n["id"] == "B" for n in nodes) else ["A", "B"],
                "inputs": {"prompt": web_search_prompt, "language": language},
            }
        )

    # --- Documentation chunks (scopes) ---
    if scope_need:
        nodes.append(
            {
                "id": "S",
                "type": "tool.docs_chunks",
                "depends_on": ["A"],
                "inputs": {
                    "scopes": scopes_selected[:DOCS_SCOPES_MAX],  # hard cap sécurité
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
                "intent": intent,
                "mode": mode,
                "language": language,
                "tone": "warm",
                "need_web": need_web,
                "smalltalk_target_key": (gates or {}).get("smalltalk_target_key"),
                "intent_eligible": intent_eligible,
                "intent_block_reason": intent_block_reason,

                "transition_window": bool(transition_window),
                "transition_reason": transition_reason,
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

    # 4) need_web => node tool.web_search obligatoire + prompt non vide
    if need_web:
        if not isinstance(web_search_prompt, str) or not web_search_prompt.strip():
            return _fallback("need_web_but_prompt_missing")

        if not any(n.get("type") == "tool.web_search" for n in nodes):
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

class OrchestratorAgent:
    """
    LLM #1 — léger.
    Il décide intent + context_level + plan DAG.
    """

    def __init__(self, llm: LLMRuntime):
        self.llm = llm

    async def run(self, *, user_message: str, ctx: Optional[Dict[str, Any]] = None) -> OrchestratorResult:
        ctx_json = json.dumps(ctx or {}, ensure_ascii=False, default=str)

        user_prompt = f"""Message utilisateur:
    {user_message}

    CONTEXTE (JSON, source de vérité): 
    {ctx_json}

    RÈGLES CRITIQUES:
    - Tu DOIS utiliser le CONTEXTE pour choisir intent.
    - transition_window et transition_reason viennent du CONTEXTE (ctx.gates). Tu ne les inventes jamais.
    - Tu peux les recopier tels quels dans ta sortie si tu les exposes, sinon ignore-les.

    SCHÉMA JSON (à suivre exactement):
    {json.dumps(JSON_SCHEMA_HINT, ensure_ascii=False)}
    """

        docs_block = _render_docs_scopes_block(ctx)
        system_prompt = SYSTEM_PROMPT + docs_block

        data, meta = await self.llm.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            trace={"agent": "orchestrator", "phase": "intent+plan"},
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

        language = _language_from_ctx(ctx)
        intent = data.get("intent") or "general_question"
        level = data.get("context_level") or "medium"
        confidence = float(data.get("confidence") or 0.0)

        need_web = bool(data.get("need_web") or False)
        web_search_prompt = data.get("web_search_prompt", None)

        scope_need = bool(data.get("scope_need") or False)

        raw_scopes = data.get("scopes_selected") or []
        scopes_selected: List[str] = []
        if isinstance(raw_scopes, list):
            for s in raw_scopes[:DOCS_SCOPES_MAX]:
                if isinstance(s, str) and s.strip():
                    scopes_selected.append(s.strip())

        # Règle 1: si scope_need=false => scopes_selected=[]
        if not scope_need:
            scopes_selected = []

        # Règle 2: si scope_need=true MAIS aucun scope valide => on désactive
        if scope_need and len(scopes_selected) == 0:
            scope_need = False

        # --- Business gates déterministes (mode smalltalk_intro + capabilities) ---
        gate_out = _apply_business_gates(
            llm_intent=str(intent),
            user_message=user_message,
            ctx=ctx or {},
            confidence=confidence,
        )

        intent_final = gate_out["intent_final"]
        mode = gate_out["mode"]
        gates = gate_out["gates"]

        # --- Guardrail scopes: jamais pendant smalltalk (intro/soft/amabilities) ---
        if mode in {"smalltalk_intro"} or intent_final in {"small_talk", "amabilities"}:
            scope_need = False
            scopes_selected = []

        # --- Discovery: scope obligatoire "value_proposition" ---
        if intent_final == "discovery":
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

        # --- Plan stable (on ignore le "plan" du LLM, trop risqué) ---
        plan = _build_plan_minimal(
            language=language or "fr",
            intent=intent_final,
            mode=mode,
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
            intent=intent_final,
            context_level=level,
            need_web=need_web,
            web_search_prompt=web_search_prompt if need_web else None,
            confidence=confidence,
            plan=plan,
            debug=debug,
        )