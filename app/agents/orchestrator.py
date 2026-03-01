# app/agents/orchestrator.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal

from app.llm.runtime import LLMRuntime
from app.core.llm_prompt_logger import log_llm_messages

from app.agents.node_registry import (
    NODE_TYPE_WHITELIST,
    render_nodes_whitelist_block,
    render_ids_rules_block,
)


IntentType = Literal[
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

StateType = Literal[
    "smalltalk_intro",
    "discovery",
    "discovery_pending",   # ✅ AJOUTER
    "onboarding",
    "ongoing_personal",
    "ongoing_pro",
]

ContextLevel = Literal["light", "medium", "max"]
MANDATORY_DISCOVERY_SCOPE = "discovery.value_proposition"
DOCS_SCOPES_MAX = 5



# NOTE: v1 — plan minimal : P1 parallel [context + quota] puis response_writer
@dataclass
class OrchestratorResult:
    ok: bool
    language: str
    state: StateType
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
- Assistante Personnelle: conseil, aide décision, accompagnement. N'exécute PAS d'actions (réservations, emails...).
- Ultimate Assistant (payant) : exécution actions concrètes (agenda, emails, réservations, finances).
- Modes Pro (payant, selon métier) : Assistante Médicale, Assistant Airbnb, etc.

═══════════════════════════════════════════════════════════════
STATE (SOURCE DE VÉRITÉ — DÉTERMINISTE)

Le backend fournit: ctx.runtime_state.state ∈
(smalltalk_intro, discovery, onboarding, ongoing_personal, ongoing_pro)

RÈGLE ABSOLUE:
- Tu ne choisis PAS le state.
- Tu choisis uniquement l'intent (liste ci-dessous) en tenant compte du state.
- En sortie, tu dois renvoyer:
- intent ∈ {{small_talk, amabilities, functional_question, general_question, decision_support,
             motivational_guidance, action_request, deep_work, professional_request,
             sensitive_question, urgent_request}}
  - context_level, need_web, scopes si nécessaire.

INTENTS & GRILLE DE SÉLECTION : 

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

📚 RÈGLE DOCS (OBLIGATOIRE)
- Si intent=functional_question :
  - scope_need = true (toujours)
  - scopes_selected = 1 à 5 scopes EXACTS (jamais 0), choisis uniquement dans la liste "DOCUMENTATION DISPONIBLE (SCOPES EXACTS)".
  - Objectif: charger les chunks les plus pertinents pour répondre précisément.
- Si tu ne trouves pas de scope pertinent dans la liste, tu mets:
  - scope_need = false
  - scopes_selected = []
  (mais c’est un cas exceptionnel)


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
→ Cible : état intérieur + clarté + énergie, pas “choisir entre A et B”.
→ level=max

✅ Déclencheurs explicites :
- “Je suis découragé”, “J’ai besoin de motivation”, “Pourquoi continuer ?”
- “J’en peux plus”, “Je suis vidé”, “Je suis perdu”, “J’ai plus envie”
- “Je sais pas pourquoi je fais ça”, “Je suis en vrac”, “Je doute de tout”

✅ Signaux faibles (IMPORTANT : souvent indirects) :
- baisse d’énergie (“fatigué”, “épuisé”, “ça me saoule”, “j’ai la flemme”, “je procrastine”)
- perte de sens (“à quoi bon”, “je tourne en rond”, “je stagne”, “ça sert à rien”)
- auto-pression / sur-contrôle (“il faut que…”, “je dois…”, “j’ai pas le droit de…”)
- rumination / confusion (“je sais pas”, “je suis bloqué”, “je suis perdu”, “je pars dans tous les sens”)
- tension émotionnelle (“je suis énervé”, “ça m’angoisse”, “j’ai la boule au ventre”)
- doute identitaire (“je suis pas fait pour ça”, “je suis nul”, “j’y arriverai pas”)

⚠️ Règle clé :
Si l’utilisateur exprime un état interne (fatigue, doute, perte de sens, stress) même sans demander “motivation”,
→ préférer motivational_guidance à decision_support.

⸻

action_request

→ Demande d’exécution d’une action concrète.
→ Signaux : “Réserve…”, “Rappelle-moi…”, “Envoie un email…”, “Planifie…”
→ level=medium

⸻

deep_work

→ Travail structuré et approfondi impliquant production, analyse longue ou livrable formel.
→ level=medium (ou max si lié aux projets/contraintes de l’utilisateur)

Déclencheurs typiques :
- analyse / synthèse d’un document (PDF, Word, Excel…)
- travail sur mémoire, thèse, dossier, business plan
- rédaction longue structurée (plan détaillé, stratégie complète)
- préparation d’examen ou coaching académique
- dev / code / debug / architecture technique
- projet nécessitant plusieurs étapes ou allers-retours

Règle clé :
Si la demande implique un livrable structuré, plusieurs itérations,
ou dépasse une réponse exploitable en quelques paragraphes,
→ choisir deep_work.

Ne PAS choisir deep_work si :
- simple question d’information (→ general_question)
- arbitrage entre options (→ decision_support)
- soutien émotionnel (→ motivational_guidance)

⸻

professional_request

→ Demande liée à un métier / cadre pro spécifique (dossier client/patient, cabinet, Airbnb ops).
→ Signaux : “Mon patient…”, “Dossier client…”, “Réservation Airbnb…”
→ level=max

⸻

sensitive_question

→ Santé, finance perso, juridique, info sensible.
→ Signaux : symptômes, impôts, juridique, situation médicale, etc.
→ level=max 

⸻

urgent_request

→ Situation critique impliquant un danger immédiat ou une détresse grave.
→ level=max

🚨 Déclencheurs explicites :
- Idées suicidaires ou auto-agressives (“je veux en finir”, “je ne veux plus vivre”, “je pense à me faire du mal”)
- Danger immédiat (“je vais faire une bêtise”, “je suis en danger”, “on me menace”)
- Symptômes médicaux graves en cours (perte de conscience, douleur thoracique intense, difficulté respiratoire aiguë)
- Panique incontrôlable avec perte de contrôle

⚠️ Important :
Le mot “urgent” seul ne suffit PAS.
Le stress, la pression professionnelle, l’anxiété légère, un délai court,
ne déclenchent PAS urgent_request.

Si l’urgence est psychologique légère ou liée à un choix,
→ utiliser motivational_guidance ou decision_support.

⸻

PRIORITÉ SI AMBIGUÏTÉ

sensitive_question > urgent_request > professional_request > decision_support >
action_request > functional_question > motivational_guidance > general_question >
small_talk > amabilities

DÉSAMBIGUÏSATION DECISION_SUPPORT vs MOTIVATIONAL_GUIDANCE

- decision_support = l’utilisateur veut choisir entre options (A/B), décider, trancher, comparer, arbitrer.
  Indices : “quelle option”, “je choisis quoi”, “dois-je”, “j’hésite entre”, “lequel est mieux”, “avantages/inconvénients”.

- motivational_guidance = l’utilisateur est en baisse d’énergie / sens / confiance, ou décrit une tension interne
  même s’il mentionne une décision.
  Indices : fatigue, découragement, anxiété, perte de sens, auto-pression, confusion, rumination.

Règle de tie-break :
Si un message contient à la fois (1) une décision et (2) un signal interne de fatigue/doute/stress,
→ choisir motivational_guidance (stabiliser d’abord), sauf si l’utilisateur demande explicitement “choisis pour moi entre A et B”.

DÉSAMBIGUÏSATION URGENT_REQUEST

- urgent_request = danger vital, crise psychologique grave, santé préoccupante immédiate.
- sensitive_question = question santé/finance/juridique sans danger immédiat.
- motivational_guidance = détresse émotionnelle non critique.
- decision_support = pression décisionnelle, même “urgente”.

Règle :
Si aucun danger immédiat ou risque vital n’est détecté,
→ ne PAS choisir urgent_request.

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

Cas particulier : sensitve_question
Quand intent = sensitive_question, tu DOIS te poser explicitement la question :
“Est-ce que ma réponse dépend d’une règle officielle, d’un taux, d’une procédure, d’une obligation légale/fiscale, d’une démarche administrative, ou d’un fait susceptible d’avoir changé récemment ?”

Si OUI → need_web = true, et web_search_prompt doit cibler des sources d’autorité.

Si NON → need_web = false (ex: organisation, méthode, hygiène financière générale, checklist non réglementaire).

🧱 Qualité attendue (obligatoire)
- Si need_web=true : web_search_prompt 3–4 lignes max, inclut pays + contexte + termes officiels.
- Sources prioritaires : gouvernement/administrations/organismes publics/textes officiels/ordres pro.
- Si tu ne trouves pas de sources fiables : tu n’inventes pas. Tu le dis et recommandes une voie sûre.

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

═══════════════════════════════════════════════════════════════
DOCS SCOPES POLICY (STRICT)

Tu peux demander des docs via :
- scope_need = true
- scopes_selected = [ ... ] (1 à 5 scopes)

Règles :
1) Tu n’inventes JAMAIS de scopes. Tu choisis uniquement les plus pertinents pour le contexte dans "DOCUMENTATION DISPONIBLE (SCOPES EXACTS)".
2) functional_question => scope_need = true OBLIGATOIRE et scopes_selected non vide (1..5), sauf si aucun scope pertinent n’existe.
3) discovery => scope_need = true (déjà géré côté code) mais tu peux aussi proposer d’autres scopes pertinents.
4) small_talk / amabilities => scope_need = false, scopes_selected = [].

