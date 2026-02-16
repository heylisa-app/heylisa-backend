
# HeyLisa — Orchestrator Policy (Context Decision) — v1.2

Objectif :
- Lisa décide du niveau de contexte : LIGHT / MEDIUM / MAX.
- La décision doit être fiable : `confidence >= 0.8`.
- Si `confidence < 0.8` → fallback LIGHT + (question user OU 1 fetch low-cost).

IMPORTANT :
- Le backend fournit `max_allowed_level` (garde-fou business).
- Lisa ne peut pas choisir au-dessus.

---

## 1) Règles “incontournables” (non négociables)

1) LIGHT est toujours autorisé pour tout le monde (y compris PRO).
2) Le niveau choisi doit être proportionné au message.
3) Si message = social turn (bonjour/merci/ok/au revoir/emoji) → LIGHT par défaut.
4) Si freemium et quota/entitlements limitent → `max_allowed_level = LIGHT` (cap côté backend).
5) En cas de doute → LIGHT + question courte (pas de pavé).

---

## 2) Détection “social turn” (LANGUE-AGNOSTIC)

Traiter comme social turn si :
- <= 6 mots OU message = emoji-only
- contenu = salutation, remerciement, validation, au revoir
- aucun verbe d’action / aucune demande “résultat”

Exemples :
- “ok”, “merci”, “bonne nuit”, “à plus”, “👌”, “lol”, “mdr”, “ok je vois”
→ LIGHT

Exception :
- social turn + action : “bonne nuit, rappelle-moi demain à 9h”
→ MEDIUM (car action + timezone)

---

## 3) Choix du niveau : heuristiques de Lisa

### LIGHT (choisir si majorité des signaux)
- Social turn
- Question stable sans dépendre de la vie user
- Réponse courte attendue
- Pas d’action, pas de décision, pas d’historique nécessaire
- Le user vient juste de passer le paywall / contexte “coût minimal”

### MEDIUM
- Le user demande conseil (décision support)
- Le user fait référence à un sujet récent (“comme on disait hier”)
- Le ton doit être très ajusté (émotion, stress, soutien)
- Onboarding en cours (glaner facts) + réponse de qualité
- Question “semi-stable” mais dépendante du profil (activité, ville, objectifs)

### MAX
- Demande actionnable multi-étapes (plan, checklists, orchestration)
- Demande pro avec contexte (cabinet, patient, dossier) OU add-on actif pertinent
- Proactivité (anniversaire, événement, suivi émotionnel) avec timeline nécessaire
- Nécessité d’historique long (contradictions, engagement, promesses)

---

## 4) Score de confiance (doit >= 0.8)

Lisa calcule un score simple, basé sur 5 critères (0–1 chacun) :

1) Clarté d’intention (intent clarity)
2) Besoin réel de contexte (context necessity)
3) Impact (risque si réponse sans contexte)
4) Coût relatif (est-ce que MEDIUM/MAX apporte une valeur nette)
5) Cohérence avec historique (est-ce compatible avec le thread récent)

Confidence = moyenne(1..5)

Règle :
- Si confidence < 0.8 :
  - fallback LIGHT
  - action : (A) poser 1 question ciblée OU (B) demander 1 fetch low-cost

---

## 5) “Extra fetches” (données ciblées)

Lisa peut demander des fetchs si :
- Contexte actuel insuffisant pour produire une réponse sûre
- Le fetch est ciblé et justifié (pas “charge tout”)

Exemples fetch low-cost :
- “Récupère les 10 derniers messages”
- “Récupère user_settings (timezone, tone, proactivity)”
- “Récupère les 5 prochains events”
- “Récupère facts catégorie X”

Exemples fetch à éviter si pas nécessaire :
- Charger toute la table facts brute
- Charger tout l’historique conversationnel complet
- Web search systématique

---

## 6) Output invariant (obligatoire)

Lisa doit produire un bloc décision à chaque message :

```json
{
  "context_decision": {
    "chosen_level": "light",
    "max_allowed_level": "medium",
    "confidence": 0.86,
    "reasons": [
      "Message = social turn (au revoir, pas d'action)",
      "Aucun historique nécessaire pour répondre humainement"
    ],
    "extra_fetches": [],
    "fallback_if_low_confidence": {
      "use_level": "light",
      "action": "ask_user"
    }
  }
}