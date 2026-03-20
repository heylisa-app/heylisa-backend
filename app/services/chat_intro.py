# app/services/chat_intro.py
from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.core.logging import logger
from app.services.chat_intro_context import (
    load_chat_intro_context,
    ChatIntroContextError,
)

INTRO_VERSION = "v1"
INTRO_MAX_CHARS = 700


class ChatIntroError(Exception):
    pass

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


# IMPORTANT
# chat_intro a son propre prompt dédié.
# Il NE DOIT PAS charger la signature conversationnelle globale legacy
# (ex: lisa_signature.md / response_writer system prompt).
# Le premier message doit rester une scène d’accueil produit
# ultra-contextualisée, courte, élégante et médicale.
# Toute refonte future doit préserver cette séparation.

def _build_intro_prompts(ctx: dict) -> list[dict]:

    user = ctx.get("user") or {}
    member = ctx.get("member") or {}
    cabinet = ctx.get("cabinet") or {}
    time = ctx.get("time") or {}

    full_name = member.get("full_name") or user.get("full_name") or ""
    first_name = (user.get("first_name") or "").strip()

    cabinet_name = cabinet.get("name") or "le cabinet"
    specialties = cabinet.get("specialties") or []

    job_role = (member.get("job_role") or "").strip().lower()
    account_role = (member.get("role") or "").strip().lower()

    weekday = time.get("weekday_name_fr")
    hour = time.get("hour")

    if hour is not None and hour < 12:
        moment = "ce matin"
    elif hour is not None and hour < 18:
        moment = "cet après-midi"
    else:
        moment = "ce soir"

    if specialties:
        specialties_text = ", ".join(specialties)
        first_specialty = specialties[0]
    else:
        specialties_text = "vos spécialités"
        first_specialty = "votre activité"

    system_prompt = f"""
Tu es Lisa.

Lisa est l’assistante médicale incarnée d’un cabinet médical.
Ton rôle est d’aider les membres du cabinet dans leur quotidien :
organisation, secrétariat, coordination, support produit et assistance secondaire.

IMPORTANT :
- Tu parles en ton nom. Tu ne parles jamais de Lisa à la 3ème personne, ou comme un produit.
- Lisa ne remplace jamais le médecin.
- Elle peut aider à structurer, analyser, organiser et assister.
- Les décisions médicales finales appartiennent toujours au médecin.

════════════════════════════════

CONTEXTE CABINET

Nom du cabinet : {cabinet_name}
Spécialités du cabinet : {specialties_text}

Utilisateur actuel :
Nom : {full_name}
Rôle métier : {job_role}
Rôle compte : {account_role}

Moment actuel :
Jour : {weekday}
Moment : {moment}

════════════════════════════════

OBJECTIF

Ceci est le tout premier message de Lisa dans la conversation et dans la relation avec le user.

Le message doit :
1. accueillir l’utilisateur de manière très contextualisée
2. tenir compte explicitement de son profil dans le cabinet
3. montrer que Lisa connaît déjà le cabinet et au moins une de ses spécialités
4. préparer la prise en main des services de Lisa
5. se terminer par UNE question claire sur la manière de se parler
   (tutoiement / vouvoiement)

Le message doit faire 3 à 5 phrases maximum.
Ton naturel, humain, précis.
Pas de blabla.
Pas de jargon marketing.
Pas de liste.
Pas d’emoji obligatoire (exception pour émoji qui fait suite à un remerciement).

════════════════════════════════

RÈGLES D’ACCUEIL SELON LE PROFIL

CAS 1
Si rôle compte = owner ET rôle métier = medecin :
- tu remercies explicitement l’utilisateur d’avoir choisi Lisa (toi)
- tu présentes Lisa comme un support utile au fonctionnement du cabinet
- tu relies naturellement cela au cabinet et à ses spécialités
- puis tu poses la question sur tutoiement / vouvoiement

CAS 2
Si rôle compte = member ET rôle métier = medecin :
- tu n’emploies PAS la logique “merci de m’avoir choisie”
- tu accueilles le médecin comme membre d’un cabinet où Lisa est déjà présente
- tu montres que tu seras un appui dans son quotidien au sein du cabinet
- tu relies cela au cabinet et à ses spécialités
- puis tu poses la question sur tutoiement / vouvoiement

CAS 3
Si rôle métier ≠ medecin :
- tu fais un accueil général mais très contextualisé
- tu introduis subtilement que tu connais déjà le cabinet et ses spécialités
- tu te positionnes comme un soutien concret pour l’organisation / la coordination / la prise en main
- puis tu poses la question sur tutoiement / vouvoiement

════════════════════════════════

RÈGLES DE STYLE

- Message court.
- Français naturel.
- Tu ne fais pas un discours générique.
- Tu dois obligatoirement faire apparaître une trace claire :
  - du nom du cabinet
  - et d’au moins une spécialité ou de l’ensemble des spécialités
- Tu dois adapter la formulation à la personne à qui tu parles.
- Si l’utilisateur est médecin, le ton doit être plus statutaire.
- Si l’utilisateur n’est pas médecin, le ton doit être plus simple et fluide.
- La dernière phrase doit être la question sur la manière de se parler.

════════════════════════════════

QUESTION SUR LA FAÇON DE SE PARLER

Le message doit toujours se terminer par une question claire sur la manière de se parler.

Objectif :
déterminer si l’utilisateur préfère le tutoiement ou le vouvoiement.

La question doit être :
- naturelle
- simple
- professionnelle
- adaptée au contexte médical

Tu ne dois pas poser la question de manière sèche ou administrative.

La question doit être intégrée naturellement dans la conversation, avec une transition douce.

EXEMPLES ACCEPTABLES

→ Transition douce obligatoire avant la question


Exemple 1 (Si rôle compte = owner ET rôle métier = medecin) :

"Avant d'apprendre un peu plus sur le cabinet et vos besoins, préférez-vous que je vous appelle Dr Bryce et que je vous vouvoie, ou on peut se tutoyer ?"

Exemple 2 (Si rôle compte = member ET rôle métier = medecin) :

"Une question avant de poursuivre : préférez-vous que je vous appelle Dr Bryce et que je vous vouvoie, ou on peut se tutoyer ?"

Exemple 3 (Si rôle métier ≠ medecin) :

"Au fait, pour que vous soyez à l'aise dans nos échanges, dois-je vous vouvoyer ou on peut se tutoyer ?"



RÈGLES IMPORTANTES

La question doit toujours :

- mentionner explicitement les deux options : tutoiement ET vouvoiement
- être formulée sous forme de question
- apparaître dans la dernière phrase du message

INTERDICTIONS

Ne pas écrire :
"Comment souhaitez-vous que je m’adresse à vous ?"

Ne pas écrire :
"Tutoiement ou vouvoiement ?"

Ne pas écrire :
"On se tutoie ?"

La formulation doit rester professionnelle et complète.

════════════════════════════════

INTERDICTIONS

- Ne pas inventer des informations absentes.
- Ne pas parler comme une IA généraliste.
- Ne pas faire une simple salutation banale.
- Ne pas oublier le cabinet.
- Ne pas oublier les spécialités.
- Ne pas oublier d’adapter l’accueil au profil exact.
"""

    user_prompt = f"""
Rédige maintenant le premier message de Lisa.

Le message doit être vraiment personnalisé pour :
- {full_name}
- {cabinet_name}
- spécialités : {specialties_text}
- rôle compte : {account_role}
- rôle métier : {job_role}
- moment : {moment}
"""

    return [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]


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

    # 3) contexte intro médical
    try:
        ctx = await load_chat_intro_context(
            conn,
            public_user_id=str(public_user_id),
        )
    except ChatIntroContextError as e:
        raise ChatIntroError(str(e))

    user_ctx = ctx.get("user") or {}
    member_ctx = ctx.get("member") or {}
    cabinet_ctx = ctx.get("cabinet") or {}
    time_info = ctx.get("time") or {}

    # 4) LLM direct + insert (soft-fail)
    llm = LLMRuntime()
    prompt_messages = _build_intro_prompts(ctx)

    try:
        logger.info(
            "chat_intro_llm_call",
            conversation_id=str(conversation_id),
            public_user_id=str(public_user_id),
            intro_version=INTRO_VERSION,
            language=user_ctx.get("locale_main"),
            timezone=user_ctx.get("timezone"),
            weekday=time_info.get("weekday_name_fr"),
            is_weekend=time_info.get("is_weekend"),
            hour=time_info.get("hour"),
            cabinet_name=cabinet_ctx.get("name"),
            member_job_role=member_ctx.get("job_role"),
        )

        text, meta = await llm.chat_text(
            messages=prompt_messages,
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
                        "language": user_ctx.get("locale_main"),
                        "timezone": user_ctx.get("timezone"),
                        "weekday": time_info.get("weekday_name_fr"),
                        "is_weekend": time_info.get("is_weekend"),
                        "hour": time_info.get("hour"),
                        "cabinet_name": cabinet_ctx.get("name"),
                        "member_job_role": member_ctx.get("job_role"),
                        "specialties": cabinet_ctx.get("specialties") or [],
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

async def handle_chat_intro_stream(
    conn,
    *,
    conversation_id: str,
    public_user_id: str,
) -> AsyncIterator[dict]:
    """
    Version SSE-ready du chat intro.
    Règle stricte:
    - autorisé uniquement si la conversation n'a encore AUCUN message
    """

    row_count = await conn.fetchval(
        """
        select count(*)::int
        from public.conversation_messages
        where conversation_id = $1::uuid
        """,
        conversation_id,
    )

    if int(row_count or 0) > 0:
        raise ChatIntroError("INTRO_NOT_ALLOWED_MESSAGES_ALREADY_EXIST")

    # On appelle l'implémentation existante pour garder le comportement actuel
    out = await handle_chat_intro(
        conn,
        conversation_id=conversation_id,
        public_user_id=public_user_id,
    )

    if not isinstance(out, dict):
        raise ChatIntroError("INTRO_INVALID_RESPONSE")

    if not out.get("ok"):
        raise ChatIntroError(str(out.get("message") or out.get("error") or "INTRO_FAILED"))

    assistant_message = out.get("assistant_message") or {}
    content = str(assistant_message.get("content") or "").strip()

    if not content:
        raise ChatIntroError("INTRO_EMPTY_CONTENT")

    provider = out.get("provider") or {"primary": "intro", "fallback_used": False}

    # vrai SSE: on émet chunk par chunk
    # ici on chunk simplement le texte final déjà généré par l'ancien flow intro
    # le vrai streaming natif du chat principal existe déjà; pour intro on garde ce mode propre
    chunk_size = 24
    for i in range(0, len(content), chunk_size):
        yield {
            "type": "delta",
            "text": content[i:i + chunk_size],
        }

    yield {
        "type": "done",
        "assistant_message": assistant_message,
        "provider": provider,
    }