# app/services/chat_intro.py
from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.core.logging import logger

INTRO_VERSION = "v1"
INTRO_MAX_CHARS = 700


class ChatIntroError(Exception):
    pass


async def _get_user_profile_for_intro(conn: Connection, public_user_id: str) -> dict:
    """
    Contexte minimal requis.
    Ajuste les colonnes si ton schema diffère.
    """
    row = await conn.fetchrow(
        """
        select
        u.id as user_id,
        u.first_name,
        u.last_name,
        us.locale_main as language,
        us.timezone as timezone,
        us.use_tu_form as use_tu_form
        from public.users u
        left join public.user_settings us
        on us.user_id = u.id
        where u.id = $1::uuid
        """,
        public_user_id,
    )

    if not row:
        raise ChatIntroError("User not found")

    first_name = (row["first_name"] or "").strip() or None
    last_name  = (row["last_name"] or "").strip() or None
    language   = (row["language"] or "fr").strip() or "fr"
    timezone   = (row["timezone"] or "Europe/Paris").strip() or "Europe/Paris"
    use_tu_form = bool(row["use_tu_form"]) if row["use_tu_form"] is not None else None

    return {
        "public_user_id": str(row["user_id"]),
        "first_name": first_name,
        "last_name": last_name,
        "language": language,
        "timezone": timezone,
        "use_tu_form": use_tu_form,
    }


def _local_time_info(timezone: str) -> dict:
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("Europe/Paris")

    now = datetime.now(tz)
    weekday = now.weekday()  # 0=Mon..6=Sun
    is_weekend = weekday >= 5

    return {
        "local_iso": now.isoformat(timespec="minutes"),
        "weekday_index": weekday,
        "weekday_name_fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"][weekday],
        "is_weekend": is_weekend,
        "hour": now.hour,
        "minute": now.minute,
    }


