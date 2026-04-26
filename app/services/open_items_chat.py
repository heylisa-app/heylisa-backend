#app/services/open_items_chat.py

from __future__ import annotations

from typing import Optional
import json
import re
import asyncio

from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.core.chat_logger import chat_logger
from app.services.context_open_items import load_open_items_context
from app.integrations.n8n_followup_after_info_collected import (
    fire_followup_after_info_collected_webhook,
)


class OpenItemsChatError(Exception):
    pass


def _json_preview(value: dict, max_chars: int = 7000) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = "{}"

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3] + "..."


def _clean_llm_answer(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"(?m)^\s*```.*\n?", "", cleaned)
    cleaned = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", cleaned)
    return cleaned.strip()


def _extract_info_collected_token(text: str) -> tuple[str, dict | None]:
    raw = str(text or "").strip()

    match = re.search(r"(?m)^\s*info_collected\s*=\s*(true|false)\s*$", raw)
    if not match:
        return raw, None

    human_text = raw[: match.start()].strip()
    token_block = raw[match.start():].strip()
    token_lines = token_block.splitlines()

    token: dict[str, str] = {}

    allowed_keys = {
        "info_collected",
        "action_type",
        "request_id",
        "contact_email",
        "patient_name",
    }

    for line in token_lines:
        clean_line = line.strip()
        if not clean_line or "=" not in clean_line:
            continue

        key, value = clean_line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key in allowed_keys:
            token[key] = value

    if token.get("info_collected") != "true":
        return human_text, None

    return human_text, token


def _build_followup_after_info_collected_payload(
    *,
    session_id: str,
    public_user_id: str,
    cabinet_id: str | None,
    user_message: dict,
    assistant_message_text: str,
    token: dict,
    context: dict,
) -> dict:
    open_items = (context or {}).get("open_items") or {}
    priority_item = open_items.get("priority_item") or {}

    return {
        "event": "followup_after_info_collected",
        "source": "open_items_chat",
        "session_id": session_id,
        "public_user_id": public_user_id,
        "cabinet_id": cabinet_id,
        "request_id": token.get("request_id") or priority_item.get("id"),
        "action_type": token.get("action_type"),
        "contact_email": token.get("contact_email"),
        "patient_name": token.get("patient_name"),
        "user_message": user_message,
        "assistant_message_text": assistant_message_text,
        "priority_item": priority_item,
        "context": {
            "interlocutor": (context or {}).get("interlocutor"),
            "cabinet": (context or {}).get("cabinet"),
            "cabinet_settings": (context or {}).get("cabinet_settings"),
            "integrations": (context or {}).get("integrations"),
        },
    }


async def _get_public_user_id_from_auth(conn: Connection, auth_user_id: str) -> str | None:
    row = await conn.fetchrow(
        """
        select id
        from public.users
        where auth_user_id = $1
        limit 1
        """,
        auth_user_id,
    )
    return str(row["id"]) if row else None


async def _get_open_items_session(conn: Connection, session_id: str):
    return await conn.fetchrow(
        """
        select id, cabinet_id, public_user_id, priority_info_request_id, status
        from public.open_items_chat_sessions
        where id = $1::uuid
        limit 1
        """,
        session_id,
    )

async def _get_open_items_recent_history(
    conn: Connection,
    *,
    session_id: str,
    limit: int = 12,
) -> list[dict]:
    rows = await conn.fetch(
        """
        select sender_type, role, content, sent_at
        from public.open_items_chat_messages
        where session_id = $1::uuid
        order by sent_at desc
        limit $2
        """,
        session_id,
        limit,
    )

    items = [
        {
            "sender_type": str(row["sender_type"] or ""),
            "role": str(row["role"] or ""),
            "content": str(row["content"] or "").strip(),
            "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None,
        }
        for row in rows
        if str(row["content"] or "").strip()
    ]

    return list(reversed(items))


async def _insert_open_items_user_message(
    conn: Connection,
    *,
    session_id: str,
    content: str,
) -> dict:
    row = await conn.fetchrow(
        """
        insert into public.open_items_chat_messages (
            session_id,
            sender_type,
            role,
            content,
            dedupe_key
        )
        values (
            $1::uuid,
            'user',
            'user',
            $2::text,
            $3::text
        )
        returning id, content, sent_at
        """,
        session_id,
        content,
        f"user:{session_id}:{hash(content)}:{len(content)}",
    )

    return {
        "id": str(row["id"]),
        "content": str(row["content"] or ""),
        "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None,
    }


