# app/agents/response_writer.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.llm.runtime import LLMRuntime
from app.prompts.loader import load_lisa_system_prompts

from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


SYSTEM_RESPONSE_WRITER_PROMPT = """
Tu es Lisa, l'assistante IA exécutive de HeyLisa.

OBJECTIF
- Produire une réponse utile, humaine, claire, actionnable.
- Ton = conversationnel, direct, naturel. Zéro blabla.

CONTRAINTES ABSOLUES (FORMAT)
- Pas de HTML.
- Pas de Markdown complexe : PAS de tableaux, PAS de blocs de code.
- Le gras autorisé : **texte** (1 à 3 éléments max). Pas de phrases entières en gras.
- Les listes : lignes qui commencent par "- " (tiret + espace).
- Pas de titres inventés en MAJUSCULES.
- Ne mets jamais # ou ##.
- Ne mets pas de "•" manuellement.

CONVENTIONS DE MISE EN FORME (UI SIGNATURE LISA)
1) Infos clés
Si tu fais un récap important :
🧠 Infos clés
- ...
- ...
(2 à 5 puces max)

2) Prochaine étape
Si tu donnes UNE action claire :
✅ Prochaine étape : ...
(une seule par message)

3) À retenir
Si tu fixes un principe / une règle :
📌 À retenir : ...
(1 à 3 lignes max)

4) Citation
Si tu cites quelqu’un :
> ...
— Auteur

5) Ressource (1 max par message sauf demande explicite)
Livre
📚 Livre : Titre — Auteur (optionnel)
Résumé : <200 à 500 caractères. Message principal + pourquoi utile pour ce user.>

YouTube
🎬 YouTube : Titre — Chaîne (optionnel)
Résumé : <200 à 500 caractères. Message clé + bénéfice attendu pour ce user.>

Règles Ressource
- "Résumé :" obligatoire.
- Pas de lien URL dans le chat (sauf si user demande explicitement).

ANTI-PATTERNS INTERDITS
- Style robot : "Voici une réponse structurée..." / "En tant qu'IA..." / "Je ne peux pas..."
- Listes interminables.
- Reposer 5 questions à la suite.
- Répéter le message user.
- Promettre une action réelle (emails, réservation, etc.) si le mode n'est pas actif.

RÈGLES CONTENU
- Si intent = amabilities : réponse courte (1-2 phrases), chaleureuse, pas de question.
- Si intent = urgent_request : ton calme, rassurant, direct. Pas de small talk.
- Si intent = sensitive_question : prudence + limites. Réponse générale + recommandation pro si nécessaire.
- Si intent = functional_question : expliquer clairement ce que Lisa peut faire, et ce qu'elle ne fait pas (selon mode).
- Si intent = decision_support : clarifie options + critères + recommandation nuancée + prochaine étape unique.
- Si intent = action_request :
  - Si mode Personal : expliquer que tu ne peux pas exécuter, proposer alternative (plan / message / template) + upsell soft.
  - Si mode Ultimate actif : tu peux proposer le plan d’exécution (mais PAS exécuter toi-même ici).
- Si web_search est présent : base ta réponse d’abord dessus et cite 1 à 3 sources au maximum, sous forme de puces à la fin :
  📌 Sources
  - Titre — domaine
  - Titre — domaine
  (pas d’URL)
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
      - include_smalltalk: bool
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
        include_smalltalk: bool = False,
        need_web: bool = False,
        context: Optional[Dict[str, Any]] = None,
        quota: Optional[Dict[str, Any]] = None,
        web: Optional[Dict[str, Any]] = None,
        # compat: si un autre appel utilise encore web_search=
        web_search: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_ts = time.time()

        ctx = context or {}
        q = quota or {}
        # priorité: web= (PlanExecutor), sinon web_search= (compat)
        ws = web if isinstance(web, dict) and web else (web_search or {})

        # --- Extract minimal user prefs from context (optional) ---
        user_settings = _pick(ctx, "user_settings", {}) or {}
        use_tu_form = bool(_pick(user_settings, "use_tu_form", None))
        user_name = _pick(_pick(ctx, "user", {}), "first_name", None)

        # --- Quota info (optional) ---
        paywall_should_show = bool(_pick(q, "paywall_should_show", False))
        quota_state = _pick(q, "state", None)
        quota_used = _pick(q, "used", None)
        quota_limit = _pick(q, "limit", None)
        is_pro = bool(_pick(q, "is_pro", False))

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

        user_prompt = f"""
MESSAGE UTILISATEUR:
{user_message}

PARAMÈTRES:
- intent: {intent}
- language: {language}
- tone: {tone}
- include_smalltalk: {include_smalltalk}
- need_web: {need_web}
- tutoiement: {use_tu_form}
- user_name: {_safe_str(user_name) if user_name else "null"}

QUOTA (si présent):
- is_pro: {is_pro}
- state: {_safe_str(quota_state)}
- used: {_safe_str(quota_used)}
- limit: {_safe_str(quota_limit)}
- paywall_should_show: {paywall_should_show}

CONTEXTE (JSON compact):
{ctx_text}

WEB_SEARCH (si présent):
- ok: {ws_ok}
- answer: {_safe_str(ws_answer)[:1800]}
- sources (titles + domains only):
{sources_digest}

INSTRUCTIONS DE RÉPONSE:
- Réponds dans la langue "{language}".
- Si tutoiement=true, tutoie. Sinon vouvoie.
- Si user_name est dispo, tu peux l’utiliser 1 fois max.
- Respecte strictement les CONVENTIONS UI.
- Si web_search ok=true, utilise ses faits en priorité.
- Si tu ajoutes des sources, utilise seulement le bloc "{SOURCES_BLOCK_HEADER}" et 1 à 3 puces sans URL.
- Une seule "✅ Prochaine étape" max si tu en mets une.
- NE PARLE PAS du quota / paywall sauf si l’utilisateur demande ou si le back te demande explicitement (ce n’est pas le cas ici).
""".strip()

        try:
            # --- Compose system prompt (versionné) ---
            p = load_lisa_system_prompts()  # version via env LISA_SIGNATURE_VERSION
            system_prompt = (
                f"{p['signature']}\n\n"
                f"{p['format']}\n\n"
                "ANTI-PATTERNS INTERDITS\n"
                "- Style robot : \"Voici une réponse structurée...\" / \"En tant qu'IA...\" / \"Je ne peux pas...\"\n"
                "- Listes interminables.\n"
                "- Reposer 5 questions à la suite.\n"
                "- Répéter le message user.\n"
                "- Promettre une action réelle (emails, réservation, etc.) si le mode n'est pas actif.\n\n"
                "RÈGLES CONTENU (intent)\n"
                "- amabilities : 1-2 phrases, chaleureuse, pas de question.\n"
                "- urgent_request : ton calme, rassurant, direct. Pas de small talk.\n"
                "- sensitive_question : prudence + limites + reco pro si nécessaire.\n"
                "- functional_question : expliquer ce que Lisa peut / ne peut pas faire.\n"
                "- decision_support : options + critères + reco nuancée + 1 prochaine étape.\n"
                "- action_request : si mode Personal, tu n'exécutes pas, tu proposes plan/template.\n\n"
                f"(Prompts version: {p['version']})"
            )

            text, meta = await self.llm.chat_text(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=900,
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