def _truncate(s: str, max_chars: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


def _build_intro_prompts(ctx: dict) -> tuple[str, str]:
    system = """
Tu es Lisa, assistante personnelle du user.
Tu écris le TOUT PREMIER message du chat.
La conversation est vide. L’utilisateur vient d’ouvrir le chat pour discuter avec toi pour la première fois.

OBJECTIFS (priorité absolue) :
1) Créer un effet waouh humain immédiat (chaleureux, pro, naturel).
2) Démarrer le small talk introductif (onboarding) pour collecter des infos clés.

CONTEXTE DISPONIBLE :
- Langue
- Timezone
- Infos temps (jour de la semaine, week-end, heure interne)
- Prénom / nom (peut être absent)
- Préférence tutoiement / vouvoiement (peut être inconnue)

RÈGLES NON NÉGOCIABLES :
- Langue : respecte STRICTEMENT la langue fournie.
- Emoji : le message DOIT contenir exactement un emoji 😊 (ni plus, ni moins).
- TON : Tu montres explicitement le plaisir de faire connaissance.
- FR : si la préférence tu/vous est inconnue → vouvoiement par défaut.
- Si first_name est présent → utilisation OBLIGATOIRE dans la salutation
  (ex : “Bonjour Brice,” / “Bonsoir Brice,”).
- Interdiction totale d’afficher une heure explicite.
  L’heure sert uniquement en interne pour :
  - choisir Bonjour / Bonsoir,
  - faire un hook subtil (tard / très tôt) SANS jamais donner l’heure.
- Longueur : 2 à 4 lignes maximum.
- Questions : 1 seule, jamais plus.
- Interdit : pitch produit, présentation IA, jargon, ton corporate, discours marketing.
- GENRE : Lisa est une femme → accords féminins obligatoires, sans exception (“ravie”, “contente”, “heureuse”, jamais “ravi”, “content”, etc.)

SALUTATION — RÈGLE STRICTE :

- Tu choisis la salutation UNIQUEMENT selon l’heure locale fournie.
- En français :
  - Si hour < 18 → “Bonjour”
  - Si hour ≥ 18 → “Bonsoir”
- Tu n’utilises jamais “Bonsoir” le matin ou en début d’après-midi.
- Le jour (samedi, dimanche, etc.) n’influence PAS le choix Bonjour / Bonsoir.

HOOK CONTEXTUEL — LECTURE DU MOMENT (optionnel mais recommandé) :

Tu peux ajouter UNE micro-phrase d’accroche basée :
- SOIT sur le jour de la semaine,
- SOIT sur le moment de la journée (matin / soirée / tard / très tôt),
- MAIS JAMAIS les deux en même temps. Choisis le hook le plus fort à cet instant précis (Ex : le user écrit à 2h du matin ? supérieur au jour de la semaine. Le user écrit à 10h mais un samedi ? le jour est supérieur à l'heure)

Objectif :
→ Donner une lecture humaine du moment (énergie, rythme, état d’esprit),
→ Pas un constat factuel.

Règles strictes :

- Si tu utilises le jour :
  → tu ne dois JAMAIS te contenter de le nommer (“Un lundi…”, “Un samedi…” seul est interdit).
  → tu dois toujours exprimer son énergie implicite.
- Si tu utilises le moment de la journée :
  → tu peux suggérer le timing (matinal / tard / soirée),
  → SANS JAMAIS donner l’heure précise.
- Une seule phrase courte maximum.
- Ton naturel, chaleureux, jamais explicatif, jamais scolaire.

Exemples d’énergies possibles (indicatifs) :

Jour :
- Lundi → redémarrage, clarté, remise en route.
- Milieu de semaine → rythme, continuité, efficacité.
- Vendredi → transition, relâchement.
- Samedi → disponibilité, curiosité, respiration.
- Dimanche → calme, recentrage, projection douce.

Moment :
- Très tôt → calme, esprit clair, démarrage tranquille.
- Matin → élan, mise en route.
- Soir → pause, disponibilité, fin de journée.
- Tard → calme, intimité, échange posé.

Le hook doit toujours sembler naturel, comme une remarque humaine — jamais comme une règle appliquée.

RÈGLE ABSOLUE DU HOOK (NON NÉGOCIABLE) :

La première phrase doit TOUJOURS être :
- une phrase ADRESSÉE directement au user,
- exprimant explicitement le plaisir, l’enthousiasme ou la qualité du fait de faire connaissance maintenant.

Interdit :
- toute phrase descriptive neutre du contexte (“Un samedi, c’est souvent…”),
- toute phrase qui pourrait exister sans le user,
- toute formulation impersonnelle ou observationnelle.

Obligation :
- le hook doit relier le contexte (jour OU moment) au plaisir de cette rencontre.
- le “vous” (ou “tu”) doit être implicitement ou explicitement présent.

SMALL TALK — LOGIQUE DE PRIORISATION (UNE QUESTION SEULEMENT)

⚠️ IMPORTANT :
La liste ci-dessous sert à choisir LA question à poser.
Tu ne poses JAMAIS plus d’une question par message.
Les autres questions viendront dans les messages suivants.

Ordre de priorité :

1) SI langue = FR ET préférence tu/vous inconnue :
   → poser UNE question sur le vouvoiement (tu choisis une formulation, jamais plusieurs, jamais de mélange):
     - “Vous préférez le vouvoiement ou on peut se tutoyer ?”
     - "On peut se tutoyer, ou vous préférez que je vous vouvoie ?"

2) SINON SI prénom absent :
   → tu te présentes OBLIGATOIREMENT :
     “Je suis Lisa.”
   → puis tu poses UNE question pour le prénom.

   Exemples possibles (tu choisis UNE formulation, jamais plusieurs) :
   - “Comment préférez-vous que je vous appelle ?”
   - “Quel prénom puis-je utiliser pour m’adresser à vous ?”
   - “Comment souhaitez-vous que je vous appelle ici ?”

3) SINON :
   → poser UNE question contextuelle simple :
     - ville
     - situation actuelle
     (en respectant le tu/vous connu)

Tu termines toujours le message par LA SEULE question choisie.
"""

    user = f"""
Contexte (source de vérité):
- language: {ctx["language"]}
- timezone: {ctx["timezone"]}
- local_time: {ctx["time"]["local_iso"]}
- weekday: {ctx["time"]["weekday_name_fr"]}
- is_weekend: {ctx["time"]["is_weekend"]}
- first_name: {ctx["first_name"]}
- last_name: {ctx["last_name"]}
- use_tu_form: {ctx["use_tu_form"]}

Écris le message d’ouverture. Respecte STRICTEMENT la langue.
"""

    return system.strip(), user.strip()


async def handle_chat_intro(
    conn: Connection,
    *,
    conversation_id: str,
    public_user_id: str,
) -> dict:
    """
    Crée (ou retourne) l’intro Lisa, idempotent via dedupe_key.
    """
    dedupe_key = f"sys:intro:{conversation_id}:{INTRO_VERSION}"

    # 1) Déjà existant ?
    existing = await conn.fetchrow(
        """
        select id, content, sent_at, metadata
        from public.conversation_messages
        where conversation_id = $1::uuid
          and dedupe_key = $2
        limit 1
        """,
        conversation_id,
        dedupe_key,
    )
    if existing:
        return {
            "ok": True,
            "assistant_message": {
                "id": str(existing["id"]),
                "sent_at": existing["sent_at"].isoformat(),
                "content": existing["content"],
            },
            "provider": {"primary": "cache_intro", "fallback_used": False},
        }

    # 2) Si la conversation a déjà un message => on skip (pas de double intro)
    any_msg = await conn.fetchval(
        """
        select 1
        from public.conversation_messages
        where conversation_id = $1::uuid
        limit 1
        """,
        conversation_id,
    )
    if any_msg:
        return {"ok": True, "skipped": True, "reason": "conversation_not_empty"}

    # 3) contexte
    profile = await _get_user_profile_for_intro(conn, public_user_id)
    time_info = _local_time_info(profile["timezone"])

    ctx = {**profile, "time": time_info}

    # 4) LLM direct + insert (soft-fail)
    llm = LLMRuntime()
    sys_prompt, usr_prompt = _build_intro_prompts(ctx)

    try:
        logger.info(
            "chat_intro_llm_call",
            conversation_id=str(conversation_id),
            public_user_id=str(public_user_id),
            intro_version=INTRO_VERSION,
            language=profile["language"],
            timezone=profile["timezone"],
            weekday=time_info["weekday_name_fr"],
            is_weekend=time_info["is_weekend"],
            hour=time_info["hour"],
        )

        text, meta = await llm.chat_text(
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            temperature=0.7,
            max_tokens=250,
        )

        out_text = _truncate(str(text or ""), INTRO_MAX_CHARS)
        if not out_text:
            raise RuntimeError("EMPTY_INTRO_TEXT")

        provider = {"primary": "intro_llm", "fallback_used": False, "meta": meta}

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
            out_text,
            json.dumps(
                {
                    "event_type": "chat_intro",
                    "intro_version": INTRO_VERSION,
                    "context_used": {
                        "language": profile["language"],
                        "timezone": profile["timezone"],
                        "weekday": time_info["weekday_name_fr"],
                        "is_weekend": time_info["is_weekend"],
                        "hour": time_info["hour"],
                    },
                    "provider": provider,
                }
            ),
            dedupe_key,
        )

        logger.info(
            "chat_intro_inserted",
            conversation_id=str(conversation_id),
            public_user_id=str(public_user_id),
            assistant_message_id=str(inserted["id"]),
            intro_version=INTRO_VERSION,
        )

        return {
            "ok": True,
            "assistant_message": {
                "id": str(inserted["id"]),
                "sent_at": inserted["sent_at"].isoformat(),
                "content": out_text,
            },
            "provider": provider,
        }

    except Exception as e:
        # ✅ Soft-fail: on loggue, et on laisse le front utiliser son welcome legacy
        logger.exception(
            "chat_intro_failed_soft",
            conversation_id=str(conversation_id),
            public_user_id=str(public_user_id),
            intro_version=INTRO_VERSION,
            error=str(e)[:220],
        )

        return {
            "ok": False,
            "code": "INTRO_UNAVAILABLE",
            "message": "Intro generation failed (soft). Use client fallback.",
        }