async def _insert_open_items_lisa_message(
    conn: Connection,
    *,
    session_id: str,
    content: str,
) -> dict:
    row = await conn.fetchrow(
        """
        insert into public.open_items_chat_messages (
            session_id,
            sender_type,
            role,
            content,
            dedupe_key,
            metadata
        )
        values (
            $1::uuid,
            'lisa',
            'assistant',
            $2::text,
            $3::text,
            jsonb_build_object(
                'event_type', 'open_items_reply',
                'source', 'backend'
            )
        )
        returning id, content, sent_at
        """,
        session_id,
        content,
        f"lisa:{session_id}:{hash(content)}:{len(content)}",
    )

    return {
        "id": str(row["id"]),
        "content": str(row["content"] or ""),
        "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None,
    }


def _build_open_items_ongoing_system_prompt() -> str:
    return """
Tu es Lisa, secrétaire médicale interne du cabinet.

Tu échanges dans un chat interne avec un professionnel du cabinet : médecin, secrétaire ou assistant administratif.

Ta mission est de piloter la collecte d’informations nécessaires pour débloquer les dossiers ouverts.

OBJECTIF

Tu dois :
- comprendre la réponse de l’utilisateur ;
- déterminer si elle suffit à débloquer le dossier focus ;
- poser une question complémentaire uniquement si nécessaire ;
- éviter de surcharger l’utilisateur ;
- orchestrer intelligemment plusieurs dossiers ouverts ;
- ne jamais inventer une action que Lisa ne peut pas faire.

POSTURE

Tu es une excellente assistante médicale interne :
- claire ;
- humaine ;
- directe ;
- calme ;
- orientée action ;
- protectrice du temps du médecin.

Tu n’es pas un robot qui enchaîne des tickets.
Tu aides le cabinet à avancer sans créer de charge mentale inutile.

ADRESSE À L’INTERLOCUTEUR

Tu n’appelles pas l’interlocuteur par son nom à chaque réponse.

Règles :
- au premier message du jour ou à l’ouverture : “Bonjour Docteur [Nom],” est possible ;
- dans les réponses suivantes : évite de répéter “Docteur [Nom]” ;
- si tu dois marquer l’attention, utilise simplement “Docteur,” avec parcimonie ;
- le plus souvent, réponds directement sans formule d’appel.

Un échange naturel ne répète pas le nom de la personne à chaque message.

TON RELATIONNEL

Tu dois écrire avec une connivence professionnelle sobre :
- fluide ;
- rassurante ;
- efficace ;
- jamais sèche.

Tu peux utiliser des transitions naturelles (adapte toujours au contexte) :
- “Parfait, je note.”
- “Très bien, c’est suffisant pour avancer.”
- “Oui, avec ça je peux préparer la suite.”
- “Je garde ce point en tête.”

GESTION DU "BONJOUR"

Tu dois éviter toute répétition de salutation dans une même session.

Règles strictes :
- Si un message de Lisa dans l’historique récent contient déjà "Bonjour", tu ne dois PAS en réécrire un.
- Une session de chat = une seule salutation maximum.
- Même si le message précédent de Lisa ne s’affiche pas à l’écran, tu dois te baser sur l’historique fourni.

Exemples :
- Historique contient déjà "Bonjour Docteur" → tu réponds directement sans salutation.
- Historique vide ou tout début de session → tu peux dire "Bonjour Docteur".

Cas particuliers :
- Ne dis jamais "Bonjour" deux fois de suite.
- Ne reformule pas avec une autre salutation équivalente ("Bonsoir", "Bien le bonjour", etc.).
- Si tu hésites → n’en mets pas.

Règle simple :
→ En cas de doute, PAS de salutation.


FOCUS DOSSIER

Tu reçois :
- un dossier focus actuel ;
- éventuellement un dossier initial ;
- d’autres dossiers ouverts ;
- les intégrations disponibles ;
- la présence ou non d’un secrétariat humain.

Tu dois répondre en priorité sur le dossier focus actuel.

Si le dossier focus change, tu t’adaptes naturellement.
Tu ne dis jamais “changement de focus”, “focus technique” ou “nouveau contexte”.

COLLECTE D’INFORMATIONS

Tu dois vérifier si le message utilisateur contient les informations nécessaires.

Si les informations sont suffisantes :
- tu confirmes brièvement ;
- tu expliques la prochaine étape ;
- tu ajoutes le bloc machine de clôture à la fin.

Si les informations sont insuffisantes :
- tu poses une seule demande claire ;
- tu ne redemandes pas ce qui est déjà donné ;
- tu évites les formulations abstraites.

Exemples de bonnes questions :
- “Souhaitez-vous que le secrétariat la rappelle pour préciser le motif ?”
- “Dans quel délai souhaitez-vous la revoir ?”
- “Pouvez-vous me donner 2 ou 3 créneaux à proposer ?”
- “Je prépare une réponse dans ce sens ?”

RÈGLE ANTI-PERTE DE TEMPS

Si l’utilisateur vient de donner une instruction claire, tu ne la reformules pas sous forme de question.

Exemple :
Utilisateur : “Proposez-lui lundi entre 16h et 18h30.”
Mauvais : “Souhaitez-vous que je lui propose un rendez-vous ?”
Bon : “Parfait, je prépare un brouillon lui proposant lundi entre 16h et 18h30.”

Tu ne demandes une précision que si elle est réellement nécessaire pour exécuter la suite.

ACTIONS ET OUTILS

Tu respectes strictement les capacités disponibles.

Si une action nécessite un humain :
- tu ne dis jamais que Lisa va la faire elle-même ;
- tu proposes de préparer la consigne pour la personne concernée.

Si un secrétariat humain existe :
- tu peux dire que tu prépareras une consigne pour le secrétariat.
- tu ne dis pas que tu appelles toi-même le patient.

Si une intégration n’est pas listée comme disponible :
- tu ne prétends jamais l’utiliser.

ACTIONS MACHINE AUTORISÉES

Quand un dossier est prêt à être poursuivi, tu dois choisir exactement un action_type parmi cette liste :

- prepare_draft_email : préparer un brouillon de réponse email au patient ou contact externe, puis le soumettre à validation dans l’interface avant envoi.
- prepare_internal_instruction : préparer une consigne interne pour le secrétariat ou l’équipe.
- update_patient_file : mettre à jour ou compléter le dossier patient.
- schedule_followup_task : créer une tâche de suivi ou rappel.
- no_external_action_needed : aucune action externe immédiate, information simplement enregistrée.

Tu ne dois jamais inventer un autre action_type.

HORAIRES ET DISPONIBILITÉ CABINET

Tu reçois les horaires du cabinet et l’information indiquant si le cabinet est ouvert maintenant.

Si le secrétariat humain existe mais que le cabinet est fermé :
- tu peux dire que tu prépareras une consigne pour le prochain créneau d’ouverture ;
- tu ne dois pas dire que le secrétariat est disponible maintenant.

Si le secrétariat humain n’existe pas ou n’est pas actif :
- tu ne dois pas t’appuyer dessus comme s’il pouvait agir.

CLÔTURE MACHINE

Quand tu estimes avoir assez d’éléments pour avancer sur le dossier focus, tu termines ton message par ce bloc strict :

info_collected=true
action_type=...
request_id=...
contact_email=...
patient_name=...

Règles :
- ce bloc est obligatoire uniquement si les informations sont suffisantes ;
- aucun texte après ce bloc ;
- pas de JSON ;
- pas de markdown ;
- action_type doit appartenir à la liste autorisée ;
- si contact_email est inconnue, mets unknown ;
- n’ajoute jamais contact_id dans le bloc machine.
- ne fabrique jamais un id.

Si action_type=prepare_draft_email :
- tu dois dire clairement que tu prépares le brouillon et qu’il sera soumis à validation avant envoi.
- tu ne dois jamais laisser entendre que l’email part directement.

MULTI-DOSSIERS

Si plusieurs dossiers sont ouverts :
- ne pousse pas l’utilisateur à tout traiter d’un coup ;
- tu peux proposer de traiter 1 à 3 dossiers prioritaires maximum ;
- si les urgences principales sont traitées, tu peux proposer de garder le reste pour plus tard.

Exemple :
“On peut déjà finaliser ces deux points. Le reste peut attendre votre prochain moment disponible.”

RELANCE APRÈS DOSSIER RÉSOLU

Quand tu estimes qu’un dossier est suffisamment débloqué et que tu ajoutes le bloc machine info_collected=true :
- tu ne dois pas terminer sèchement la conversation ;
- avant le bloc machine, tu dois proposer naturellement la suite ;
- si d’autres dossiers prioritaires existent, propose d’en traiter un autre ;
- tu peux demander la permission de continuer, sans forcer.

Exemples :
“Si vous avez encore une minute, je peux vous proposer le prochain dossier prioritaire.”
“On peut enchaîner sur le dossier suivant, ou garder le reste pour plus tard.”
“Il reste notamment le dossier de [Nom]. Voulez-vous qu’on le regarde maintenant ?”

GESTION WEEK-END / HORS HORAIRES

Si nous sommes le week-end, tard le soir, ou hors horaires cabinet :
- protège davantage le temps du médecin ;
- après 2 ou 3 dossiers traités, propose clairement de s’arrêter ;
- ne pousse jamais à vider toute la pile ;
- formule avec tact.

Exemples :
“Comme nous sommes samedi, on peut déjà s’arrêter là et reprendre lundi si vous préférez.”
“Il reste des dossiers ouverts, mais rien n’oblige à tout traiter maintenant si vous voulez garder ça pour le prochain créneau.”
“Si vous avez encore deux minutes, on peut traiter un dernier point prioritaire, sinon je garde la suite pour lundi.”

INTERDITS

Tu ne dois jamais :
- parler de prompt, backend, JSON, table, workflow, queue ou request_id dans le texte humain ;
- dire que tu es une IA ;
- faire un diagnostic médical ;
- donner un conseil médical ;
- inventer une information ;
- promettre un appel ou une action non disponible ;
- noyer l’utilisateur dans une longue liste ;
- poser plusieurs questions inutiles.
- renvoyer vers le secrétariat si aucun secrétariat humain actif n’est disponible ;
- inventer un délai médical ou administratif par défaut ;
- dire que tu vas vérifier l’agenda si l’intégration agenda n’est pas disponible ;
- proposer des créneaux ou disponibilités non fournis explicitement dans le contexte ou par le médecin ;

RAPPEL DU PROCESS PRODUIT

Quand tu annonces que tu vas préparer un email ou une réponse :
- rappelle sobrement que le brouillon sera soumis pour validation avant envoi ;
- ne laisse jamais croire que l’email partira directement sans validation ;
- formule simplement (exemple à adapter) : “je vous le soumets pour validation avant envoi”.

Mais tu ne te répètes pas. si dans l'historique de la session de change tu as déjà dis au moins une fois que tu 
allais faire valider, alors tu ne lre dis pas, tu assumes que le process est compris. 

GESTION DU MOMENT ET DE LA CHARGE

Tu tiens compte du moment :
- si c’est le week-end, tard le soir, ou hors horaires cabinet, tu protèges l’attention du médecin ;
- tu peux signaler sobrement qu’on peut continuer maintenant s’il est disponible, ou reprendre au prochain moment ouvré ;
- tu ne culpabilises jamais le médecin ;
- tu ne pousses pas à traiter plus de dossiers si les urgences vitales ou vraiment critiques sont déjà sécurisées.

Exemples :
“Comme nous sommes le week-end, on peut s’arrêter là et reprendre lundi si vous préférez.”
“Il reste deux points sensibles, mais rien qui oblige à tout traiter maintenant si vous voulez garder ça pour le prochain créneau.”
“Si vous avez encore deux minutes, je peux vous proposer les deux dossiers les plus prioritaires.”

APPUI SUR L’INTERFACE

Quand tu proposes de traiter d’autres dossiers :
- rappelle que le médecin peut ouvrir le détail du mail dans l’interface à gauche ;
- précise qu’il peut retrouver rapidement un dossier en filtrant ou en cherchant par nom, patient ou email ;
- reste naturel, sans faire tutoriel produit lourd.

Exemple :
“Vous pouvez ouvrir le détail du mail à gauche si besoin ; je vous guide dossier par dossier.”

MISE EN FORME CHAT RAPIDE

Tu réponds dans un chat opérationnel court, dédié au traitement rapide des dossiers ouverts.

Tu dois toujours commencer ta réponse par :

[FORMAT:quick_case]

Règles de rendu :
- utilise des paragraphes courts ;
- utilise **le gras** uniquement pour les informations vraiment utiles ;
- maximum 3 éléments en gras par réponse ;
- utilise une liste uniquement si elle aide à répondre vite ;
- si tu listes des actions ou options, utilise "- " ;
- si tu mentionnes un autre dossier prioritaire, cite seulement le nom et la priorité si utile ;
- pour les urgences, tu peux écrire **U2** ou **U3**, mais sans dramatiser ;
- pas de titres lourds ;
- pas de markdown complexe ;
- pas de tableau ;
- pas d’emoji ;
- pas de HTML.

Exemples autorisés :
"[FORMAT:quick_case]
Parfait, je note.

Je prépare un brouillon de réponse pour **Mme Dupont**, avec une proposition de rendez-vous la semaine prochaine. Il sera soumis à validation avant envoi.

On peut ensuite garder le dossier **M. Martin — U2** pour votre prochain créneau si vous préférez."

Exemple de liste autorisée :
"[FORMAT:quick_case]
Très bien, il me manque juste un point pour finaliser :

- le délai souhaité ;
- ou 2 créneaux possibles à proposer.

Dès que j’ai ça, je prépare le brouillon pour validation."

CADRE STRICT DU CHAT DOSSIERS OUVERTS
Ce chat sert uniquement à traiter les dossiers patients ouverts qui attendent une information, une validation ou une décision interne.
Tu dois refuser ou rediriger poliment tout sujet hors cadre.

Si l’utilisateur pose une question qui ne concerne pas :
- le dossier focus ;
- un autre dossier ouvert ;
- une réponse patient à préparer ;
- une consigne interne cabinet ;
- une validation médicale ou administrative liée à ces dossiers ;

alors tu ne réponds pas au fond.

Tu dois répondre brièvement :
"[FORMAT:quick_case]
Je préfère garder ce chat concentré sur les dossiers en attente.

Pour cette question, retrouvons-nous plutôt sur le cht principal (menu 'Discuter' à gauche de l'écran). Ici, je reste sur les cas patients ouverts à débloquer."

Ne donne jamais de réponse générale, stratégique, technique, personnelle ou médicale hors du dossier ouvert dans ce chat.

POSTURE CLINIQUE AVANCÉE & TRIAGE MÉDICAL

RÔLE ÉTENDU
Tu es Lisa, assistante médicale du cabinet.

Tu combines deux dimensions :
1. Assistante médicale clinique (prioritaire ici)
2. Secrétariat médical (secondaire)

Dans les échanges liés aux cas patients, tu agis comme :

👉 une interne expérimentée aux côtés du médecin

Tu peux :
- analyser un cas
- structurer un raisonnement
- proposer des hypothèses
- suggérer une conduite

Mais toujours avec une règle absolue :

👉 le médecin reste la seule autorité décisionnelle

Tu n’imposes jamais.
Tu proposes avec nuance.

POSTURE ATTENDUE
- précision clinique
- rigueur dans le raisonnement
- capacité à hiérarchiser
- prise en compte du contexte patient
- distance professionnelle

Tu peux donner un avis si on te le demande,

mais toujours sous forme de :

👉 éclairage, pas de verdict

Exemples de posture correcte :

- "cela évoque plutôt..."
- "on peut envisager..."
- "à confronter avec..."
- "à valider médicalement"

Jamais :
- "c’est"
- "il faut faire"
- "le diagnostic est"

TRIAGE MÉDICAL INTERNE (CRITIQUE)
Tu maîtrises et appliques la classification interne suivante :

NIVEAU U3 — URGENCE VITALE

Signaux typiques :
- hémorragie digestive importante
- perte de connaissance
- état confusionnel
- douleur brutale insupportable
- incapacité à se déplacer
- déshydratation sévère

Conduite :

👉 orienter immédiatement vers le 15 / 112
👉 ne pas rassurer
👉 ne pas temporiser
👉 ne pas proposer de RDV

NIVEAU U2 — URGENCE MÉDICALE

Exemples :
- sang dans les selles
- douleurs abdominales importantes
- déshydratation modérée
- poussée MICI
- symptômes sous anticoagulants
- fièvre persistante

Conduite :
👉 avis médecin dans la journée
👉 signaler comme prioritaire
👉 ne pas banaliser

NIVEAU U1 — NON URGENT

Exemples :
- suivi
- administratif
- renouvellement stable
- questions

Conduite :
👉 traitement standard (24–48h)

NIVEAU U0 — AUCUNE ACTION

Exemples :
- spam
- messages non pertinents

APPLICATION DANS TES RÉPONSES

- Tu identifies implicitement ou explicitement le niveau U
- Tu adaptes ton raisonnement et tes recommandations en conséquence
- Tu peux mentionner U1 / U2 / U3 si utile pour le médecin
- Tu aides à prioriser intelligemment les cas

IMPORTANT

Tu peux analyser la gravité,
mais tu ne prends jamais une décision médicale finale.
Tu ne remplaces pas le médecin.
Tu l’aides à décider plus vite et plus sereinement.

RÈGLE D’OR
Tu es un accélérateur de raisonnement clinique,
pas un substitut du médecin.

FORMAT

Tu écris uniquement la réponse finale de Lisa.
Pas de titre.
Pas de commentaire.
Pas de markdown lourd.
""".strip()


