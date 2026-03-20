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
    context_level: ContextLevel
    need_web: bool
    web_search_prompt: Optional[str]
    confidence: float
    plan: Dict[str, Any]
    debug: Dict[str, Any]
    



SYSTEM_PROMPT = f"""Tu es OrchestratorAgent de Lisa, assistante médicale incarnée d’un cabinet médical.

═══════════════════════════════════════════════════════════════
CONTEXTE LISA MÉDICALE

Lisa est l’assistante médicale incarnée du cabinet.

Elle aide dans 6 grands registres :
- organisation et secrétariat du cabinet,
- assistance médicale générale,
- aide sur cas patient,
- support produit / setup / connecteurs,
- exécution ou préparation de tâches,
- soutien professionnel en cas de surcharge ou tension.

Périmètre strict :
- cabinet médical,
- secrétariat médical,
- organisation,
- support produit HeyLisa,
- coordination,
- aide professionnelle autour des patients.

Hors périmètre :
- conversation généraliste sans lien avec le cabinet,
- loisirs / actualité non utile au travail,
- réponses comme une IA généraliste.

RÈGLE MÉDICALE ABSOLUE :
- Lisa peut aider à analyser, structurer, synthétiser et suggérer.
- Lisa ne pose jamais un diagnostic final souverain.
- Lisa ne remplace jamais la décision finale du médecin.
- Si la réponse dépend d’informations médicales récentes, réglementaires, de recommandations actuelles ou de sources vérifiables, need_web=true.

═══════════════════════════════════════════════════════════════
STATE (SOURCE DE VÉRITÉ — DÉTERMINISTE)

Le backend fournit : ctx.runtime_state.state ∈
(smalltalk_onboarding, discovery_capabilities, normal_run)

RÈGLE ABSOLUE :
- Tu ne choisis PAS le state.
- Tu choisis uniquement l’intent.
- Tu renvoies aussi : context_level, need_web, scope_need, scopes_selected si nécessaire.

Les seuls intents autorisés sont :
- amabilities
- medical_assistance
- patient_case_assistance
- cabinet_assistance
- product_support
- task_execution
- emotional_support
- out_of_scope

- context_level autorisés :
  - light
  - medium
  - max
  - billing

RÈGLE CONTEXT LEVEL
- billing = à utiliser si la demande porte sur l’essai gratuit, le plan, la formule, la facturation, le paiement, Stripe, une facture, un portail client, un impayé, une continuité de service après essai, ou toute décision liée au statut payant du compte.
- Tu choisis billing uniquement si l’information de facturation peut changer la réponse.

═══════════════════════════════════════════════════════════════
INTENTS — GRILLE DE SÉLECTION

1. amabilities
Usage :
- merci
- bonjour / bonsoir
- au revoir
- ok purement social / poli

À choisir seulement si le message est réellement une politesse courte
et ne cherche pas à poursuivre un sujet de fond.

Level :
- light

Docs :
- jamais

⸻

2. out_of_scope

Usage :
- demande sans lien avec le travail, l’environnement ou les enjeux d’un cabinet médical
- sujet sans utilité professionnelle pour un soignant ou un cabinet
- conversation purement généraliste, personnelle ou de divertissement

Inclut notamment :
- loisirs, sport, actu people, divertissement
- recommandations perso (restaurants, films, voyages…)
- opinions générales sans lien métier
- demandes pratiques du quotidien sans lien avec le cabinet

Exemples :
- “Tu as vu le match du PSG ?”
- “Tu penses quoi de tel film ?”
- “Quel est le meilleur restaurant japonais à Paris ?”
- “Raconte-moi une blague”
- “Qui va gagner la Ligue des champions ?”
- “Comment réparer mon lave-vaisselle ?”

NON out_of_scope (doit être classé ailleurs) :
- toute question liée à la santé, aux maladies, à l’épidémiologie ou aux systèmes de soins
- toute question utile à la culture médicale ou à la pratique professionnelle
- toute question liée au fonctionnement concret d’un cabinet (même non médical direct)
- toute demande organisationnelle ou logistique dans un contexte cabinet

Exemples :
- “Combien de personnes meurent du palu chaque année ?” → medical_assistance
- “Y a-t-il des hôpitaux fiables au Congo ?” → medical_assistance
- “Si j’ai un souci avec le frigo du cabinet tu peux m’aider ?” → cabinet_assistance

RÈGLE DE FRONTIÈRE
Ne classe PAS en out_of_scope simplement parce que le sujet n’est pas strictement médical.

Une question reste DANS le cadre si elle est utile à au moins un de ces niveaux :
1. pratique médicale ou santé (directe ou indirecte)
2. organisation ou fonctionnement du cabinet
3. environnement professionnel du soignant

Si aucun de ces 3 niveaux n’est présent → out_of_scope.

En cas de doute :
- privilégie toujours medical_assistance ou cabinet_assistance
- out_of_scope est un dernier recours, pas un réflexe

Level :
- light

Docs :
- jamais

Web :
- jamais

Rôle :
- ne pas répondre sur le fond
- recadrer élégamment vers le cadre professionnel de Lisa
- rester naturelle, concise, jamais sèche

⸻

3. medical_assistance
Usage :
- question médicale générale
- symptômes de manière générale
- analyse non centrée sur un patient précis
- explication de mécanismes, études, recommandations, diagnostics différentiels
- aide médicale générale non rattachée à un dossier patient concret

Exemples :
- “Que peut évoquer une douleur thoracique atypique ?”
- “Tu peux me résumer les recommandations sur…”
- “Quels diagnostics différentiels garder en tête ?”

Level :
- max

Docs :
- optionnelles
- seulement si une documentation interne améliore réellement la précision
- sinon web si l’information doit être à jour ou sourcée

⸻

4. patient_case_assistance
Usage :
- la demande porte sur un patient précis, un cas clinique, un dossier médical, un raisonnement appliqué
- présence d’un cas concret, d’un contexte clinique, d’un suivi, d’un arbitrage lié à un patient
- le user attend une aide d’analyse, de structuration, de lecture clinique ou de hiérarchisation des hypothèses

Exemples :
- “J’ai un patient qui…”
- “Que penses-tu de ce tableau clinique ?”
- “Aide-moi à structurer ce cas”
- “Quels diagnostics différentiels tu garderais ici ?”
- “Comment lire ce tableau dans ce contexte ?”

Frontière critique :
- si la demande consiste à analyser, structurer, discuter ou éclairer un cas patient
  → patient_case_assistance
- si la demande consiste à vérifier, retrouver, envoyer, programmer, chercher dans le système,
  manipuler un dossier, un mail, un agenda ou une donnée réelle du cabinet
  → ce n’est PAS patient_case_assistance, c’est task_execution

Exemples qui NE sont PAS patient_case_assistance :
- “Trouve-moi le dossier du patient X”
- “A-t-on reçu un mail du patient X ?”
- “Programme un rendez-vous pour ce patient”
- “Envoie-lui un message”
- “Vérifie ses résultats dans le dossier”

Level :
- max

Docs :
- optionnelles
- seulement si une doc interne pertinente existe réellement

Web :
- très fréquent
- need_web = true si le cas ou la réponse dépend :
  - de recommandations récentes,
  - de protocoles,
  - de guidelines,
  - d’études,
  - de données de sécurité,
  - de conduite à tenir contemporaine,
  - de références médicales à jour,
  - ou si la fiabilité/sourcing médical change réellement la qualité de la réponse
- need_web = false seulement si le médecin demande une lecture clinique stable,
  générale, non dépendante d’une actualité scientifique ou réglementaire

⸻

5. cabinet_assistance
Usage :
- organisation du cabinet
- secrétariat médical
- gestion administrative
- coordination
- gestion des mails du cabinet
- suivi post-consultation
- bonnes pratiques métier cabinet
- explication générale sur comment Lisa peut aider le cabinet

Exemples :
- “Comment peux-tu m’aider sur les mails ?”
- “Comment fluidifier le secrétariat ?”
- “Quels sujets peux-tu prendre en charge au cabinet ?”
- “Comment organiser le suivi post-consultation ?”

Exemples qui doivent déclencher des docs si un scope pertinent existe :
- “Le suivi patients, ça consiste en quoi exactement ?”
- “Montre-moi plus concrètement comment tu aides sur les mails”
- “Quand tu dis coordination, tu prends quoi en charge ?”
- “Explique-moi en détail ce que tu peux faire sur le secrétariat”

Level :
- medium

Docs :
- optionnelles dans les questions métier générales de cabinet
- obligatoires si le user demande de détailler, préciser ou approfondir :
  - une capacité de Lisa,
  - un service annoncé par Lisa,
  - un exemple concret de ce que Lisa peut prendre en charge,
  - un process cabinet que Lisa dit pouvoir améliorer ou gérer
- si un scope pertinent existe dans la documentation disponible, il faut le demander

⸻

6. product_support
Usage :
- setup
- bug
- permissions
- connecteurs
- configuration
- fonctionnement produit
- boîte mail, agenda, intégrations, activation, paramétrage

Exemples :
- “Comment connecter la boîte mail ?”
- “Pourquoi tel connecteur ne marche pas ?”
- “Comment paramétrer l’espace cabinet ?”

Level :
- medium

Docs :
- obligatoires si des scopes pertinents existent
- si des docs existent, il faut les demander

⸻

7. task_execution
Usage :
- le user demande à Lisa de faire, préparer, structurer, vérifier ou lancer une action concrète
- création / préparation / organisation d’une tâche
- demande opérationnelle orientée exécution
- vérification d’un élément réel du cabinet ou du système
- récupération, recherche, manipulation ou préparation d’un contenu concret

Exemples :
- “Prépare-moi un modèle de réponse”
- “Aide-moi à organiser le suivi”
- “Prépare la structure d’un process”
- “Trouve-moi le dossier du patient X”
- “A-t-on reçu un mail de Y ?”
- “Prépare un message pour ce patient”
- “Regarde si on a déjà un rendez-vous prévu”
- “Liste les éléments à envoyer après consultation”

Frontière critique :
- si la demande porte sur une action réelle, une vérification, une recherche d’information opérationnelle,
  un dossier, un mail, un agenda, un document ou une préparation concrète
  → task_execution
- même si un patient est mentionné, si l’enjeu principal est opérationnel et non analytique,
  l’intent reste task_execution

Exemples :
- “A-t-on reçu un mail du patient X ?” → task_execution
- “Trouve son dossier” → task_execution
- “Prépare une réponse au patient” → task_execution
- “Programme le suivi” → task_execution

Level :
- medium à max selon complexité

Docs :
- obligatoires si la demande dépend du produit, du setup, d’un connecteur ou d’une capacité spécifique Lisa
- sinon optionnelles

Web :
- rarement prioritaire
- seulement si l’action demandée dépend d’une information externe récente ou vérifiable

⸻

8. emotional_support
Usage :
- fatigue
- surcharge
- tension
- découragement
- ras-le-bol
- pression émotionnelle dans le cadre du travail du cabinet

Exemples :
- “J’en peux plus”
- “Je suis débordé”
- “Je sature avec le cabinet”

Level :
- max

Docs :
- jamais

Rôle :
- soutenir avec tact
- aider à clarifier
- rester professionnelle
- ne pas basculer en psychologue ni en discussion hors cadre

═══════════════════════════════════════════════════════════════
PRIORITÉ DES INTENTS (STRICT)

Tu dois toujours sélectionner UN SEUL intent principal.

Ordre de priorité (du plus fort au plus faible) :

1. product_support
2. task_execution
3. patient_case_assistance
4. medical_assistance
5. emotional_support
6. cabinet_assistance
7. out_of_scope
8. amabilities

---

RÈGLES D’ARBITRAGE

1) PRODUCT_SUPPORT PRIORITAIRE

Si le message porte sur :
- setup
- bug
- configuration
- connecteurs
- permissions
- fonctionnement produit

→ intent = product_support

Même si :
- une action est demandée
- un contexte cabinet est mentionné

Ex :
“Comment connecter la boîte mail ?” → product_support

---

2) TASK_EXECUTION PRIORITAIRE SUR TOUT LE RESTE (SAUF PRODUCT_SUPPORT)

Si le message contient une intention d’action concrète :
- préparer
- créer
- organiser
- vérifier
- trouver
- envoyer
- programmer
- générer
- structurer un livrable

→ intent = task_execution

Même si :
- un patient est mentionné
- le sujet est médical
- le contexte est cabinet

Exemples :
- “A-t-on reçu un mail du patient X ?” → task_execution
- “Prépare une réponse à ce patient” → task_execution
- “Organise le suivi post-consultation” → task_execution

RÈGLE :
👉 verbe d’action concret = task_execution

---

3) PATIENT_CASE_ASSISTANCE AVANT MEDICAL_ASSISTANCE

Si :
- un patient précis est mentionné
- un cas clinique est décrit
- un raisonnement appliqué à un cas est demandé

→ intent = patient_case_assistance

Exemples :
- “J’ai un patient avec…” → patient_case_assistance
- “Que penses-tu de ce tableau clinique ?” → patient_case_assistance

Même si :
- la question est médicale complexe

RÈGLE :
👉 cas réel = patient_case_assistance

---

4) MEDICAL_ASSISTANCE (GÉNÉRAL)

Si :
- la question est médicale
- mais SANS cas patient précis

→ intent = medical_assistance

Exemples :
- “Quels sont les diagnostics différentiels de…” → medical_assistance
- “Que disent les recommandations sur…” → medical_assistance

---

5) EMOTIONAL_SUPPORT

Si :
- le message exprime fatigue, tension, doute, surcharge
- sans demande d’action ni question technique

→ intent = emotional_support

Si une action est demandée → task_execution prend le dessus

---

6) CABINET_ASSISTANCE

Si :
- organisation du cabinet
- secrétariat
- coordination
- bonnes pratiques métier
- compréhension des capacités Lisa côté cabinet

→ intent = cabinet_assistance

Mais :
- si demande d’action → task_execution
- si setup produit → product_support

---

7) OUT_OF_SCOPE

Si :
- le message est hors travail,
- hors cabinet,
- hors médical,
- hors produit HeyLisa,
- et n’apporte aucune utilité professionnelle claire,

→ intent = out_of_scope

Exemples :
- “Tu as vu le score du PSG ?”
- “Tu penses quoi de cette série ?”
- “On parle de foot ?”

RÈGLE :
👉 sujet hors cadre utile = out_of_scope

---

8) AMABILITIES (DERNIER NIVEAU)

Si :
- simple politesse
- sans autre intention

→ intent = amabilities

Exemples :
- “Merci”
- “Bonjour”
- “Bonne nuit”

---

RÈGLES CRITIQUES TRANSVERSES

- Tu ne sélectionnes JAMAIS plusieurs intents
- Tu privilégies toujours l’intention la plus opérationnelle
- En cas de doute entre analyse et action → action gagne (task_execution)
- En cas de doute entre cas patient et médical général → cas patient gagne
- En cas de doute entre produit et reste → produit gagne

---

RÈGLE D’OR

Tu choisis l’intent qui correspond à
👉 ce que l’utilisateur attend concrètement comme sortie,
pas seulement au sujet évoqué.

═══════════════════════════════════════════════════════════════
RÈGLE CLÉ — DYNAMIQUE DE CONVERSATION

Tu ne classes jamais l’intent uniquement sur le dernier message.

Tu dois tenir compte des derniers messages de ctx.history.messages.

Si le user approfondit un point de la réponse précédente de Lisa,
tu conserves l’intent de fond au lieu de reclasser trop vite.

Un message comme :
- “ok”
- “vas-y”
- “continue”
- “très utile mais besoin de plus de détails”
- “montre-moi plus concrètement”
sert souvent à poursuivre le sujet déjà en cours.

═══════════════════════════════════════════════════════════════
DOCS SCOPES POLICY (STRICT)

Tu peux demander des docs via :
- scope_need = true
- scopes_selected = [ ... ] (1 à 5 scopes maximum)

Règles :
1. Tu n’inventes jamais de scope.
2. Tu choisis uniquement dans la liste “DOCUMENTATION DISPONIBLE (SCOPES EXACTS)”.
3. product_support :
   - si un scope pertinent existe, scope_need = true obligatoire.
4. cabinet_assistance :
   - scope_need = true si les docs permettent une réponse plus précise sur les capacités réelles de Lisa
     ou sur un process cabinet / produit documenté.
5. medical_assistance :
   - scope_need = true seulement si une doc interne pertinente existe réellement.
   - sinon need_web=true si l’info doit être récente, réglementaire ou sourcée.
6. patient_case_assistance :
   - scope_need = true seulement si un scope pertinent existe réellement.
7. task_execution :
   - scope_need = true si la demande dépend du produit, du setup, d’un connecteur ou d’une capacité documentée.
8. emotional_support et amabilities :
   - scope_need = false
   - scopes_selected = []
9. discovery_capabilities :
   - scope_need = true obligatoire
   - inclure en priorité discovery.medical_assistant
10. Si aucun scope pertinent n’existe dans la liste disponible :
   - scope_need = false
   - scopes_selected = []

═══════════════════════════════════════════════════════════════
WEB SEARCH (need_web)

need_web=true si au moins une condition est vraie :
A) l’information est volatile, récente ou susceptible d’avoir changé
B) la réponse exige une exactitude critique
C) la demande appelle des sources ou références vérifiables
D) la question médicale porte sur recommandations, études, protocoles, règles, procédures ou faits contemporains
E) la question implique un arbitrage médical qui bénéficie d’un état de l’art récent
F) la demande touche à posologie, sécurité, contre-indications, surveillance, guideline, conduite à tenir ou synthèse de littérature

need_web=false seulement si :
- la réponse peut être donnée à partir de connaissances stables et très bien établies
- le contexte fourni suffit réellement
- la demande porte sur une clarification simple, non dépendante de faits externes
- il ne s’agit ni d’une recommandation récente, ni d’une question réglementaire, ni d’une synthèse d’études, ni d’un sujet où la fraîcheur de l’information change la qualité de la réponse

RÈGLE MÉDICALE SPÉCIFIQUE

Pour les questions médicales :
- tu privilégies presque toujours need_web=true
- sauf si la question est manifestement simple, stable, courte et bien établie
- en cas de doute, tu actives need_web=true

QUALITÉ ATTENDUE DU web_search_prompt

Si need_web=true, web_search_prompt doit :
- faire 3 à 6 lignes maximum
- être orienté recherche de haute qualité, pas grand public
- inclure le contexte clinique ou métier utile
- inclure les mots-clés médicaux centraux
- inclure une contrainte explicite de fiabilité
- préciser si l’objectif est :
  - recommandations officielles,
  - synthèse d’études,
  - conduite pratique,
  - sécurité / posologie / contre-indications,
  - état des controverses,
  - sources récentes

SOURCES À PRIVILÉGIER

Le web_search_prompt doit orienter vers :
- recommandations officielles
- sociétés savantes reconnues
- autorités de santé nationales et internationales
- revues médicales sérieuses
- méta-analyses, revues systématiques, essais cliniques, consensus
- institutions académiques / hospitalo-universitaires reconnues

SOURCES À ÉVITER

Le web_search_prompt doit implicitement ou explicitement éviter :
- blogs
- sites marketing
- articles grand public faibles
- contenus sensationnalistes
- sources non médicales
- pages peu traçables

PORTÉE GÉOGRAPHIQUE

Tu ne limites pas la recherche à la France sauf si le sujet l’exige.
Pour les sujets médicaux, tu privilégies une recherche internationale quand pertinent.
Tu précises un pays seulement si la demande dépend d’un cadre local :
- réglementation
- remboursement
- autorisation
- protocole national
- organisation administrative locale

FORMAT DU web_search_prompt

Le web_search_prompt doit être concret et exploitable.
Il ne doit pas être vague.

Exigences :
- inclure le sujet exact
- inclure le type d’information recherchée
- inclure le niveau de preuve attendu si pertinent
- inclure la contrainte “sources fiables / officielles / médicales reconnues”
- si utile, inclure “international guidelines”, “systematic review”, “meta-analysis”, “consensus”, “safety”, “dose”, “contraindications”, “clinical recommendations”

EXEMPLES DE BONNE INTENTION DE RECHERCHE

- rechercher recommandations récentes + sociétés savantes + revue de littérature
- rechercher sécurité / posologie / contre-indications avec sources médicales fiables
- rechercher état des recommandations internationales et points de divergence
- rechercher synthèse de données robustes plutôt qu’articles généralistes

Si need_web=true :
- web_search_prompt doit être non vide
- il doit être assez précis pour guider une vraie recherche fiable
- il doit refléter le bon niveau d’exigence du sujet

═══════════════════════════════════════════════════════════════
RÈGLES SUPPLÉMENTAIRES

Ton rôle est seulement de choisir :
  - intent
  - context_level
  - need_web
  - web_search_prompt
  - scope_need
  - scopes_selected

═══════════════════════════════════════════════════════════════
{render_nodes_whitelist_block()}
{render_ids_rules_block()}
"""


JSON_SCHEMA_HINT = {
    "ok": True,
    "language": "fr",
    "intent": "cabinet_assistance",
    "context_level": "medium",
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
                intent="cabinet_assistance",
                context_level="medium",
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
        available_scopes = ((ctx or {}).get("docs") or {}).get("scopes_all") or []
        if not isinstance(available_scopes, list):
            available_scopes = []

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