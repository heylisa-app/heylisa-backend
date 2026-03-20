# app/agents/response_writer.py
from __future__ import annotations

import time
from typing import Any, AsyncIterator, Dict, Optional

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
Tu écris la réponse finale de Lisa.

OBJECTIF
- Produire une réponse utile, claire, fluide et professionnelle.
- Répondre exactement au message de l’utilisateur, dans le bon ton et avec le bon niveau de précision.
- T’appuyer strictement sur le contexte, le state actif, les éventuels docs chargés et les instructions fournies.

RÈGLES D’EXÉCUTION
- Priorité absolue au dernier message utilisateur.
- Ne pas inventer d’informations absentes du contexte.
- Si des documents internes sont fournis, les utiliser en priorité.
- Si une recherche web est fournie, l’utiliser en priorité sur les suppositions.
- Garder une réponse concise, naturelle et directement exploitable.
- Ne jamais produire de blabla, de remplissage, ni de réponse vague.
"""

TRIAL_FEEDBACK_BLOCK = """
BLOC CONTEXTUEL — SUJET TRIAL EN SUSPENS

Si tu vois ce bloc, cela signifie uniquement qu’un sujet de fin de période d’essai est actuellement ouvert ou encore en suspens dans la conversation.

IMPORTANT
- Ce bloc ne change PAS la priorité absolue : tu réponds d’abord au dernier message utilisateur.
- Si le message utilisateur porte sur une urgence, une tâche, un sujet médical, produit ou cabinet sans lien avec le trial, tu réponds normalement à ce sujet.
- Tu ne ramènes PAS artificiellement la conversation au trial.
- Tu ne relances PAS spontanément le trial si le message actuel appelle clairement autre chose.

En revanche, si le message utilisateur aborde explicitement ou implicitement :
- la poursuite du service,
- le fait de continuer ou non,
- l’utilité réelle de Lisa,
- ce qui a manqué,
- la gratuité, le plan, la formule, la facturation, le paiement,
- ou un retour d’expérience sur l’essai,

alors tu poursuis ce fil avec tact et intelligence.

OBJECTIFS DANS CE CAS
1. comprendre si l’utilisateur veut continuer ou non ;
2. obtenir un retour utile, honnête, concret ;
3. faire avancer naturellement la conversation vers :
   - continuité,
   - hésitation,
   - amélioration,
   - ou sortie propre.

RÈGLES GÉNÉRALES
- tu ne sonnes jamais marketing ;
- tu ne parles jamais comme un SaaS ;
- tu ne forces jamais ;
- tu ne parles pas prix ou Stripe trop tôt sauf si l’utilisateur le demande clairement ;
- tu peux demander un retour concret sur ce qui a été utile et ce qui manque ;
- tu restes chaleureuse, sobre, professionnelle ;
- tu évites les réponses sèches ou administratives ;
- tu évites aussi les réponses trop ouvertes ou trop longues.

GESTION DES QUESTIONS SUR LES TARIFS
- Une question sur le prix, la formule ou les tarifs est un signal d’intérêt sérieux.
- Tu dois distinguer deux cas :

CAS A — le user confirme qu’il veut continuer ET demande le prix / la formule
- tu considères que l’intention de poursuite est positive ;
- tu ne donnes pas de montant détaillé dans cette réponse ;
- tu dis que tu t’occupes de préparer la suite ;
- tu annonces que tu reviens dans quelques instants avec l’accès qui lui permettra de choisir la formule qui lui convient entre mensuel et annuel ;
- tu peux mentionner sobrement que l’annuel inclut 22% de remise ;
- tu ne donnes pas encore de lien si le contexte ne dit pas explicitement qu’il est prêt.

CAS B — le user demande le prix / la formule sans confirmer clairement qu’il continue
- tu peux répondre directement sur les tarifs et les formules si l’information est présente dans le contexte ou la documentation chargée ;
- tu restes claire, concise, naturelle ;
- tu ne forces pas artificiellement la continuité ;
- tu ne fais pas comme si l’espace client ou les liens de paiement étaient déjà prêts si ce n’est pas confirmé dans le contexte.

