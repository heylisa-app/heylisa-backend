# HeyLisa Backend

Backend Python (FastAPI) de **HeyLisa** — Assistante IA exécutive.  
Ce service constitue le **socle backend applicatif** (logique métier, accès DB, orchestration), distinct :
- du frontend mobile (Expo / React Native)
- des workflows n8n (automations, webhooks)
- de Supabase (auth + base de données managée)

---

## 🎯 Objectifs du backend (vision)

- Fournir des **endpoints applicatifs stables** (Context Loader, Quota, Lisa runtime, etc.)
- Centraliser la **logique métier critique** (quotas, droits, modes, règles)
- Garantir un accès **DB asynchrone performant** (asyncpg)
- Être déployable facilement (Railway dev/prod)

⚠️ À ce stade, le backend est volontairement **minimal** : on pose le socle proprement avant d’empiler la logique.

---

## 🧱 Stack technique

- **Python 3.11**
- **FastAPI** — framework API
- **Uvicorn** — serveur ASGI
- **asyncpg** — driver PostgreSQL asynchrone (choix acté)
- **pydantic-settings** — gestion des variables d’environnement
- **structlog** — logging structuré
- **Supabase Postgres** — base de données (externe)

---

## 📁 Structure du projet

heylisa-backend/
├── app/
│   ├── api/            # Routes API (ex: health)
│   ├── core/           # Config & logging
│   ├── init.py
│   └── main.py         # Entrée FastAPI
│
├── heylisa-n8n/        # Assets / flows n8n liés (hors scope backend pur)
├── supabase_schema_prod.sql
│
├── .env                # Variables locales (non versionné)
├── .env.example        # Template d’env
├── requirements.txt
├── runtime.txt         # Version Python pour Railway
├── README.md
└── .gitignore

---

## ⚙️ Setup local

### 1) Environnement Python

