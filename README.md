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
python3 -m uvicorn app.main:app --reload --port 8000

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