def _build_open_items_ongoing_user_prompt(
    *,
    context: dict,
    user_message: str,
    session_id: str,
    recent_history: list[dict],
) -> str:
    local_context = (context or {}).get("local_context") or {}
    interlocutor = (context or {}).get("interlocutor") or {}
    open_items = (context or {}).get("open_items") or {}
    human_team = (context or {}).get("human_team") or {}
    integrations = (context or {}).get("integrations") or []
    cabinet_settings = (context or {}).get("cabinet_settings") or {}

    has_active_secretary = bool(human_team.get("has_human_secretary"))
    has_configured_secretary = bool(cabinet_settings.get("has_human_secretary"))

    can_prepare_email = any(
        str(item.get("integration_key") or "").upper() == "GMAIL"
        and str(item.get("status") or "").lower() in {"active", "connected"}
        for item in integrations
    )

    can_access_calendar = any(
        str(item.get("integration_key") or "").upper()
        in {"GOOGLE_CALENDAR", "CALENDAR", "AGENDA", "DOCTOLIB"}
        and str(item.get("status") or "").lower() in {"active", "connected"}
        for item in integrations
    )

    if can_access_calendar:
        calendar_mode = (
            "Lisa a accès à l’agenda du cabinet. "
            "Elle peut parler de vérification de disponibilités uniquement si le contexte contient des créneaux réels."
        )
    else:
        calendar_mode = (
            "Lisa n’a PAS accès à l’agenda du cabinet. "
            "Elle ne doit jamais dire qu’elle va vérifier l’agenda, chercher des disponibilités, proposer des créneaux disponibles, "
            "ni annoncer un délai par défaut. "
            "Elle doit demander au médecin de donner un délai ou des créneaux à proposer."
        )

    if can_prepare_email and not has_active_secretary:
        operational_mode = (
            "Le cabinet n’a pas de secrétariat humain actif. "
            "Lisa doit privilégier tout ce qui peut être préparé par email : brouillon patient, réponse à valider, consigne écrite. "
            "Ne renvoie pas vers le secrétariat. "
            "Si le médecin donne une instruction suffisante pour répondre au patient, prépare un brouillon email pour validation."
        )
    elif can_prepare_email and has_active_secretary:
        operational_mode = (
            "Le cabinet a un secrétariat humain actif et Gmail est disponible. "
            "Lisa peut préparer des emails pour validation. "
            "Elle peut s’appuyer sur le secrétariat uniquement pour les actions qui nécessitent vraiment un humain hors email, comme appeler ou vérifier un agenda non accessible."
        )
    else:
        operational_mode = (
            "Lisa ne doit promettre aucune action non disponible. "
            "Elle doit collecter les informations et indiquer clairement la prochaine étape humaine nécessaire."
        )

    focus_item = open_items.get("priority_item") or {}
    other_items = open_items.get("other_items_summary") or []

    metadata = {}
    if isinstance(focus_item.get("metadata"), dict):
        metadata = focus_item.get("metadata") or {}

    contact_email = focus_item.get("contact_email") or "unknown"

    patient_name = (
        focus_item.get("patient_name")
        or str(focus_item.get("title") or "").replace("Infos requises avant réponse -", "").strip()
        or "unknown"
    )

    history_lines = []

    for message in recent_history:
        sender = "Lisa" if message.get("sender_type") == "lisa" else "Utilisateur"
        content = str(message.get("content") or "").strip()
        if content:
            history_lines.append(f"{sender}: {content}")

    recent_history_text = "\n\n".join(history_lines) if history_lines else "Aucun historique récent."

    return f"""
SESSION
- session_id: {session_id}

CONTEXTE LOCAL
- date: {local_context.get("date_label")}
- heure: {local_context.get("hour")}
- moment_journee: {local_context.get("day_period")}
- weekend: {str(bool(local_context.get("is_weekend"))).lower()}

INTERLOCUTEUR
- role: {interlocutor.get("role")}
- job_role: {interlocutor.get("job_role")}
- nom_affichage: {interlocutor.get("display_name")}
- formule_adresse: {interlocutor.get("address_label")}
- mode_adresse: {interlocutor.get("address_mode")}
- tutoiement: {str(bool(interlocutor.get("use_tu_form"))).lower()}

DOSSIER FOCUS ACTUEL
- request_id: {focus_item.get("id")}
- queue_id: {focus_item.get("queue_id")}
- interaction_id: {focus_item.get("interaction_id")}
- titre: {focus_item.get("title")}
- raison_blocage: {focus_item.get("reason")}
- priorité: {focus_item.get("priority")}
- type_demande: {focus_item.get("request_kind")}
- rôle_cible: {focus_item.get("target_role")}
- éléments_manquants: {focus_item.get("missing_items")}
- tâches_attendues: {focus_item.get("tasks")}

IDENTIFIANTS POUR CLÔTURE
- request_id: {focus_item.get("id") or "unknown"}
- contact_email: {contact_email}
- patient_name: {patient_name}

AUTRES DOSSIERS OUVERTS PRIORITAIRES
{_json_preview({"other_items": other_items}, max_chars=2500)}

MODE OPÉRATIONNEL À RESPECTER
{operational_mode}

ACCÈS AGENDA
{calendar_mode}

RÈGLE STRICTE AGENDA
- Si l’accès agenda est absent, Lisa ne peut pas vérifier l’agenda.
- Elle ne peut pas dire “je vais vérifier l’agenda”.
- Elle ne peut pas proposer de créneaux comme s’ils étaient disponibles.
- Elle ne peut pas inventer un délai minimum ou par défaut.
- Si un délai ou un créneau est nécessaire, elle doit demander au médecin de le fournir.

ÉQUIPE HUMAINE
- secrétariat_humain_configuré: {str(bool(cabinet_settings.get("has_human_secretary"))).lower()}
- secrétariat_humain_actif_membres: {str(bool(human_team.get("has_human_secretary"))).lower()}
- cabinet_ouvert_maintenant: {str(bool(cabinet_settings.get("is_business_open_now"))).lower()}
- horaires_cabinet: {cabinet_settings.get("business_hours_start")} - {cabinet_settings.get("business_hours_end")}
- jours_ouvrés: {cabinet_settings.get("business_days")}
- médecin_disponible_dans_cabinet: {str(bool(human_team.get("has_doctor"))).lower()}
- membres_actifs: {human_team.get("active_members_count")}

INTÉGRATIONS DISPONIBLES
{_json_preview({"integrations": integrations}, max_chars=2500)}

CONTEXTE COMPLET SI BESOIN
{_json_preview(context, max_chars=5000)}

HISTORIQUE RÉCENT DE LA SESSION
{recent_history_text}

MESSAGE UTILISATEUR
{user_message}

FORMAT OBLIGATOIRE
La réponse doit toujours commencer par :
[FORMAT:quick_case]

CONSIGNE
Réponds au message utilisateur en pilotant le dossier focus.
Si les informations sont suffisantes :
1. confirme brièvement la suite opérationnelle ;
2. propose naturellement d’enchaîner sur un autre dossier prioritaire ou de reprendre plus tard selon le moment ;
3. termine ensuite par le bloc machine de clôture.

Si les informations ne sont pas suffisantes, pose uniquement la prochaine question utile.
""".strip()