═══════════════════════════════════════════════════════════════

🔒 PLAYBOOK DECISION MATRIX

Tu dois déterminer playbook_need et playbook_level selon les règles suivantes :
	1.	Si ctx.onboarding.status == “started”
→ playbook_need = true
→ playbook_level = “full”
	2.	Sinon si ctx.onboarding.pro_mode == true ET intent in [“professional_request”, “action_request”]
→ playbook_need = true
→ playbook_level = “light”
	3.	Sinon si ctx.onboarding.pro_mode == false ET intent == “action_request”
→ playbook_need = true
→ playbook_level = “light”
	4.	Si ctx.gates.smalltalk_intro_eligible == true
→ playbook_need = false
	5.	Sinon
→ playbook_need = false

Tu ne choisis jamais la clé du playbook.
La clé vient de ctx.onboarding.primary_agent_key.

═══════════════════════════════════════════════════════════════
ONBOARDING_PATCH (ÉCRITURE DB)

Tu peux proposer un onboarding_patch UNIQUEMENT si ctx.runtime_state.state == "onboarding".

Règles strictes :
- onboarding_patch.should_write = true seulement si le message user apporte une info exploitable.
- target doit être une string courte (ex: "personal", "business", "airbnb", "medical") ou null.
- level_max doit être "light" | "medium" | "max" ou null.
- metadata_patch = petit objet (max 10 clés). Pas de texte long. Pas de PII.
- Si tu n'es pas sûr => should_write=false (et tout le reste null/{{}}).

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

  "playbook_need": False,
  "playbook_level": None,

  "onboarding_patch": {
    "should_write": False,
    "target": None,
    "level_max": None,
    "metadata_patch": {}
  },

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