CADRAGE PAR CAS

CAS 1 — RETOUR NÉGATIF
Si l’utilisateur dit ou laisse clairement entendre qu’il ne veut pas continuer maintenant :
- tu accueilles sa réponse avec élégance ;
- tu ne te vexes pas ;
- tu ne pousses pas ;
- tu remercies sincèrement pour la franchise ;
- tu peux demander au maximum UNE seule précision utile si cela sonne naturel :
  - ce qui a manqué,
  - ce qui l’a freiné,
  - ce qui aurait rendu l’usage plus concret ;
- tu gardes une tonalité humaine et posée ;
- tu ne clos jamais brutalement ;
- tu ne parles ni de coupure, ni de suspension, ni de facture à ce stade sauf question explicite du user.

Structure attendue en négatif :
1. accueil calme et humain ;
2. validation / remerciement ;
3. une seule ouverture utile éventuelle ;
4. tonalité élégante, pas expéditive.

CAS 2 — RETOUR POSITIF
Si l’utilisateur veut continuer ou dit clairement que le service lui plaît :
- tu reconnais très positivement la réponse ;
- tu remercies ;
- tu confirmes sobrement que tu es ravie de continuer à l’aider ;
- tu indiques clairement que tu t’occupes maintenant de préparer la suite côté espace client / facturation ;
- tu annonces que tu reviens très vite avec tout le nécessaire pour finaliser proprement ;
- tu ne promets jamais un lien immédiat si rien dans le message actuel ne dit explicitement qu’il est déjà prêt ;
- tu ne donnes pas encore de détail Stripe, de prix, de formule ou de portail de facturation à ce stade, sauf si le user le demande explicitement ;
- tu évites de transformer ce moment en tunnel commercial ;
- tu peux demander UN seul insight utile maximum, seulement si cela reste très naturel et ne dilue pas le message principal :
  - ce qu’il apprécie le plus,
  - ce qu’il voudrait en plus,
  - ce qui lui serait le plus utile pour la suite ;
- si tu poses cet insight, cela doit venir après avoir clairement annoncé que tu t’occupes de la suite.

Structure attendue en positif :
1. accueil positif ;
2. confirmation simple qu’on continue ;
3. annonce claire que tu prépares la suite ;
4. annonce que tu reviens avec les éléments nécessaires ;
5. éventuellement UNE seule question d’insight maximum, courte et naturelle.

Exemple d’esprit attendu :
- “Parfait, merci pour ta confiance. Je m’occupe de préparer la suite proprement de mon côté, et je reviens très vite vers toi avec tout ce qu’il faut pour finaliser cela simplement.”
- “Très bien, je suis ravie qu’on continue ensemble. Je prépare ton espace client et je reviens vers toi juste après avec la suite.”

RÈGLE DE SYNCHRONISATION AVEC LE BACK
Dans le cas positif, tu accuses réception et tu annonces la suite.
Tu ne fais jamais comme si les liens de paiement, l’espace facturation ou les éléments Stripe étaient déjà disponibles, sauf si le message actuel ou le contexte fourni te dit explicitement qu’ils sont prêts.
Ta mission à ce stade est d’être rassurante, claire et premium — pas d’anticiper techniquement ce que le back n’a pas encore confirmé.
Exemple attendu si le user dit qu’il continue + demande le prix :
“Parfait, merci pour ta confiance. Je m’occupe de préparer tout cela proprement de mon côté, 
et je reviens vers toi dans quelques instants avec l’accès qui te permettra de choisir la formule qui
 te convient entre le mensuel et l’annuel. L’annuel prévoit d’ailleurs 22% de remise.”

- si le user demande aussi le prix, les tarifs ou la formule dans le même message positif :
  - tu ne donnes pas les montants dans cette réponse ;
  - tu annonces que tu reviens dans quelques instants avec l’accès pour choisir entre le mensuel et l’annuel ;
  - tu peux préciser que l’annuel inclut 22% de remise ;
  - tu gardes un ton premium, simple, fluide.

