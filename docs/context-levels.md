# HeyLisa — Context Levels (LIGHT / MEDIUM / MAX) — v1.2

Objectif :
- Donner à Lisa un contexte **stable, synthétique, et scalable**.
- Éviter de charger “tout” à chaque message.
- Permettre une **décision agentique** (Lisa choisit), avec un garde-fou business côté backend.

Principe :
- Backend calcule `max_allowed_level` (garde-fou coût/entitlements).
- Lisa choisit `chosen_level` ∈ [LIGHT..max_allowed_level] avec `confidence >= 0.8`.
- Si `confidence < 0.8` → fallback LIGHT.

---

## 0) Conventions

- Tous les timestamps en ISO 8601.
- Toutes les dates “humaines” doivent être interprétées via `timezone`.
- Les champs doivent être présents même si vides (pour éviter les prompts “branchy”).

---

## 1) Context LIGHT (minimal universel — toujours possible)

Usage typique :
- Salutations / small talk / acquiescement / au revoir
- Questions simples “stables”
- Freemium (par défaut) : LIGHT only

Champs LIGHT :

### Identité & préférences de base
- `user.id`
- `user.preferred_name` (ou `null`)
- `user.first_name` (ou `null`)
- `user.locale_main` (ex: "fr", "en")
- `user.timezone` (ex: "Europe/Paris") ✅ obligatoire
- `user.tu_vous` (values: "tu" | "vous" | "unknown")

### Produits / entitlements / quota
- `billing.is_pro` (bool)
- `billing.active_products` (array string, ex: ["personal_assistant", "airbnb"])
- `freemium.quota_limit`
- `freemium.quota_used`
- `freemium.quota_remaining`
- `freemium.quota_exhausted` (bool)

### Conversation context ultra-court
- `conversation.id`
- `conversation.channel`
- `conversation.last_contact_at`
- `conversation.last_user_message_at`
- `conversation.last_topics` (1–3 tags max)
- `conversation.thread_summary` (2–5 lignes max)
- `conversation.last_messages` (max 5 items: role + short content)

### Flags relationnels
- `relationship.onboarding_completed` (bool)
- `relationship.proactivity_enabled` (bool)

---

## 2) Context MEDIUM (assistant “réel” — utile pour répondre bien)

Usage typique :
- Questions générales mais contextualisées (“tu me conseilles quoi ?”)
- Suivi d’un sujet déjà en cours
- Début de décision support
- User Pro/Premium mais message non trivial

Champs MEDIUM = LIGHT + :

### Profil synthèse (1 écran)
- `profile.one_liner` (ex: "Entrepreneur, construit HeyLisa, focus automation/IA")
- `profile.primary_city` (ou `null`)
- `profile.main_activity` (ou `null`)
- `profile.family_context` (1 ligne max, optionnel)
- `profile.current_projects` (liste courte 1–5)
- `profile.communication_tone` (ex: "warm_direct", "professional", "playful")

### Mémoire utile (facts “high confidence”)
- `facts.core` (clé/valeur, confidence >= 0.8)
  - ex: `core.preferred_name`, `core.primary_city`, `core.activity`
- `facts.preferences` (confidence >= 0.8)
  - ex: `preferences.communication_tone`, `preferences.proactivity_enabled`

### Radar 6D (très synthétique)
- `radar6d.summary` (1–3 lignes)
- `radar6d.scores` (6 nombres 0–100 ou null)
- `radar6d.last_updated_at`

### Conversation (plus riche mais limitée)
- `conversation.last_messages` (max 10 items)
- `conversation.open_loops` (0–3 items: "Tu m’as dit de te rappeler X", "Tu avais un RDV Y")

---

## 3) Context MAX (mode “pilotage” — réservé aux cas complexes)

Usage typique :
- Demande actionnable / multi-étapes
- Demande pro (cabinet médical, legal, finance) + besoin d’historique
- Préparation proactivité (événements, suivis, rappels)
- Add-ons actifs (Ultimate, Airbnb…) + question nécessitant plus de matière

Champs MAX = MEDIUM + :

### Timeline & événements
- `timeline.upcoming_events` (0–10)
- `timeline.recent_events` (0–10)
- `timeline.reminders` (0–10)
- `timeline.next_action_suggestions` (0–5)

### Projets & référentiels
- `projects.active` (0–10, each: name, status, next_step, last_update)
- `knowledge.pinned_docs` (ids + titles + scopes)
- `knowledge.key_constraints` (ex: “pas d’hallucination legal”, “websearch only if…”)

### Historique conversationnel élargi
- `conversation.last_messages` (max 20 items)
- `conversation.long_memory_summary` (10–20 lignes max)
- `conversation.patterns` (anti-pattern checks: repetition, name usage)

---

## 4) Exemple de payload de contexte (LIGHT)

```json
{
  "level": "light",
  "generated_at": "2026-02-06T10:15:00Z",
  "user": {
    "id": "usr_123",
    "preferred_name": "Brice",
    "first_name": "Brice",
    "locale_main": "fr",
    "timezone": "Europe/Paris",
    "tu_vous": "tu"
  },
  "billing": {
    "is_pro": false,
    "active_products": ["personal_assistant"]
  },
  "freemium": {
    "quota_limit": 8,
    "quota_used": 2,
    "quota_remaining": 6,
    "quota_exhausted": false
  },
  "relationship": {
    "onboarding_completed": false,
    "proactivity_enabled": true
  },
  "conversation": {
    "id": "conv_456",
    "channel": "mobile_chat",
    "last_contact_at": "2026-02-06T10:13:10Z",
    "last_user_message_at": "2026-02-06T10:13:10Z",
    "last_topics": ["onboarding"],
    "thread_summary": "1er contact. Lisa collecte prénom, ville, activité.",
    "last_messages": [
      {"role": "assistant", "content": "Salut ! On se tutoie ou on se vouvoie ?"},
      {"role": "user", "content": "On se tutoie 🙂"}
    ]
  }
}