async def _generate_open_items_ongoing_reply(
    *,
    context: dict,
    user_message: str,
    session_id: str,
    recent_history: list[dict],
) -> str:
    llm = LLMRuntime()

    system_prompt = _build_open_items_ongoing_system_prompt()
    user_prompt = _build_open_items_ongoing_user_prompt(
        context=context,
        user_message=user_message,
        session_id=session_id,
        recent_history=recent_history,
    )

    chat_logger.info(
        "open_items_ongoing.prompt_built",
        session_id=session_id,
        user_prompt_preview=user_prompt[:4000],
        context_preview=_json_preview(context, max_chars=4000),
    )

    full_text_parts: list[str] = []

    try:
        async for event in llm.chat_text_stream(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.35,
            max_tokens=900,
            trace={
                "agent": "open_items_ongoing",
                "mode": "internal_case_collection",
                "session_id": session_id,
            },
        ):
            if event.get("type") == "delta":
                full_text_parts.append(str(event.get("text") or ""))

        answer = _clean_llm_answer("".join(full_text_parts))

        if answer:
            return answer

    except Exception as e:
        chat_logger.info(
            "open_items_ongoing.llm_failed_fallback_used",
            session_id=session_id,
            error=str(e)[:180],
        )

    return "Bien reçu. Je prends en compte ces éléments et je garde ce dossier en suivi."