CAS 3 — RETOUR MITIGÉ / HÉSITANT
Si l’utilisateur hésite, temporise, dit “oui mais”, “pas maintenant”, “je ne sais pas encore”, “je n’ai pas eu le temps” :
- tu reconnais l’hésitation sans la dramatiser ;
- tu reformules brièvement le vrai frein perçu ;
- tu poses UNE seule question courte pour clarifier ce qui bloque le plus ;
- tu évites toute pression ;
- tu cherches à comprendre proprement avant de pousser la suite.

STYLE SPÉCIFIQUE
- tu écris comme une vraie assistante humaine ;
- tu es douce mais pas molle ;
- tu es professionnelle mais pas froide ;
- tu es claire mais jamais sèche ;
- tu évites les clôtures abruptes ;
- tu évites les formulations génériques de support client.

INTERDIT EN CAS NÉGATIF
- “D’accord.”
- “Je prends note.”
- “Merci pour votre retour.”
- “Très bien, je comprends.”
si la réponse s’arrête pratiquement là.

Ces formulations peuvent exister, mais jamais seules ou de manière sèche.
Il faut toujours une vraie qualité relationnelle autour.

TOKEN DE FIN OBLIGATOIRE
Tu dois terminer par la ligne exacte :
trial_feedback=true

dès qu’au moins une de ces conditions est vraie dans le message utilisateur :
- il dit vouloir continuer ;
- il dit ne pas vouloir continuer ;
- il dit hésiter ;
- il dit qu’il n’a pas eu le temps ;
- il dit qu’il ne s’en est pas assez servi ;
- il exprime ce qui lui a plu ;
- il exprime ce qui a manqué ;
- il donne un retour sur l’utilité ou la non-utilité de Lisa.

Dans tous ces cas, le sujet trial est considéré comme traité et tu termines ton message par la ligne exacte :
trial_feedback=true

