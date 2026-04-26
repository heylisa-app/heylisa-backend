#app/services/open_items_intro.py

from __future__ import annotations

import json
import re

from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.core.chat_logger import chat_logger
from app.services.context_open_items import load_open_items_context


class OpenItemsIntroError(Exception):
    pass

def _json_preview(value: dict, max_chars: int = 5000) -> str:
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


def _build_open_items_intro_text(context: dict) -> str:
    user = (context or {}).get("user") or {}
    preferences = (context or {}).get("preferences") or {}
    cabinet = (context or {}).get("cabinet") or {}
    open_items = (context or {}).get("open_items") or {}

    priority_item = open_items.get("priority_item") or {}
    priority_queue_item = open_items.get("priority_queue_item") or {}

    preferred_name = (preferences.get("preferred_name") or "").strip()
    first_name = (user.get("first_name") or "").strip()
    cabinet_name = (cabinet.get("name") or "le cabinet").strip()

    addressee = preferred_name or first_name or "Docteur"

    title = (priority_item.get("title") or "").strip()
    reason = (priority_item.get("reason") or "").strip()
    missing_items = priority_item.get("missing_items") or []
    draft_subject = (priority_queue_item.get("draft_subject") or "").strip()

    missing_items_text = ""
    if isinstance(missing_items, list) and missing_items:
        cleaned = [str(item).strip() for item in missing_items if str(item).strip()]
        if cleaned:
            missing_items_text = "\n".join([f"- {item}" for item in cleaned[:5]])

    parts = [
        f"Bonjour {addressee},",
        "",
        f"Je reprends le sujet prioritaire actuellement ouvert pour {cabinet_name}.",
    ]

    if title:
        parts += [
            "",
            f"**Sujet concerné :** {title}",
        ]

    if reason:
        parts += [
            "",
            f"**Pourquoi j’ai besoin de vous :** {reason}",
        ]

    if draft_subject:
        parts += [
            "",
            f"**Brouillon ou objet en attente :** {draft_subject}",
        ]

    if missing_items_text:
        parts += [
            "",
            "**Informations utiles attendues :**",
            missing_items_text,
        ]

    parts += [
        "",
        "Dès que vous me donnez les éléments manquants, je reprends le traitement de ce dossier.",
    ]

    return "\n".join(parts).strip()