```bash
python3 -m venv .venv

#### Activer l'environnement virtuel
source .venv/bin/activate

Vérification :

which python
python3 --version
# => Python 3.11.x depuis .venv

2) Installation des dépendances
pip install -r requirements.txt

Contenu actuel :
fastapi
uvicorn[standard]
python-dotenv
pydantic-settings
structlog
httpx
asyncpg

3) Variables d’environnement

Créer .env à la racine (ne jamais committer) :

DATABASE_URL=postgresql://postgres:PASSWORD@db.<project-ref>.supabase.co:5432/postgres
ENVIRONMENT=dev
LOG_LEVEL=INFO

⚠️ Important :
	•	Ne pas mettre de crochets [] autour du password dans l’URL (sinon asyncpg casse).
	•	Pour Supabase : choisir Direct connection pour usage “service backend / long-lived”.
	•	En dev local, l’IP allowlist Supabase peut être requise selon ta config.

👉 DATABASE_URL correspond à la connection string Supabase
(Supabase → Settings → Database → Connection string).

⸻

4) Lancer le serveur en local (commande standard)

⚠️ Commande officielle recommandée (évite les soucis de PATH) :

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

⚠️ Commande simple
uvicorn app.main:app --reload --port 8000

✅ Health check

Endpoints :
GET /health

Test : 
curl -s http://127.0.0.1:8000/health | python3 -m json.tool


Réponse attendue : 
{
  "status": "healthy",
  "environment": "dev",
  "version": "0.1.0",
  "timestamp": "2026-02-06T02:45:14.538215"
}

GET /v1/quota/{public_user_id}

Test : 
curl -s http://127.0.0.1:8000/v1/quota/<PUBLIC_USER_ID> | python3 -m json.tool

Retourne l’état quota d’un user (read-only) :

Réponse :
{
  "public_user_id": "...",
  "is_pro": false,
  "free_quota_used": 6,
  "free_quota_limit": 8,
  "state": "normal",
  "paywall_should_show": false
}

VOIR LES LOGS DU CHAT

FULL LOG : 
En local :
LOG_LEVEL=DEBUG python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Filtré : 
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --access-log --log-level debug | grep -E "chat_intro|chat_message|heylisa_backend"

python3 -m uvicorn app.main:app --reload --port 8000 --log-level info


Et si tu veux les prompts en fichiers (Step 2 quand on l’ajoute côté ResponseWriter) :
LOG_LEVEL=DEBUG DEBUG_PIPELINE=1 DEBUG_DUMP_PROMPTS=1 python3 -m uvicorn ...

A) Voir tout le chat tracing
python3 -m uvicorn app.main:app --reload --port 8000 | grep heylisa.chat

B) Voir uniquement les events (encore plus strict)
python3 -m uvicorn app.main:app --reload --port 8000 | grep '"logger": "heylisa.chat"'

C) Voir juste les nodes
python3 -m uvicorn app.main:app --reload --port 8000 | grep '"event": "chat.node.'

(sur mac, grep marche direct)


Règles Quota (v1)

Tables utilisées
	•	public.users.is_pro (source de vérité abonnement)
	•	public.user_settings.free_quota_used (compteur)
	•	public.user_settings.free_quota_limit (limit)

Invariants
	•	On ne reset jamais free_quota_used (quota free “lifetime”)
	•	state calculé backend (aide Lisa + logique côté services) :
	•	normal si used < limit - 1
	•	warn_last_free si used == limit - 1 (ex: message #7 si limit=8)
	•	blocked si used >= limit

Paywall
	•	Le front doit afficher paywall si :
	•	!isPro && free_quota_used >= free_quota_limit
	•	C’est volontairement un pont direct DB <-> front en realtime (option A).
	•	Le backend sert surtout à fournir un état consolidé (state) pour Lisa / services.

📜 Journal d’implémentation

2026-02-06 — Backend v0 stabilisé

But
	•	Poser un socle backend propre avant toute logique métier.
	•	Préparer l’intégration future des endpoints (Quota, Context Loader, Lisa).

Réalisé
	•	Initialisation FastAPI fonctionnelle
	•	Logging structuré en place
	•	Endpoint /health opérationnel
	•	Environnement Python isolé (.venv)
	•	Choix technique acté : asyncpg pour PostgreSQL
	•	Commandes de run standardisées (python3 -m uvicorn)
	•	Compatibilité Railway (runtime.txt)

Décisions techniques clés
	•	DB driver : asyncpg (asynchrone, performant)
	•	Backend volontairement minimal au départ
	•	Documentation tenue au fil de l’eau (pas de dette doc)

⸻

🚧 Ce qui n’est PAS encore implémenté (volontairement)
	•	Pool de connexion DB
	•	Endpoints métier (quota, context loader, etc.)
	•	Auth backend (repose encore sur Supabase côté front)
	•	Sécurité avancée (RLS backend, scopes, etc.)

👉 Ces éléments seront ajoutés étape par étape, chacun documenté dans ce journal.

⸻

▶️ Prochaines étapes prévues
	1.	Ajout du module DB asyncpg (pool)
	2.	Service Quota standalone (sans branchement front)
	3.	Endpoint /quota/status
	4.	Puis intégration progressive au Context Loader

⸻

🧠 Règle de gouvernance

Toute évolution backend doit :
	•	être commitée
	•	être documentée ici (quoi / pourquoi / contraintes)
	•	ne pas casser l’existant sans décision explicite


## 🧠 Chat Engine — État actuel (février 2026)

Architecture générale
	•	Frontend (Expo / React Native)
	•	UI chat optimiste + DB source of truth
	•	Gestion fine des états :
	•	isLisaBusy
	•	isLisaThinking
	•	isSlowThinking
	•	Aucun message Lisa n’est écrit côté front (sauf fallback local UX)
	•	Backend (API Chat)
	•	Endpoint principal :
	POST /v1/chat/message


	•	Le backend est l’unique source de vérité pour :
	•	la création des messages Lisa
	•	la persistance en base
	•	la logique métier (quota, routing, agents à venir)

⸻

Flux d’un message utilisateur
	1.	L’utilisateur envoie un message depuis le front
	2.	Le message est sauvegardé immédiatement en base (conversation_messages)
	3.	Le front affiche le message en optimiste
	4.	Le front appelle :
POST /v1/chat/message

avec :

{
  "conversation_id": "...",
  "user_message_id": "..."
}

	5.	Le backend traite le message (logique en cours d’extension)
	6.	Le front recharge l’historique depuis la DB
👉 UI 100% alignée DB, zéro divergence

⸻

Gestion des erreurs (front)
	•	Erreurs réseau / front
	•	Pas de fallback backend
	•	Pas d’écriture DB
	•	Message UX local Lisa :
“Je n’arrive pas à joindre le serveur. Réessaie dans quelques secondes 🙏”
	•	Le message utilisateur est restauré dans le champ si non sauvegardé
	•	Erreurs backend
	•	Fallback Lisa local (pas DB)
	•	Aucun état bloquant (watchdog UI)
	•	Watchdogs
	•	Soft warning après 25s (isSlowThinking)
	•	Hard UI release après 5 min (anti “Lisa thinking infini”)

⸻

Configuration environnement
	•	Le frontend utilise dynamiquement :

BACKEND_BASE_URL

injecté via :
	•	app.config.ts
	•	extra.backend.baseUrl
	•	fallback local http://127.0.0.1:8000

	•	En production :
https://api.heylisa.io

👉 Aucun changement front requis entre dev / prod.

⸻

État de stabilité
	•	✅ Chat fonctionnel en DEV
	•	✅ Paywall backend-compatible
	•	✅ UX fluide (typing, scroll, erreurs)
	•	✅ Architecture validée pour extension (agents, routing, onboarding)


## Pilotage des LLMs : règle actée (simple et saine)

1️⃣ Choix des providers

On grave ça dans le marbre :

Ordre d’appel
	1.	DeepSeek → provider primaire
	2.	OpenAI 4o-mini → fallback uniquement

Principe
	•	Le backend ne sait pas “quel agent” utilise quel LLM.
	•	Il appelle un LLM runtime unique.
	•	Ce runtime :
	•	tente DeepSeek
	•	si erreur / timeout / output invalide → fallback OpenAI
	•	renvoie { text, provider }

👉 Tu l’as déjà implicitement fait dans le chat engine, on ne change rien, on généralise.

⸻

2️⃣ Très bon point : ne PAS figer les outputs de tous les agents

Tu as 100% raison.

❌ Erreur classique à éviter

“On définit dès maintenant les JSON outputs de 12 agents qu’on n’a pas encore vraiment éprouvés”

Résultat habituel :
	•	rigidité prématurée
	•	refactors incessants
	•	perte de vitesse

⸻

3️⃣ La bonne stratégie (ce que je te recommande fortement)

✅ Ce qu’on fixe MAINTENANT

Seulement les invariants systémiques, pas les métiers :

A. Convention universelle d’output agent

Tous les agents doivent respecter au moins ceci :

{
  "confidence": 0.0,
  "decision": "...",
  "notes": "...",
  "payload": {}
}

	•	confidence ∈ [0,1] → obligatoire
	•	decision → string courte (routing, choix contexte, etc.)
	•	notes → explicatif humain (debug / logs / observabilité)
	•	payload → libre, évolutif, spécifique à l’agent

👉 Le backend ne fait confiance à un agent que si confidence ≥ 0.8
Sinon → fallback déterministe (LIGHT context, réponse safe, etc.)

C’est LA règle critique


⸻

B. System messages & prompts : figés, mais extensibles

On fige :
	•	la structure
	•	la philosophie
	•	les garde-fous

On n’énumère pas :
	•	tous les agents
	•	tous les champs
	•	tous les cas

⸻

4️⃣ Organisation concrète des prompts (v1 réaliste)

app/prompts/
  system/
    lisa_persona.md
    safety.md
    output_contract.md   # ← le JSON minimal ci-dessus
  agents/
    intent_classifier.md
    router.md
    onboarding.md
    response_generator.md


	•	Chaque prompt est indépendant
	•	Le backend compose dynamiquement
	•	Aucun prompt “géant universel”

⸻

5️⃣ Comment le backend orchestre sans sur-spécifier


 ✅ Backend agentique (Orchestration)

Request
    ↓
Orchestrator (décide du plan)
    ↓
Agent Graph (DAG - Directed Acyclic Graph)
    ├─→ Agent A (parallèle)
    ├─→ Agent B (parallèle)
    │     ↓
    └─→ Agent C (séquentiel, dépend de A+B)
          ↓
       Agent D (synthèse)
    ↓
Response

Non-linéaire, adaptatif, asynchrone


Mico-Exemple logique simplifiée (pseudo-flow)

message user
   ↓
IntentClassifierAgent
   → confidence < 0.8 ? fallback general
   ↓
RouterAgent
   → choisit context_level (light / medium / max)
   → confidence < 0.8 ? force light
   ↓
ContextLoader(context_level)
   ↓
ResponseGeneratorAgent


À aucun moment :
	•	le backend n’impose une structure métier rigide
	•	le backend ne “devine” à la place de Lisa

👉 Lisa décide, le backend valide et borne.

⸻

6️⃣ Où vivent les règles métier (important)

Élément
Où
Persona Lisa > system prompt
Anti-patterns > system prompt
Choix contexte > agent router
Limites quota > backend
Fallback sécurité > backend
Langue / timezone > context loader
Proactivité > agent + cron / jobs

👉 Le backend est le gendarme, pas l’intelligence.

⸻

7️⃣ Ce qui est verrouillé 

On a :
	•	un runtime LLM propre
	•	une architecture agentique contrôlée
	•	une évolution incrémentale possible
	•	zéro dette de prompt prématurée
	•	une Lisa qui reste maîtresse de ses décisions


---

## 📜 Journal d’implémentation

### 2026-02-07 — Chat Engine v1 (Orchestrator + PlanExecutor + ResponseWriter) ✅

Objectif
- Passer d’un “chat direct LLM” à une architecture **agentique contrôlée** (DAG) :
  - Orchestrator = décide intent / contexte / besoin web / plan
  - PlanExecutor = exécute le plan (tools + agents)
  - ResponseWriter (Lisa) = génère la réponse finale avec conventions UI stables

Réalisé
- ✅ **OrchestratorAgent** (LLM) qui produit un plan DAG JSON :
  - Détection `intent`, `context_level`, `need_web`, `web_search_prompt`
  - Génération du plan via une **whitelist stricte** de nodes
  - Guardrails : confidence, cohérence need_web, contraintes amabilities
- ✅ **PlanExecutor** :
  - Exécution topo simple basée sur `depends_on`
  - Exécution des nodes autorisés :
    - `tool.db_load_context` (context loader)
    - `tool.quota_check` (statut quota)
    - `tool.web_search` (Perplexity sonar-pro)
    - `agent.response_writer` (Lisa)
  - **Verrou “answer-only”** : sortie toujours une string safe (fallback + truncation)
  - **Hard allowlist** côté executor : tout node non autorisé est rejeté
- ✅ **ResponseWriterAgent (Lisa)** :
  - System prompt stable + anti-patterns + règles intent
  - **Conventions UI** pour réponses “chat-safe” (pas de HTML, pas de markdown complexe)
  - Gestion des sources web :
    - Affiche au besoin un bloc `📌 Sources` (1 à 3 puces, sans URL)
    - N’injecte au modèle que titres + domaines (pas de liens bruts)
  - Compat params : `web=` + fallback `web_search=`

Décisions techniques clés
- **Architecture agentique (DAG) contrôlée**
  - Le backend exécute, borne et valide.
  - L’intelligence est répartie : orchestrator (plan) + lisa (rédaction).
- **Whitelisting strict des nodes**
  - Source de vérité : `app/agents/node_registry.py`
  - Utilisé par :
    - l’Orchestrator (dans le prompt + validation)
    - le PlanExecutor (refus hard si type non autorisé)
- **IDs A/B/C/D**
  - Convention simple pour v0 :
    - A = context
    - B = quota
    - C = web_search (si besoin)
    - D = response_writer (final)
  - L’ordre de traitement réel reste déterminé par `depends_on` (pas par la lettre).

Endpoints impactés
- `POST /v1/chat/message`
  - Devient le point d’entrée unique :
    - lit message user (DB)
    - orchestre plan
    - exécute
    - écrit le message Lisa en DB (source of truth)

Gestion des erreurs
- **Niveau Chat (chat.py)**
  - Try/except global : fallback réponse safe si crash complet
- **Niveau PlanExecutor**
  - Verrou final “answer-only” : même si response_writer foire, on renvoie une string safe
  - Anti pavé : limite `MAX_ANSWER_CHARS` + ellipsis

Fichiers ajoutés / modifiés (v1)
- `app/services/chat.py`
  - Branche OrchestratorAgent + PlanExecutor
  - Persistance DB + idempotence via `assistant_message_id` + `dedupe_key`
- `app/agents/orchestrator.py`
  - Prompt de routing + génération plan DAG
  - Validation plan + fallback minimal
  - Intégration whitelist via `node_registry`
- `app/services/plan_executor.py`
  - Exécution DAG + guardrails answer-only
  - Hard allowlist `NODE_TYPE_WHITELIST`
- `app/agents/response_writer.py`
  - Lisa “writer” : conventions UI + règles intent + sources digest
- `app/tools/web_search.py`
  - Tool web search (Perplexity sonar-pro) JSON strict
- `app/agents/node_registry.py`
  - Source de vérité : whitelist node types + règles IDs
  - Helpers de rendu pour inclusion dans le system prompt

Ce qui n’est PAS encore implémenté (volontairement)
- ❌ Exécution d’actions réelles (Ultimate mode : agenda, email, etc.)
- ❌ “Pro modes” (Medical/Airbnb/etc.) branchés au routing
- ❌ Parallélisation réelle (parallel_group ignoré en v0)
- ❌ Observabilité avancée (traces structurées par node, metrics, etc.)

Prochaines étapes prévues
1. Verrouiller les prompts de l’Orchestrator (tests non-régression par intent)
2. Optimisation ResponseWriter (Lisa) :
   - cadrage des entrées (context, web, intent)
   - anti-robot + concision + style stable
3. (Option) Ajout d’un “debug mode” backend (stockage exec_out.debug en metadata)
4. (Option) Parallélisation vraie des nodes `parallel_group`

---

## Scope of work - Flow Orchestrateur

1) Ce que fait VRAIMENT l’orchestrateur

Il fait 3 choses, dans cet ordre :

A) Lecture d’état (state)

À partir du contexte (profil, quota, facts, abonnements, historique), il déduit :
	•	eligibility.smalltalk_intro = true/false
	•	capabilities (ce que Lisa a le droit de faire selon les abonnements)
	•	conversation_phase (ex: intro onboarding / conversation normale)
	•	topic continuity (le user dit “ok” => on garde l’intent précédent ou on suit une continuité)

B) Décision d’intent (intent + mode)

Il choisit un intent en tenant compte de la dynamique (last 10 messages), pas juste le dernier.

C) Application de guardrails business (gates)

Il applique les règles “non négociables” :
	•	smalltalk_intro prioritaire si éligible ET pas dévié par intent prioritaire
	•	certains intents interdits si pas d’abonnement => on garde l’intent “naturel”, mais on le marque non éligible et on bascule en “downgrade behavior” (réponse adaptée + upsell soft si besoin)
	•	quand smalltalk_intro est actif, small_talk et amabilities sont désactivés (ou plutôt absorbés par le mode intro)

⸻

2) Les entrées indispensables (ctx) — version “source of truth”

I- Contexte minimum :

user_profile
	•	public_user_id
	•	first_name, last_name
	•	locale_main, timezone
	•	use_tu_form (bool|null)

user_status
	•	is_pro (OK mais pas suffisant)
	•	free_quota_used (count messages user lifetime)
	•	free_quota_limit (8)
	•	state: normal | warn_last_free | blocked

user_facts_required
	•	required_keys = [first_name, use_tu_form, main_city, main_activity]
	•	known / missing + missing_count

subscriptions / capabilities / Integrations

(À partir de public.lisa_user_agents (ton screen) :
	•	agents actifs (ex: personal_assistant)
	•	donc capabilities calculées :
	•	can_action_request
	•	can_deep_work
	•	can_professional_modes
	•	etc.)

history
	•	last_10 messages (role + content + ts + sender)
	•	last_user_message (string)
	•	last_assistant_message (string)
	•	optional: last_orchestrator_intent (si tu le stockes en metadata)

II- Contexte additionnel

Principes (simples, robustes)

A. Contexte = proportionnel à l’utile
	•	Si le user dit “merci bonne nuit”, on ne charge pas le bilan comptable 2024 et l’astrologie.
	•	Si le user démarre (smalltalk_intro), on charge minimum vital pour collecter les facts.

B. Le contexte est une décision orchestrateur, mais le backend garde le sifflet
	•	Orchestrateur propose context_level
	•	Backend force certains cas (ex : user non pro → pas de medium/max)

Règles v1 (ancrées)
	•	Si intent = smalltalk_intro → context_level = light (forcé)
	•	Si is_pro = false → context_level ∈ {light} (forcé)
	•	Si is_pro = true et user a agent perso (personal/ultimate)
→ medium possible, selon intent, sinon light.
	•	Si user a un agent “pro mode” actif (medical_assistant, etc.)
→ max possible, selon intent + question, sinon medium/light.

Extension future (déjà prévue)
	•	Orchestrateur peut activer un node SQL ciblé (“fetch something precise”), injecté dans le contexte (mais on garde ça pour après, pas dans la clôture smalltalk).

	🧠 Context Management — v1 (HeyLisa)

Objectif

Garantir que Lisa reçoive le bon niveau de contexte, ni plus ni moins, en fonction :
	•	de l’intention utilisateur,
	•	de son stade (nouvel utilisateur vs habitué),
	•	de ses capacités / abonnements.

Principe fondamental :

Le contexte est proportionnel à l’utile.

⸻

1. Architecture générale des contextes

Le contexte est structuré en 2 blocs distincts :

I. Bloc minimum (toujours chargé)

Ce bloc est la source of truth.
Il est chargé dans tous les cas, quel que soit l’intent ou le niveau.

user_profile
	•	public_user_id
	•	first_name
	•	last_name
	•	full_name

settings
	•	locale_main
	•	timezone
	•	use_tu_form (bool | null)
	•	intro_smalltalk_turns
	•	intro_smalltalk_done
	•	main_city
	•	main_activity

user_status
	•	is_pro
	•	free_quota_used
	•	free_quota_limit
	•	state : normal | warn_last_free | blocked

history
	•	messages : 10 derniers messages (ordre chronologique)
	•	role
	•	content
	•	sent_at

user_facts (logique smalltalk)
	•	required_keys
	•	known
	•	missing_required
	•	missing_required_count

gates
	•	smalltalk_intro_eligible
	•	smalltalk_target_key
	•	missing_required

➡️ Ce bloc est stable, minimal, et ne doit jamais être cassé.

⸻

2. Bloc additionnel — niveaux de contexte

Le bloc additionnel est variable, décidé par l’orchestrateur mais contrôlé par le backend.

Niveaux disponibles

Niveau Description
light -> Contexte minimal utile
medium -> Contexte enrichi (assistant personnel)
max -> Contexte professionnel profond (modes pro)

4. Définition officielle du Context Light (v1)

Le contexte light inclut :

4.1 Bloc minimum (cf. section 1)

Toujours inclus.

4.2 Facts persistés (DB)

Chargés depuis public.user_facts.

Structure exposée au modèle :

facts_store: {
  count: number,
  items: [
    {
      fact_key: string,
      category: string,
      scope: string,
      value_type: string,
      value: any,
      confidence: number,
      is_estimated: boolean,
      source_ref: string | null,
      notes: string | null,
      updated_at: string
    }
  ],
  keys: string[]
}

📌 Important :
	•	Les valeurs réelles sont bien présentes (main_city = "Paris", etc.)
	•	facts_keys_sample sert au debug, pas à l’agent.
	•	L’agent raisonne sur items.value, pas sur les clés seules.

⸻

5. Rôle du Context Light en SmalltalkIntro

Le contexte light est le contexte de référence du SmalltalkIntro.

Il permet :
	•	de connaître ce qui est déjà su sur l’utilisateur,
	•	d’identifier le prochain fact prioritaire à collecter,
	•	de guider une conversation naturelle sans surcharger le modèle.

👉 Même un utilisateur ancien peut repasser en light context
si l’intent est trivial ("merci", "bonne nuit").

⸻

6. Ce que le Context Light ne fait pas
	•	❌ Ne charge pas de données métier lourdes
	•	❌ Ne charge pas d’historique long
	•	❌ Ne déclenche pas de SQL ciblé
	•	❌ Ne suppose aucun besoin professionnel

Ces extensions sont prévues dans medium / max, ultérieurement.

⸻

7. État de validation
	•	✅ Context light implémenté
	•	✅ Facts DB chargés avec valeurs
	•	✅ Logs explicites (facts_store_count, facts_keys_sample)
	•	✅ SmalltalkIntro fonctionnel et traçable
	•	🔒 Contrat figé pour v1
	
⸻

3) Règle clé : smalltalk_intro = un MODE, pas juste un intent

On introduit 2 notions :

(1) eligibility.smalltalk_intro

Déterministe :
	•	free_quota_used < 8 ET
	•	missing_required_count > 0

Note : tu as raison, ne pas conditionner à is_pro, car on peut s’abonner avant d’atteindre 8. Donc le quota gating prime.

(2) mode.lock = smalltalk_intro (soft lock)

Si eligible, alors le mode par défaut devient smalltalk_intro…
…sauf si la conversation dévie vers un intent prioritaire.

Donc on a une règle :

Smalltalk Intro doit s’appliquer si :
	•	eligible.smalltalk_intro = true
	•	ET pas de signal “override” (voir section 4)

⸻

4) Overrides : quand on casse le smalltalk_intro même si éligible

On définit une liste d’intents qui cassent le mode intro (au moins pour ce tour) :

Priorité haute (toujours override) :
	•	urgent_request
	•	sensitive_question

Priorité moyenne (override si explicite) :
	•	functional_question (ex: “tu fais quoi ?”, “comment tu fonctionnes ?”)
	•	professional_request (si user parle patient, réservation, etc.)
(mais là tu vas souvent être non éligible côté capabilities)

Priorité “flow naturel” (override si l’utilisateur part vraiment en tâche) :
	•	decision_support
	•	motivational_guidance
	•	general_question

Et cas spécial : le user dit “ok”, “oui”, “non”, “vas-y”, “nickel”.
Là l’orchestrateur doit regarder le tour précédent :

	•	si on était en smalltalk_intro => on continue smalltalk_intro
	•	sinon on continue l’intent précédent / thread actif

⸻

5) Désactivation de certains intents en mode intro

Tu l’as dit : quand eligible.smalltalk_intro = true, on désactive :
	•	amabilities (un “merci” pendant l’intro, on le traite comme une micro-politesse MAIS on reste en intro)
	•	small_talk (absorbé par smalltalk_intro)

Donc :
	•	L’orchestrateur peut toujours détecter “amabilities” comme signal,
	•	mais il ne doit pas retourner intent=amabilities si intro est active,
	•	il retourne intent=smalltalk_intro avec un flag signals.amabilities=true (utile pour writer).

⸻

6) Capabilities gating (abonnements) — ton cas action_request / deep_work / professional_request

Tu as un point très important : le user peut demander une action même si pas éligible.

Donc on sépare :
	•	intent = ce que le user veut
	•	eligible = est-ce qu’on a le droit / le mode actif

Exemple

User: “Réserve-moi un resto”
	•	intent = action_request
	•	eligible = false (si pas agent / abonnement)
	•	behavior = “refuse + propose upgrade / propose alternative (guidage)”

Donc le résultat orchestrateur doit porter :
	•	intent
	•	intent_eligible: bool
	•	intent_block_reason: str|null
	•	mode (smalltalk_intro vs normal)

⚠️⚠️⚠️ IL FAUT RAJOUTER AUSSI LES SERVICES ACTIFS SELON CAPABILITIES (CAR USER PEUT VOIR UN ABONNEMENT MAIS PAS AVOIR CONNECTÉ UN OUTIL NÉCESSAIRE)
⸻

7) Sortie OrchestratorResult — à enrichir

Je te conseille d’étendre ton JSON (sans exploser le système) :
	•	intent: …
	•	mode: "smalltalk_intro" | "normal"
	•	intent_eligible: true/false
	•	gates: { smalltalk_intro_eligible, smalltalk_intro_locked, blocked_reason }
	•	capabilities: { can_action_request, can_deep_work, can_professional_request }
	•	signals: { short_reply, amabilities, etc. } (optionnel)

Et le plan peut rester minimal, mais avec inputs ResponseWriter enrichis :
	•	inputs.mode
	•	inputs.intent_eligible
	•	inputs.block_reason
	•	inputs.smalltalk_target_key (si intro: quelle fact on collecte maintenant)

⸻

8) Concrètement : ton “Step 1” change

Au lieu de “Orchestrator = LLM qui classifie et fait un plan”, on fait :

Partie déterministe (Python, avant LLM)
	•	compute eligibility.smalltalk_intro
	•	compute capabilities depuis lisa_user_agents
	•	compute conversation signals (short reply, last intent continuity si dispo)

Partie LLM (mais contrainte)
	•	choisir intent en regardant last10 + last_user
	•	MAIS avec règle : si eligible.smalltalk_intro => propose smalltalk_intro sauf override

Puis re-guardrails (Python, après LLM)
	•	appliquer les gates
	•	forcer intent si nécessaire
	•	calculer intent_eligible
	•	injecter flags dans plan

⚠️⚠️⚠️ ON GARDE SEULEMENT APPLIQUER LES GATES ET INJECTER LES FLAGS DANS "RE-GUARDRAILS"
⸻

9) Next step (sans discuter 3h) : ce qu’on code maintenant

On avance dans l’ordre que tu voulais :

Étape 1.1 — on ajoute 2 champs dans IntentType
	•	smalltalk_intro
	•	(éventuellement) blocked (pas obligatoire, mais utile)

Étape 1.2 — on modifie OrchestratorAgent.run pour accepter ctx

Et on ajoute au SYSTEM_PROMPT :
	•	définition de mode
	•	règles smalltalk_intro + overrides
	•	règle “short reply => dépend du contexte précédent”

Étape 1.3 — on sort du LLM la décision “intent” seulement (plan minimal figé)

Franchement : garde ton plan minimal constant pour l’instant.
Le vrai pilotage se fait via inputs de ResponseWriter.

⸻

🔎 Discovery Sequence (v1) — mode forcé, guidage, docs scopes

Objectif

La Discovery est une séquence structurée qui “prend la main” sur le chat pour :
	•	cadrer l’utilisateur (ce qu’il veut, son contexte, ses contraintes),
	•	établir un socle de facts utiles,
	•	guider vers une aide efficace sans tourner en rond,
	•	préparer l’activation d’un mode payant si besoin (Ultimate / Pro modes), sans forcer.

Principes clés
	•	Discovery est un MODE, pas juste un intent.
	•	Source de vérité = ctx.gates (calculé par context_loader, jamais inventé par le LLM).
	•	Si ctx.gates.discovery_forced=true et ctx.gates.discovery_status != "complete", alors Discovery override tout,
sauf urgent_request et sensitive_question.

Contrat côté Orchestrator
	1.	LLM propose un intent (et need_web / scopes docs éventuels).
	2.	Le backend applique des guardrails déterministes :

	•	mode = "discovery" + intent_final = "discovery" si discovery forced (sauf urgence/sensible)
	•	Absorption des intents “sociaux” pendant discovery :
	•	amabilities → reste en discovery
	•	small_talk → reste en discovery

	3.	Le plan n’est pas “inventé” par le LLM : on construit un plan stable (min-risk) et on injecte les flags.

Documentation interne (docs scopes) pendant Discovery

Discovery peut s’appuyer sur la doc produit, mais de manière contrôlée :
	•	Les scopes disponibles sont listés dans le system prompt via ctx.docs.scopes_all.
	•	L’orchestrator peut activer scope_need=true et choisir scopes_selected (1 à 3 max).
	•	Le PlanExecutor exécute alors tool.docs_chunks (node S) :
	•	Source de vérité : ctx.docs.chunks_by_scope[scope]
	•	Hard caps : max 3 scopes, max 20 chunks, max 8 chunks par scope
	•	Le ResponseWriter reçoit docs_chunks et doit les utiliser en priorité si présents (avant le contexte compact).

DAG v1 (plan minimal)

En Discovery, le plan reste stable. Exemple typique :
	•	A: tool.db_load_context
	•	B: tool.quota_check
	•	(S): tool.docs_chunks (si scope_need=true)
	•	(C): tool.web_search (si need_web=true)
	•	D: agent.response_writer (réponse finale)

Node IDs convention : A, B, C, S, D
Source de vérité whitelist : app/agents/node_registry.py

Inputs injectés au ResponseWriter (Discovery)

Le ResponseWriter reçoit en entrée :
	•	mode="discovery"
	•	intent="discovery"
	•	transition_window + transition_reason (copiés depuis ctx.gates)
	•	intent_eligible + intent_block_reason (capabilities gating)
	•	docs_chunks (si activé)
	•	web (si activé)

Règles de réponse (Discovery)
	•	Ton : conversationnel, direct, actionnable.
	•	Pas de “cours magistral” : questions ciblées + prochaines étapes.
	•	Respect strict des conventions UI (pas de markdown lourd / pas de code fences).
	•	Si sources web affichées : uniquement un bloc 📌 Sources avec 1–3 puces sans URL.

	---

## ✅ 2026-02-11 — Docs scopes + Discovery AHA flags (stabilisé)

### Docs scopes (RAG light, contrôlé)
- Le **Context Loader** expose la liste des scopes disponibles :
  - `ctx.docs.scopes_all` + `ctx.docs.scopes_count`
- L’Orchestrator peut activer `scope_need=true` et sélectionner `scopes_selected` (1 à 3 max).
- Le PlanExecutor exécute alors le node :
  - `S: tool.docs_chunks` (capé : 3 scopes, 8 chunks/scope, 20 chunks total)
- Le ResponseWriter reçoit `docs_chunks` et les utilise en priorité si présents.

✅ Objectif : **docs utiles quand nécessaires**, sans surcharge ni dérive.

---

### Discovery : AHA moment (flags internes, zéro pollution DB)
Discovery peut produire des “flags” internes en fin de réponse :
- `aha_moment=true`
- `onboarding_abort=true`

⚠️ Règle non négociable :
- **Ces flags ne doivent jamais être persistés dans `conversation_messages.content`.**

✅ Implémentation (v1) :
- Le backend **nettoie le texte** avant insertion DB (strip des flags en fin de message).
- Les flags sont stockés uniquement en **metadata** (`provider.flags`), si besoin d’observabilité.

---

### Logs utiles (diagnostic docs)
Dans les logs `heylisa.chat`, on doit voir :
- `chat.ctx.summary` → `docs_scopes_count > 0`
- `chat.docs_chunks.db` → `rows_count` et `chunks_count`
- `chat.response_writer.docs_chunks` → preview du 1er chunk (safe)

Si `has_docs=false` côté `chat.response_writer.call`, le problème est avant (ctx/scopes) ou dans la sélection des scopes.

---