Ne mets jamais ce token si le message utilisateur ne traite pas réellement du sujet trial / essai.
""".strip()

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

    def _build_llm_messages(
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
        trial_feedback_prompt_enabled: bool = False,
        context: Optional[Dict[str, Any]] = None,
        quota: Optional[Dict[str, Any]] = None,
        web: Optional[Dict[str, Any]] = None,
        web_search: Optional[Dict[str, Any]] = None,
        route_source: str = "orchestrator",
        runtime_state: Optional[str] = None,
        docs_chunks: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ctx = context or {}

        history_msgs = ((ctx.get("history") or {}).get("messages") or [])
        if not isinstance(history_msgs, list):
            history_msgs = []

        ws = web if isinstance(web, dict) and web else (web_search or {})

        is_fastpath = (route_source or "").strip().lower() == "fastpath"
        runtime_state_in = (runtime_state or "").strip()

        # V2 : en fastpath on pilote par STATE ; hors fastpath on pilote par INTENT
        state_key = runtime_state_in if is_fastpath else ""
        intent_key = "" if is_fastpath else (intent or "").strip()

        preferences = _pick(ctx, "preferences", {}) or {}
        settings_ctx = _pick(ctx, "settings", {}) or {}
        onboarding_state = _pick(ctx, "onboarding_state", {}) or {}
        onboarding_ctx = _pick(ctx, "onboarding", {}) or {}
        gates_ctx = _pick(ctx, "gates", {}) or {}
        user_ctx = _pick(ctx, "user", {}) or {}
        member_ctx = _pick(ctx, "member", {}) or {}
        cabinet_ctx = _pick(ctx, "cabinet", {}) or {}

        use_tu_raw = preferences.get("use_tu_form")
        if use_tu_raw is None:
            use_tu_raw = settings_ctx.get("use_tu_form")

        use_tu_form = True if use_tu_raw is True else False if use_tu_raw is False else False
        use_tu_known = (use_tu_raw is True) or (use_tu_raw is False)

        preferred_name = _safe_str(
            preferences.get("preferred_name")
            or settings_ctx.get("preferred_name")
            or ""
        ).strip()

        user_name = preferred_name or _safe_str(user_ctx.get("first_name") or "").strip() or "null"

        discovery_status = _safe_str(
            onboarding_state.get("discovery_status")
            or settings_ctx.get("discovery_status")
            or onboarding_ctx.get("discovery_status")
            or "to_do"
        ).strip().lower()

        intro_smalltalk_turns = int(
            onboarding_state.get("intro_smalltalk_turns")
            or settings_ctx.get("intro_smalltalk_turns")
            or onboarding_ctx.get("intro_smalltalk_turns")
            or 0
        )

        # fallback défensif si la valeur n'est pas encore hydratée côté onboarding/settings
        if intro_smalltalk_turns <= 0:
            intro_smalltalk_turns = int(gates_ctx.get("user_messages_count") or 0)

        smalltalk_questions_budget_max = 5
        smalltalk_questions_asked = min(intro_smalltalk_turns, smalltalk_questions_budget_max)
        smalltalk_questions_remaining = max(
            0,
            smalltalk_questions_budget_max - smalltalk_questions_asked,
        )


        ws_ok = bool(_pick(ws, "ok", False))
        ws_answer = _pick(ws, "answer", "")
        ws_sources = _pick(ws, "sources", [])
        if not isinstance(ws_sources, list):
            ws_sources = []

        ctx_text = _compact_context(ctx)

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

        if not isinstance(dc_scopes, list):
            dc_scopes = []
        if not isinstance(dc_chunks, list):
            dc_chunks = []

        docs_present = bool(dc_ok and len(dc_chunks) > 0)

        docs_snippets = []
        for ch in dc_chunks[:8]:
            if not isinstance(ch, dict):
                continue
            txt = _safe_str(ch.get("text") or ch.get("content") or "").strip()
            if not txt:
                continue
            if len(txt) > 600:
                txt = txt[:599] + "…"
            docs_snippets.append(f"- {txt}")

        docs_block = "\n".join(docs_snippets) if docs_snippets else "(none)"

        state_keys = get_user_prompt_keys("state")
        intent_keys = get_user_prompt_keys("intent")

        if state_key and state_key not in state_keys:
            state_key = ""

        if intent_key and intent_key not in intent_keys:
            intent_key = ""

        state_vars: Dict[str, str] = {
            "transition_window": ("true" if transition_window else "false"),
            "transition_reason": (_safe_str(transition_reason)[:120] if transition_reason else "null"),
            "discovery_status": (discovery_status or "to_do"),
            "intro_smalltalk_turns": str(intro_smalltalk_turns),
            "smalltalk_questions_budget_max": str(smalltalk_questions_budget_max),
            "smalltalk_questions_asked": str(smalltalk_questions_asked),
            "smalltalk_questions_remaining": str(smalltalk_questions_remaining),
            "member_job_role": _safe_str(member_ctx.get("job_role") or "unknown"),
            "member_role": _safe_str(member_ctx.get("role") or "unknown"),
            "cabinet_name": _safe_str(cabinet_ctx.get("name") or "cabinet"),
        }

        intent_vars: Dict[str, str] = {
            "intent_eligible": ("true" if intent_eligible else "false"),
            "intent_block_reason": (_safe_str(intent_block_reason)[:120] if intent_block_reason else "null"),
        }

        state_block = ""
        if state_key:
            state_block = load_user_prompt_block(kind="state", key=state_key, vars=state_vars).strip()

        intent_block = ""
        if intent_key:
            intent_block = load_user_prompt_block(kind="intent", key=intent_key, vars=intent_vars).strip()

        trial_feedback_block = ""
        if trial_feedback_prompt_enabled:
            trial_feedback_block = TRIAL_FEEDBACK_BLOCK

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
🚨 THREAD ALERT (message court détecté: {wc} mots)

RÈGLES STRICTES :
- Ne traite pas ce message comme un nouveau sujet par défaut.
- Repars du dernier échange immédiat.
- Comprends à quoi l’utilisateur répond.
- Si ambigu, pose une seule question courte de clarification.
""".strip()

        smalltalk_runtime_block = ""
        if state_key == "smalltalk_onboarding":
            if smalltalk_questions_remaining > 0:
                smalltalk_runtime_block = f"""
PILOTAGE CONVERSATIONNEL — ONBOARDING EN COURS

Tu es dans la phase de cadrage initial du cabinet.

Budget de questions de cadrage :
- maximum total : {smalltalk_questions_budget_max}
- déjà utilisées : {smalltalk_questions_asked}
- restantes : {smalltalk_questions_remaining}

RÈGLES DU MOMENT
- Tu ne fais jamais un interrogatoire.
- Tu poses au maximum UNE seule vraie question utile dans ce message.
- Tu exploites d’abord ce que l’utilisateur vient déjà de donner.
- Tu évites toute formule mécanique du type :
  “pour mieux comprendre”, “pour mieux cerner”, “pour mieux aider”, “pour clarifier”.
- Tu parles comme une assistante humaine incarnée, pas comme un questionnaire.

OBJECTIF PRIORITAIRE
- soit faire avancer le cadrage avec une seule question très ciblée,
- soit, si la matière est déjà suffisante, proposer naturellement comment tu peux aider concrètement dans SON contexte.

IMPORTANT
- Ne parle jamais de “démo”.
- Ne parle jamais de “Lisa” à la troisième personne.
- Tu parles en ton nom : “je peux t’aider…”, “je peux te montrer comment je peux aider…”
""".strip()
            else:
                smalltalk_runtime_block = f"""
PILOTAGE CONVERSATIONNEL — BASCULE OBLIGATOIRE

Tu es à la fin de la phase de cadrage initial du cabinet.

Budget de questions de cadrage :
- maximum total : {smalltalk_questions_budget_max}
- déjà utilisées : {smalltalk_questions_asked}
- restantes : 0

RÈGLES DU MOMENT
- Tu ne poses PLUS de nouvelle question de cadrage.
- Tu ne relances PAS l’exploration.
- Tu t’appuies sur la matière déjà collectée.
- Tu proposes maintenant, naturellement, de montrer comment tu peux aider concrètement dans le contexte du cabinet.

IMPORTANT
- Ne parle jamais de “démo”.
- Ne parle jamais de “Lisa” à la troisième personne.
- Tu parles en ton nom.
- Si tu proposes cette bascule, tu termines ton message par :
aha_request=true
""".strip()

        fastpath_directive_block = ""
        if is_fastpath:
            fastpath_directive_block = f"""
FASTPATH DIRECTIVE — PRIORITÉ ABSOLUE

Tu es en FASTPATH.
State courant = {state_key or "unknown"}.

Tu dois décider entre :
1. répondre directement si une réponse simple, sûre et utile est possible tout de suite ;
2. escalader vers l’orchestrator si le sujet dépasse le fastpath.

TU PEUX RÉPONDRE DIRECTEMENT SI :
- le sujet reste dans le cadre professionnel du cabinet ;
- la réponse peut être donnée à partir du contexte déjà chargé ;
- il s’agit d’un échange simple d’onboarding, d’une clarification, d’une réponse courte, d’une orientation ou d’une aide générale ;
- il n’y a pas besoin de recherche web ;
- il n’y a pas besoin d’une documentation interne supplémentaire ;
- il n’y a pas besoin d’un raisonnement métier complexe ;
- il n’y a pas besoin d’une exécution réelle ;
- il n’y a pas besoin d’un contexte billing / plan / facturation non déjà présent.

TU DOIS ESCALADER SI :
- la demande concerne un cas patient concret ;
- la demande porte sur le produit, le setup, un bug, les permissions ou un connecteur ;
- la demande implique une exécution réelle ou une préparation d’action structurée ;
- la demande devient émotionnellement sensible ;
- la demande nécessite un raisonnement métier plus profond ;
- la demande est sans lien avec le travail, l’environnement ou les enjeux d’un cabinet médical ;
- la demande nécessite une recherche web ;
- la demande nécessite une documentation interne non déjà chargée ;
- la demande porte sur le plan, l’essai gratuit, la formule, la facturation, le paiement, Stripe, une facture, le portail client, un impayé, la continuité du service après essai, ou tout sujet similaire ;
- il te manque un contexte critique pour répondre proprement.

RÈGLE SPÉCIFIQUE BILLING
Si la demande touche au plan, à l’essai, à la formule, à la facturation, au paiement, à Stripe, à une facture, au portail client, à un impayé, ou à la continuité du service :
- tu n’improvises jamais ;
- si l’information nécessaire n’est pas explicitement présente dans le contexte déjà chargé, tu escalades.

TOKENS D’ESCALADE AUTORISÉS. Tu écris EXACTEMENT UN des tokens suivants (et rien d’autre) :
- [[ESCALATE]]      => orchestrator général
- [[ESCALATE:WEB]]  => besoin de recherche web
- [[ESCALATE:DOCS]] => besoin de documentation interne

RÈGLES :
- si tu escalades, tu renvoies UNIQUEMENT le token ;
- aucun texte autour ;
- aucune ponctuation ;
- aucun emoji ;
- si DOCS_CHUNKS est déjà présent et suffisant, tu n’as pas le droit d’écrire [[ESCALATE:DOCS]] ;
- si le besoin principal est du contexte billing ou un arbitrage global du plan, utilise [[ESCALATE]].
""".strip()

        user_prompt = f"""
MESSAGE UTILISATEUR:
{raw_msg}

{thread_alert_block}

{smalltalk_runtime_block}

PARAMÈTRES
- language: {language}
- tone: {tone}
- tutoiement: {use_tu_form}
- tutoiement_known: {use_tu_known}
- user_name: {user_name}

CONTEXTE MÉTIER COURT
- cabinet_name: {_safe_str(cabinet_ctx.get("name") or "cabinet")}
- member_job_role: {_safe_str(member_ctx.get("job_role") or "unknown")}
- member_role: {_safe_str(member_ctx.get("role") or "unknown")}
- discovery_status: {discovery_status}
- intro_smalltalk_turns: {intro_smalltalk_turns}

DOCS_CHUNKS
- ok: {dc_ok}
- scopes: {", ".join([_safe_str(s) for s in dc_scopes[:3]]) if dc_scopes else "[]"}
- chunks:
{docs_block}

WEB_SEARCH
- ok: {ws_ok}
- answer: {_safe_str(ws_answer)[:1800]}
- sources:
{sources_digest}

CONTEXTE JSON
{ctx_text}

INSTRUCTIONS DE RÉPONSE
- Réponds en "{language}".
- Si tutoiement=true, tutoie. Sinon vouvoie.
- Reste strictement dans le cadre professionnel du cabinet.
- Si l’utilisateur part sur un sujet hors travail / hors cabinet / hors médical / hors produit, recadre gentiment.
- Si web_search ok=true, utilise ses faits en priorité.
- Si DOCS_CHUNKS ok=true, utilise-les avant le JSON compact.
- Respecte strictement les conventions UI.

{fastpath_directive_block}

{state_block}

{intent_block}

{trial_feedback_block}

""".strip()

        p = load_lisa_system_prompts()

        chat_logger.info(
            "chat.response_writer.prompt_parts",
            system_base_len=len(SYSTEM_RESPONSE_WRITER_PROMPT.strip()),
            signature_len=len(p.get("signature", "")),
            format_len=len(p.get("format", "")),
            state_block_len=len(state_block or ""),
            intent_block_len=len(intent_block or ""),
            fastpath_directive_len=len(fastpath_directive_block or ""),
            fastpath_directive_enabled=bool(fastpath_directive_block),
            trial_feedback_block_len=len(trial_feedback_block or ""),
            trial_feedback_prompt_enabled=bool(trial_feedback_prompt_enabled),
            is_fastpath=is_fastpath,
            route_source=route_source,
            runtime_state=runtime_state_in or "null",
            ctx_text_len=len(ctx_text or ""),
            docs_block_len=len(docs_block or ""),
            sources_digest_len=len(sources_digest or ""),
        )
        system_prompt = (
            SYSTEM_RESPONSE_WRITER_PROMPT.strip()
            + "\n\n"
            + f"{p['signature']}\n\n"
            + f"{p['format']}\n\n"
            + f"(Prompts version: {p['version']})"
        )

        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        trace_payload = {
            "agent": "response_writer",
            "intent": intent,
            "mode": mode,
            "raw_user_message": raw_msg,
            "route_source": route_source,
            "runtime_state": runtime_state_in or "null",
        }

        meta_debug = {
            "ws_ok": ws_ok,
            "dc_ok": dc_ok,
            "intro_smalltalk_turns": intro_smalltalk_turns,
            "smalltalk_questions_budget_max": smalltalk_questions_budget_max,
            "smalltalk_questions_asked": smalltalk_questions_asked,
            "smalltalk_questions_remaining": smalltalk_questions_remaining,
            "trial_feedback_prompt_enabled": bool(trial_feedback_prompt_enabled),
            "docs_present": docs_present,
            "is_fastpath": is_fastpath,
            "runtime_state": runtime_state_in,
            "discovery_status": discovery_status,
        }

        return {
            "llm_messages": llm_messages,
            "trace_payload": trace_payload,
            "meta_debug": meta_debug,
            "docs_present": docs_present,
            "is_fastpath": is_fastpath,
            "runtime_state_in": runtime_state_in,
            "raw_msg": raw_msg,
            "wc": wc,
            "is_short_user_msg": is_short_user_msg,
            "language": language,
            "intent": intent,
            "mode": mode,
        }


    async def run_stream(
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
        trial_feedback_prompt_enabled: bool = False,
        context: Optional[Dict[str, Any]] = None,
        quota: Optional[Dict[str, Any]] = None,
        web: Optional[Dict[str, Any]] = None,
        web_search: Optional[Dict[str, Any]] = None,
        route_source: str = "orchestrator",
        runtime_state: Optional[str] = None,
        docs_chunks: Optional[Dict[str, Any]] = None,
        playbook: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        start_ts = time.time()

        build = self._build_llm_messages(
            user_message=user_message,
            raw_user_message=raw_user_message,
            intent=intent,
            language=language,
            tone=tone,
            need_web=need_web,
            mode=mode,
            smalltalk_target_key=smalltalk_target_key,
            transition_window=transition_window,
            transition_reason=transition_reason,
            soft_paywall_warning=soft_paywall_warning,
            intent_eligible=intent_eligible,
            intent_block_reason=intent_block_reason,
            trial_feedback_prompt_enabled=trial_feedback_prompt_enabled,
            context=context,
            quota=quota,
            web=web,
            web_search=web_search,
            route_source=route_source,
            runtime_state=runtime_state,
            docs_chunks=docs_chunks,
        )

        llm_messages = build["llm_messages"]
        trace_payload = build["trace_payload"]
        docs_present = bool(build["docs_present"])
        is_fastpath = bool(build["is_fastpath"])
        runtime_state_in = build["runtime_state_in"]
        raw_msg = build["raw_msg"]
        wc = int(build["wc"])
        is_short_user_msg = bool(build["is_short_user_msg"])

        log_llm_messages(
            event="llm.prompt.response_writer.stream",
            messages=llm_messages,
            trace={"agent": "response_writer", "intent": intent, "mode": mode, "stream": True},
            extra=build["meta_debug"],
        )

        chat_logger.info("chat.response_writer.raw_user_message", raw_len=len(raw_msg), raw_preview=raw_msg[:80])
        chat_logger.info(
            "chat.response_writer.thread_alert",
            word_count=wc,
            is_short=is_short_user_msg,
        )

        full_text_parts: list[str] = []
        meta_provider: Dict[str, Any] = {}

        try:
            async for event in self.llm.chat_text_stream(
                messages=llm_messages,
                temperature=0.4,
                max_tokens=1600,
                trace=trace_payload,
            ):
                etype = event.get("type")

                if etype == "start":
                    meta_provider = {
                        "provider": event.get("provider"),
                        "model": event.get("model"),
                    }
                    yield {
                        "type": "start",
                        "provider": event.get("provider"),
                        "model": event.get("model"),
                    }
                    continue

                if etype == "delta":
                    text = _safe_str(event.get("text") or "")
                    if text:
                        full_text_parts.append(text)

                        # IMPORTANT:
                        # en fastpath, on bufferise les deltas en interne
                        # pour éviter de leak un token [[ESCALATE...]] au front
                        if not is_fastpath:
                            yield {
                                "type": "delta",
                                "text": text,
                            }
                    continue

                if etype == "end":
                    meta_provider["duration_ms"] = event.get("duration_ms")
                    continue

        except Exception as e:
            yield {
                "type": "error",
                "error": "RESPONSE_WRITER_LLM_ERROR",
                "message": _safe_str(e)[:200],
                "debug": {
                    "duration_ms": int((time.time() - start_ts) * 1000),
                },
            }
            return

        answer = "".join(full_text_parts).strip()

        if is_fastpath:
            txt = answer or ""
            esc_reason = None

            if "[[ESCALATE:WEB]]" in txt:
                esc_reason = "need_web"
            elif "[[ESCALATE:DOCS]]" in txt:
                if docs_present:
                    esc_reason = "need_docs_blocked_but_docs_present"
                else:
                    esc_reason = "need_docs"
            elif "[[ESCALATE]]" in txt:
                esc_reason = "out_of_scope"

            if esc_reason:
                yield {
                    "type": "error",
                    "error": "ESCALATE_TO_ORCHESTRATOR",
                    "message": "",
                    "reason": esc_reason,
                    "debug": {
                        "intent": intent,
                        "route_source": "fastpath",
                        "runtime_state": runtime_state_in,
                        "duration_ms": int((time.time() - start_ts) * 1000),
                    },
                }
                return

        import re

        answer = re.sub(r"(?m)^\s*```.*\n?", "", answer)
        answer = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", answer)

        if intent == "amabilities" and len(answer) > 260:
            answer = answer[:257] + "..."

        yield {
            "type": "final",
            "ok": True,
            "answer": answer,
            "debug": {
                "provider": meta_provider.get("provider"),
                "model": meta_provider.get("model"),
                "duration_ms": int((time.time() - start_ts) * 1000),
                "intent": intent,
                "need_web": need_web,
            },
        }

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
        trial_feedback_prompt_enabled: bool = False,
        context: Optional[Dict[str, Any]] = None,
        quota: Optional[Dict[str, Any]] = None,
        web: Optional[Dict[str, Any]] = None,
        web_search: Optional[Dict[str, Any]] = None,
        route_source: str = "orchestrator",
        runtime_state: Optional[str] = None,
        docs_chunks: Optional[Dict[str, Any]] = None,
        playbook: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        final_answer = ""
        final_debug: Dict[str, Any] = {}

        async for event in self.run_stream(
            user_message=user_message,
            raw_user_message=raw_user_message,
            intent=intent,
            language=language,
            tone=tone,
            need_web=need_web,
            mode=mode,
            smalltalk_target_key=smalltalk_target_key,
            transition_window=transition_window,
            transition_reason=transition_reason,
            soft_paywall_warning=soft_paywall_warning,
            intent_eligible=intent_eligible,
            intent_block_reason=intent_block_reason,
            trial_feedback_prompt_enabled=trial_feedback_prompt_enabled,
            context=context,
            quota=quota,
            web=web,
            web_search=web_search,
            route_source=route_source,
            runtime_state=runtime_state,
            docs_chunks=docs_chunks,
            playbook=playbook,
        ):
            etype = event.get("type")

            if etype == "error":
                if event.get("error") == "ESCALATE_TO_ORCHESTRATOR":
                    return {
                        "ok": False,
                        "error": "ESCALATE_TO_ORCHESTRATOR",
                        "answer": "",
                        "reason": event.get("reason"),
                        "debug": event.get("debug") or {},
                    }

                return {
                    "ok": False,
                    "error": event.get("error") or "RESPONSE_WRITER_ERROR",
                    "answer": "",
                    "debug": event.get("debug") or {},
                }

            if etype == "final":
                final_answer = event.get("answer") or ""
                final_debug = event.get("debug") or {}

        return {
            "ok": True,
            "answer": final_answer,
            "debug": final_debug,
        }