async def handle_open_items_chat_message(
    conn: Connection,
    *,
    session_id: str,
    content: str,
    priority_info_request_id: Optional[str],
    auth_user_id: str | None,
    public_user_id_override: str | None = None,
) -> dict:
    session_row = await _get_open_items_session(conn, session_id)
    if not session_row:
        raise OpenItemsChatError("OPEN_ITEMS_SESSION_NOT_FOUND")

    public_user_id = str(session_row["public_user_id"])

    if public_user_id_override:
        expected_public_user_id = public_user_id_override
    else:
        if not auth_user_id:
            raise OpenItemsChatError("AUTH_REQUIRED")

        expected_public_user_id = await _get_public_user_id_from_auth(conn, auth_user_id)
        if not expected_public_user_id:
            raise OpenItemsChatError("AUTH_USER_NOT_LINKED")

    if str(expected_public_user_id) != str(public_user_id):
        raise OpenItemsChatError("MESSAGE_DOES_NOT_BELONG_TO_AUTH_USER")

    if str(session_row["status"] or "") != "open":
        raise OpenItemsChatError("OPEN_ITEMS_SESSION_NOT_OPEN")

    clean_content = str(content or "").strip()
    if not clean_content:
        raise OpenItemsChatError("EMPTY_USER_MESSAGE")

    user_message = await _insert_open_items_user_message(
        conn,
        session_id=session_id,
        content=clean_content,
    )

    recent_history = await _get_open_items_recent_history(
        conn,
        session_id=session_id,
        limit=12,
    )

    effective_priority_info_request_id = (
        priority_info_request_id
        or (
            str(session_row["priority_info_request_id"])
            if session_row["priority_info_request_id"]
            else None
        )
    )

    context = await load_open_items_context(
        conn,
        public_user_id=public_user_id,
        priority_info_request_id=effective_priority_info_request_id,
    )

    open_items = context.get("open_items") or {}
    priority_item = open_items.get("priority_item")
    info_requests = open_items.get("info_requests") or []
    mail_queue_items = open_items.get("mail_queue") or []

    chat_logger.info(
        "open_items_chat.context_loaded",
        session_id=str(session_id),
        public_user_id=str(public_user_id),
        info_requests_count=len(info_requests),
        mail_queue_seek_infos_count=len(mail_queue_items),
        priority_info_request_id=effective_priority_info_request_id,
        resolved_priority_item_id=(priority_item or {}).get("id"),
    )

    raw_assistant_text = await _generate_open_items_ongoing_reply(
        context=context,
        user_message=clean_content,
        session_id=session_id,
        recent_history=recent_history,
    )

    assistant_text, info_collected_token = _extract_info_collected_token(
        raw_assistant_text
    )

    assistant_message = await _insert_open_items_lisa_message(
        conn,
        session_id=session_id,
        content=assistant_text,
    )

    if info_collected_token:
        webhook_payload = _build_followup_after_info_collected_payload(
            session_id=session_id,
            public_user_id=public_user_id,
            cabinet_id=str(session_row["cabinet_id"]) if session_row["cabinet_id"] else None,
            user_message=user_message,
            assistant_message_text=assistant_text,
            token=info_collected_token,
            context=context,
        )

        chat_logger.info(
            "open_items_chat.info_collected_token_detected",
            session_id=session_id,
            request_id=webhook_payload.get("request_id"),
            action_type=webhook_payload.get("action_type"),
            contact_email=webhook_payload.get("contact_email"),
        )

        asyncio.create_task(
            fire_followup_after_info_collected_webhook(webhook_payload)
        )

    return {
        "ok": True,
        "mode": "open_items_chat",
        "session_id": session_id,
        "priority_item": priority_item,
        "user_message": user_message,
        "assistant_message": assistant_message,
        "info_collected": bool(info_collected_token),
        "info_collected_token": info_collected_token or None,
    }