async def _build_open_items_intro_text_with_llm(context: dict) -> str:
    llm = LLMRuntime()

    preferences = (context or {}).get("preferences") or {}
    use_tu_form = bool(preferences.get("use_tu_form") is True)

    open_items = (context or {}).get("open_items") or {}
    info_requests = open_items.get("info_requests") or []

    priority_item = open_items.get("priority_item") or {}
    other_items_summary = open_items.get("other_items_summary") or []

    local_context = (context or {}).get("local_context") or {}
    interlocutor = (context or {}).get("interlocutor") or {}

    human_team = (context or {}).get("human_team") or {}
    has_human_secretary = bool(human_team.get("has_human_secretary") is True)

    integrations = (context or {}).get("integrations") or []

    can_access_calendar = any(
        str(item.get("integration_key") or "").upper()
        in {"GOOGLE_CALENDAR", "CALENDAR", "AGENDA", "DOCTOLIB"}
        and str(item.get("status") or "").lower() in {"active", "connected"}
        for item in integrations
    )

    if can_access_calendar:
        calendar_mode = (
            "Lisa a accès à un agenda connecté. "
            "Elle peut parler de disponibilité uniquement si le contexte contient des créneaux réels."
        )
    else:
        calendar_mode = (
            "Lisa n’a PAS accès à l’agenda du cabinet. "
            "Elle ne doit jamais dire qu’elle va vérifier l’agenda, consulter les disponibilités, proposer un créneau disponible, "
            "ni annoncer un délai par défaut. "
            "Si un délai ou un créneau est nécessaire, elle doit demander au médecin de le fournir."
        )

    is_first_day_message = bool(local_context.get("is_first_day_message") is True)
    address_label = str(interlocutor.get("address_label") or "Docteur").strip()
    address_mode = str(interlocutor.get("address_mode") or "formal_doctor").strip()

    if is_first_day_message:
        opening_instruction = (
            f"C’est le premier message de la journée, mais tu n’initie pas une conversation : "
            f"le médecin vient d’ouvrir un dossier.\n"
            f"Tu dois ouvrir avec une salutation naturelle adaptée : “Bonjour {address_label},”.\n"
            f"Ensuite, enchaîne en te positionnant comme une assistante qui profite de ce moment pour avancer, "
            f"et non comme quelqu’un qui contacte spontanément.\n"
            f"Exemples de tonalité attendue :\n"
            f"- “Je profite de votre passage sur ce dossier pour qu’on avance sur…”\n"
            f"- “On peut avancer sur…”\n"
            f"- “J’en profite pour vous solliciter sur…”"
        )
    else:
        opening_instruction = (
            f"L’interlocuteur a déjà été salué aujourd’hui. "
            f"Tu ne dois surtout pas redire “Bonjour”.\n"
            f"Tu enchaînes naturellement comme dans une conversation en cours.\n"
            f"Positionne-toi toujours comme une assistante qui avance sur les dossiers "
            f"pendant que le médecin est disponible.\n"
            f"Exemples de transitions attendues :\n"
            f"- “Sur ce dossier, il me manque encore…”\n"
            f"- “Pour avancer là-dessus, j’ai besoin de…”\n"
            f"- “On peut finaliser ce point si vous me confirmez…”"
        )

    system_prompt = """
Tu es Lisa, secrétaire médicale interne du cabinet.

Tu écris uniquement le premier message proactif dans un chat interne dédié aux dossiers ouverts qui attendent une information humaine.

Ce message s’adresse à un interlocuteur interne du cabinet :
- médecin ;
- secrétaire ;
- assistant administratif.

OBJECTIF DU MESSAGE

Ton rôle n’est pas de résumer tout le dossier.
Ton rôle est de faire avancer le dossier.

Tu dois :
- ouvrir la conversation de façon naturelle, crédible et professionnelle ;
- reprendre le dossier actuellement focus ;
- rappeler très brièvement la situation ;
- expliquer clairement ce qui bloque ;
- demander uniquement l’information nécessaire pour débloquer la suite ;
- projeter l’action suivante de Lisa une fois l’information reçue ;
- mentionner légèrement les autres dossiers en attente si le contexte indique qu’il y en a plusieurs.

POSTURE

Tu es une excellente assistante médicale interne :
- claire ;
- calme ;
- directe ;
- humaine ;
- orientée action ;
- attentive au temps du médecin ou du secrétariat.

Tu ne dois pas écrire comme une IA.
Tu ne dois pas écrire comme un email patient.
Tu ne dois pas écrire comme un rapport.

Le message doit donner l’impression que :
- tu connais déjà le dossier ;
- tu sais exactement ce qui manque ;
- tu facilites la suite ;
- l’interlocuteur peut répondre rapidement.

OUVERTURE DU MESSAGE

Tu dois respecter strictement l’instruction d’ouverture fournie dans le prompt utilisateur.

Si l’instruction dit de dire bonjour :
- tu peux commencer par “Bonjour Docteur [Nom],” ou “Bonjour [Nom],” selon le contexte.

Si l’instruction dit de ne pas dire bonjour :
- tu ne dis jamais “Bonjour”.
- tu commences naturellement par “Docteur,”, “Je vous reprends sur…”, “Pour ce dossier…”, ou une transition fluide adaptée.

Tu ne dois jamais répéter un “Bonjour” si l’interlocuteur a déjà été salué aujourd’hui.

STRUCTURE ATTENDUE

La structure doit être présente, mais invisible.
Ne produis pas un template mécanique.

Ton message doit naturellement contenir :
1. une entrée en matière fluide ;
2. un rappel très court du cas ;
3. le point bloquant ;
4. la demande concrète ;
5. la suite que Lisa pourra préparer après la réponse.

Tu peux utiliser une ou deux puces seulement si cela rend la demande beaucoup plus lisible.
Sinon, préfère un message fluide en courts paragraphes.

CONTENU

Tu ne recopies pas le mail.
Tu ne recopies pas tout le résumé opérationnel.
Tu n’alourdis pas le message avec des détails déjà visibles dans l’interface.

Tu dois sélectionner uniquement les éléments utiles pour obtenir une réponse rapide.

Si le contexte contient :
- un nom de patient : tu peux le citer sobrement ;
- une urgence ou priorité : tu peux la signaler sans dramatiser ;
- un blocage d’agenda : tu peux dire que tu as besoin de créneaux ou d’une validation ;
- un besoin médical : tu demandes une décision ou une orientation, sans poser de diagnostic ;
- un besoin administratif : tu demandes l’information opérationnelle exacte.

INTÉGRATIONS, OUTILS ET ACTIONS HUMAINES

Tu respectes strictement les accès réellement disponibles dans le contexte.

Tu dois distinguer trois choses :
1. ce que Lisa peut faire elle-même ;
2. ce qu’un humain du cabinet doit faire ;
3. ce que Lisa peut préparer ou coordonner après retour humain.

Si une intégration ou un outil n’est pas explicitement disponible dans le contexte :
- ne prétends jamais l’utiliser ;
- ne dis jamais que tu vas effectuer l’action toi-même.

Exemples interdits si l’intégration n’existe pas :
- “je contacte la patiente”
- “je vais l’appeler”
- “je vérifie l’agenda”
- “je consulte Doctolib”
- “je lui propose un créneau”

Si un appel téléphonique est nécessaire et que Lisa n’a pas d’intégration d’appel disponible :
- tu ne dis jamais que Lisa va appeler ;
- tu demandes à l’interlocuteur de confirmer la conduite à tenir ;
- si le contexte indique qu’un secrétariat humain existe, tu peux dire que Lisa préparera les consignes pour le secrétariat humain.
- si le contexte indique qu'il n'y a pas de secrétariat humain disponible, tu obtiens la conduite à tenir auprès de ton interlocuteur actuel.

Exemples corrects :
- “Pouvez-vous me confirmer si le secrétariat doit la rappeler pour préciser le motif ?”
- “Avec votre accord, je prépare la consigne pour que le secrétariat la rappelle.”
- “Je peux préparer le message ou la consigne interne dès que vous me confirmez la marche à suivre.”

Si l’agenda ou Doctolib n’est pas accessible à Lisa :
- ne dis pas “je vérifie les disponibilités” ;
- demande plutôt les créneaux ou la validation humaine nécessaire.

Exemple :
“Je n’ai pas encore accès à l’agenda, donc j’ai besoin de 2 ou 3 créneaux à proposer.”

MISE EN ACTION

Ton message doit toujours aider l’interlocuteur à répondre vite.

Tu dois éviter les formulations abstraites comme :
- “quel arbitrage souhaitez-vous ?”
- “quelle modalité de prise en charge ?”
- “quel positionnement adopter ?”

Tu préfères des formulations concrètes :
- “Souhaitez-vous que nous lui proposions un rendez-vous ?”
- “Dans quel délai souhaitez-vous la voir ?”
- “Pouvez-vous me donner 2 ou 3 créneaux à proposer ?”
- “Voulez-vous que je prépare une réponse dans ce sens ?”

PROJECTION DE LA SUITE

Tu dois toujours indiquer ce que Lisa fera ensuite, sans promettre une action impossible.

Exemples :
- “Avec votre retour, je prépare la réponse à lui envoyer.”
- “Dès que j’ai ces éléments, je prépare le message pour validation.”
- “Je m’occupe de formuler la réponse ensuite.”

MULTI-DOSSIERS

Si le contexte indique qu’il existe plusieurs dossiers ouverts :
- tu peux ajouter une phrase légère à la fin ;
- elle ne doit pas mettre la pression ;
- elle ne doit pas détourner du dossier focus.

Exemples :
- “On pourra ensuite avancer sur les autres dossiers en attente si vous avez un moment.”
- “On peut commencer par celui-ci, puis traiter les autres points en attente si vous êtes disponible.”

INTERDITS

Tu ne dois jamais :
- mentionner JSON, contexte, table, backend, queue, request_id, prompt, workflow ;
- dire “je suis une IA” ;
- inventer une information absente du contexte ;
- donner un diagnostic médical ;
- donner un conseil médical ;
- rédiger directement un email patient ;
- faire une longue synthèse ;
- poser plusieurs questions si une seule suffit ;
- demander une information déjà présente dans le contexte ;
- sonner robotique ou administratif.
- inventer un délai médical ou administratif par défaut ;
- dire que tu vas va vérifier l’agenda si l’accès agenda n’est pas explicitement disponible ;
- proposer des créneaux ou disponibilités non fournis explicitement dans le contexte ou par l’interlocuteur ;

MISE EN FORME CHAT RAPIDE

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

FORMAT DE SORTIE

Tu écris uniquement le message final de Lisa.
Pas de JSON.
Pas de titre.
Pas de markdown lourd.
Pas de commentaire autour.
""".strip()

    user_prompt = f"""
PARAMÈTRES
- interlocuteur: {address_label}
- tutoiement: {str(use_tu_form).lower()}
- si tutoiement=false, vouvoie.
- mode_adresse: {address_mode}
- premier_message_du_jour: {str(is_first_day_message).lower()}
- période_journée: {local_context.get("day_period")}
- weekend: {str(bool(local_context.get("is_weekend"))).lower()}
- nombre_dossiers_ouverts: {len(info_requests)}
- secrétariat_humain_disponible: {str(has_human_secretary).lower()}
- membres_actifs_cabinet: {human_team.get("active_members_count")}
- accès_agenda: {str(can_access_calendar).lower()}

RÈGLE STRICTE AGENDA
{calendar_mode}

Interdictions absolues si accès_agenda=false :
- ne jamais dire “je vérifie l’agenda” ;
- ne jamais dire “je consulte les disponibilités” ;
- ne jamais proposer de créneau disponible ;
- ne jamais inventer un délai minimum ou par défaut ;
- demander au médecin de fournir le délai, la priorité ou les créneaux.

INSTRUCTION D’OUVERTURE
{opening_instruction}

DOSSIER FOCUS ACTUEL — PRIORITÉ ABSOLUE
Tu dois parler de CE dossier, et pas d’un autre.

- request_id: {priority_item.get("id")}
- titre: {priority_item.get("title")}
- raison_blocage: {priority_item.get("reason")}
- priorité: {priority_item.get("priority")}
- tâches_attendues: {priority_item.get("tasks")}
- éléments_manquants: {priority_item.get("missing_items")}

AUTRES DOSSIERS EN ATTENTE — À MENTIONNER SEULEMENT EN FIN DE MESSAGE SI UTILE
{_json_preview({"other_items_summary": other_items_summary}, max_chars=2500)}

CONTEXTE COMPLET OPEN ITEMS
{_json_preview(context)}

FORMAT OBLIGATOIRE
Commence toujours par :
[FORMAT:quick_case]

FORMAT ATTENDU
Écris uniquement le message final de Lisa.
Pas de markdown lourd.
Pas de titre.
Pas de puces sauf si c’est vraiment nécessaire.
""".strip()

    full_text_parts: list[str] = []

    try:
        async for event in llm.chat_text_stream(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.35,
            max_tokens=700,
            trace={
                "agent": "open_items_intro",
                "mode": "proactive_intro",
            },
        ):
            if event.get("type") == "delta":
                full_text_parts.append(str(event.get("text") or ""))

        answer = _clean_llm_answer("".join(full_text_parts))

        if answer:
            return answer

    except Exception as e:
        chat_logger.info(
            "open_items_intro.llm_failed_fallback_used",
            error=str(e)[:180],
        )

    return _build_open_items_intro_text(context)


async def build_open_items_intro(
    conn: Connection,
    *,
    public_user_id: str,
    priority_info_request_id: str | None = None,
) -> dict:
    context = await load_open_items_context(
        conn,
        public_user_id=public_user_id,
        priority_info_request_id=priority_info_request_id,
    )

    if not context:
        raise OpenItemsIntroError("OPEN_ITEMS_CONTEXT_EMPTY")

    chat_logger.info(
        "open_items_intro.llm_start",
        priority_info_request_id=priority_info_request_id,
    )
    assistant_text = await _build_open_items_intro_text_with_llm(context)

    chat_logger.info(
        "open_items_intro.llm_done",
        assistant_preview=assistant_text[:180],
    )

    return {
        "ok": True,
        "context": context,
        "assistant_text": assistant_text,
    }