def _state_from_ctx(ctx: Optional[Dict[str, Any]]) -> str:
    try:
        s = ((ctx or {}).get("runtime_state") or {}).get("state")
        s = str(s or "").strip()
        return s
    except Exception:
        return ""

def _normalize_state(s: str) -> StateType:
    s = (s or "").strip()
    if s in {"smalltalk_intro", "discovery", "discovery_pending", "onboarding", "ongoing_personal", "ongoing_pro"}:
        return s  # type: ignore
    return "ongoing_personal"

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
    Orchestrator ne choisit PLUS de state.
    Il choisit uniquement intent + applique:
    - guardrails smalltalk_intro (ne pas "déraper" trop vite)
    - capabilities gating (action/deep_work/pro_request)
    """
    gate = _compute_smalltalk_intro_gate(ctx)
    caps = _compute_capabilities(ctx)

    eligible_intro = bool(gate["smalltalk_intro_eligible"])
    short_ack = _is_short_ack(user_message)

    intent = (llm_intent or "general_question").strip()

    # intents autorisés (safety net)
    allowed = {
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
    }
    if intent not in allowed:
        intent = "general_question"

    # Guardrail smalltalk_intro:
    # si intro éligible, on laisse passer uniquement:
    # - urgent/sensitive
    # - ou un intent "fort" si confiance haute ET message pas juste un ack
    hard_overrides = {"urgent_request", "sensitive_question"}
    strong_intents = {
        "functional_question",
        "general_question",
        "decision_support",
        "motivational_guidance",
        "professional_request",
        "action_request",
        "deep_work",
    }

    if eligible_intro:
        if intent in hard_overrides:
            intent_final = intent
        elif intent in strong_intents and confidence >= 0.85 and not short_ack:
            intent_final = intent
        else:
            # pendant l’intro, on absorbe vers small_talk (pas "smalltalk_intro"!)
            intent_final = "small_talk"
    else:
        intent_final = intent

    # Capabilities gating
    intent_eligible = True
    block_reason = None
    if intent_final in {"action_request", "deep_work", "professional_request"}:
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

    playbook_need: bool,
    playbook_level: Optional[str],
    primary_agent_key: Optional[str],

    # --- onboarding write (optionnel) ---
    should_insert_onboarding_node: bool,
    onboarding_target: Optional[str],
    onboarding_level_max: Optional[str],
    onboarding_metadata_patch: Dict[str, Any],
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

    if playbook_need and primary_agent_key:
        nodes.append(
            {
                "id": "P",
                "type": "tool.playbook_load",
                "depends_on": ["A"],
                "inputs": {
                    "agent_key": primary_agent_key,
                    "level": playbook_level or "light",
                },
            }
        )

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

    # --- Onboarding write ---
    # Node O : écrit target/level_max/metadata puis sync status started/complete
    if should_insert_onboarding_node:
        nodes.append(
            {
                "id": "O",
                "type": "tool.onboarding_set_fields",
                "depends_on": ["A"],
                "inputs": {
                    "target": onboarding_target,
                    "level_max": onboarding_level_max,
                    "metadata_patch": onboarding_metadata_patch or {},
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

    if should_insert_onboarding_node:
        deps.append("O")

    if playbook_need and primary_agent_key:
        deps.append("P")

    nodes.append(
        {
            "id": "D",
            "type": "agent.response_writer",
            "depends_on": deps,
            "inputs": {
                "state": state,
                "intent": intent,
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
            intent: IntentType = "general_question"
            level: ContextLevel = "medium"
            plan = _fallback_plan_minimal("fr")
            return OrchestratorResult(
                ok=False,
                language=language,
                state=_normalize_state(_state_from_ctx(ctx)),
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
                state=_normalize_state(_state_from_ctx(ctx)),
                intent="general_question",
                context_level="medium",
                need_web=False,
                web_search_prompt=None,
                confidence=0.0,
                plan=plan,
                debug={"error": "INVALID_JSON_FROM_LLM", "meta": meta, "raw_llm": raw_llm},
            )
        
        state = _normalize_state(_state_from_ctx(ctx))
        language = _language_from_ctx(ctx)
        primary_agent_key = None
        try:
            ob = (ctx or {}).get("onboarding") or {}
            if isinstance(ob, dict):
                primary_agent_key = ob.get("primary_agent_key")
                if isinstance(primary_agent_key, str):
                    primary_agent_key = primary_agent_key.strip() or None
        except Exception:
            primary_agent_key = None
        intent = data.get("intent") or "general_question"
        level = data.get("context_level") or "medium"
        confidence = float(data.get("confidence") or 0.0)

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

        raw_scopes = data.get("scopes_selected") or []
        scopes_selected: List[str] = []
        if isinstance(raw_scopes, list):
            for s in raw_scopes[:DOCS_SCOPES_MAX]:
                if isinstance(s, str) and s.strip():
                    scopes_selected.append(s.strip())

    
        # --- Onboarding patch (optionnel, proposé par le LLM) ---
        onboarding_patch = data.get("onboarding_patch") or {}
        if not isinstance(onboarding_patch, dict):
            onboarding_patch = {}

        op_should_write = bool(onboarding_patch.get("should_write") is True)

        op_target = onboarding_patch.get("target")
        op_level_max = onboarding_patch.get("level_max")
        op_metadata_patch = onboarding_patch.get("metadata_patch") or {}
        if not isinstance(op_metadata_patch, dict):
            op_metadata_patch = {}

        # nettoyage soft
        if isinstance(op_target, str):
            op_target = op_target.strip()
        else:
            op_target = None

        if isinstance(op_level_max, str):
            op_level_max = op_level_max.strip()
        else:
            op_level_max = None

        # règle hard: on write seulement en state=onboarding + should_write + au moins 1 champ exploitable
        should_insert_onboarding_node = (
            state == "onboarding"
            and op_should_write
            and bool(op_target or op_level_max or op_metadata_patch)
        )

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

        # matrice déterministe
        playbook_need = False
        playbook_level = None

        if ob_status == "started":
            playbook_need = True
            playbook_level = "full"
        elif (ob_pro_mode is True) and (intent_final in {"professional_request", "action_request"}):
            playbook_need = True
            playbook_level = "light"
        elif (ob_pro_mode is False) and (intent_final == "action_request"):
            playbook_need = True
            playbook_level = "light"

        # règle: si smalltalk intro, jamais de playbook
        if smalltalk_intro_eligible:
            playbook_need = False
            playbook_level = None
            
        mode = state
        gates = gate_out["gates"]

        # --- Guardrail scopes: jamais pendant smalltalk (intro/soft/amabilities) ---
        if state == "smalltalk_intro" or intent_final in {"small_talk", "amabilities"}:
            scope_need = False
            scopes_selected = []

        # --- Discovery: scope obligatoire "value_proposition" ---
        if state == "discovery":
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
            state=state,
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

            playbook_need=playbook_need,
            playbook_level=playbook_level,
            primary_agent_key=primary_agent_key,

            should_insert_onboarding_node=bool(should_insert_onboarding_node),
            onboarding_target=op_target,
            onboarding_level_max=op_level_max,
            onboarding_metadata_patch=op_metadata_patch,
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
        debug["onboarding_should_write"] = bool(should_insert_onboarding_node)
        debug["onboarding_patch_preview"] = {
            "target": op_target,
            "level_max": op_level_max,
            "metadata_patch_keys": list((op_metadata_patch or {}).keys())[:20],
        }
        debug["docs_scopes_count"] = int(((ctx or {}).get("docs") or {}).get("scopes_count") or 0)

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
            state=state,
            intent=intent_final,
            context_level=level,
            need_web=need_web,
            web_search_prompt=web_search_prompt if need_web else None,
            confidence=confidence,
            plan=plan,
            debug=debug,
        )