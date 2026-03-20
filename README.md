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

PROCESSUS SPLIT TERMINAL CURSOR (ultra clean)

Dans Cursor / VS Code :

Terminal → Split Terminal
À gauche :
cd ~/dev/heylisa-backend


puis : 
source .venv/bin/activate
LOG_LEVEL=DEBUG python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. À droite :
cd ~/dev/heylisa-mobile
npm start

4. pour la webapp:
cd ~/heylisa-webapp
npm run dev

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




================================================
HeyLisa — Sprint 1 Auth & Provisioning

Objectif du sprint

Mettre en place un socle unique d’identité et de provisioning pour HeyLisa Assistante Médicale, partagé entre web, mobile, backend FastAPI, Supabase et la future facturation Stripe.

Ce sprint ne branche pas encore Stripe de manière active. Il prépare un modèle propre pour que :
	•	un compte créé sur le web puisse se connecter sur l’app,
	•	un compte créé sur l’app puisse se connecter sur le web,
	•	chaque nouvel utilisateur crée automatiquement un cabinet,
	•	chaque cabinet ait un owner/admin initial,
	•	les objets métier soient cohérents et réutilisables pour les futurs rôles, invitations, abonnements et permissions.

⸻

Principes validés

1. Source de vérité identité
	•	Supabase Auth (auth.users) = source de vérité pour l’identité technique.
	•	Web et mobile utilisent le même auth.
	•	Pas de système parallèle d’auth côté backend.

2. Profil applicatif
	•	La table users reste le profil applicatif principal, alimenté depuis auth.users.
	•	La table user_settings continue d’être créée automatiquement à la création d’un user.

3. Entité métier principale
	•	L’abonnement, la structure et les droits sont portés par cabinet_accounts.
	•	Un user peut appartenir à un ou plusieurs cabinets à terme.
	•	Au sprint 1, tout nouveau signup crée 1 cabinet + 1 membership owner/admin.

4. Facturation
	•	La facturation sera portée par le cabinet, pas par le user isolé.
	•	Stripe ne sera pas créé au signup.
	•	La création Stripe sera déclenchée plus tard par Lisa, après la période d’essai de 14 jours, si l’utilisateur confirme qu’il souhaite continuer.

5. Rôle minimal requis au sprint 1
	•	Chaque cabinet doit avoir un owner/admin initial.
	•	C’est ce rôle qui pourra fermer/supprimer le compte plus tard.
	•	Les permissions fines par rôle seront détaillées dans un sprint ultérieur.

⸻

Flow cible Sprint 1

Signup web
	1.	L’utilisateur remplit le formulaire web.
	2.	auth.users est créé via Supabase Auth.
	3.	Email de vérification envoyé.
	4.	Après confirmation email et première connexion :
	•	création / mise à jour de users,
	•	création de user_settings,
	•	création du cabinet_accounts,
	•	création du cabinet_members avec rôle owner.
	5.	Le user peut ensuite se connecter sur web et mobile avec les mêmes credentials.

Signup mobile

Même logique que le signup web.

Login cross-platform
	•	Signup web => login app OK.
	•	Signup app => login web OK.

⸻

Décision de modélisation

Hiérarchie
	•	auth.users → identité technique
	•	users → profil applicatif
	•	cabinet_accounts → structure métier
	•	cabinet_members → lien user ↔ cabinet + rôle
	•	user_settings → préférences / settings initiaux

⸻

Tables concernées au Sprint 1

1. auth.users

Gérée par Supabase.

Champs clés utilisés :
	•	id
	•	email
	•	email_confirmed_at
	•	created_at
	•	raw_user_meta_data (si utile)

2. users

Rôle : profil applicatif lié à auth.users.

Champs minimaux attendus :
	•	id (PK, = auth.users.id)
	•	email
	•	full_name (nullable au début si nécessaire)
	•	preferred_language (optionnel)
	•	default_cabinet_account_id (nullable au moment de création, rempli après provisioning)
	•	onboarding_completed (bool, défaut false)
	•	created_at
	•	updated_at

3. user_settings

Rôle : préférences utilisateur.

Champs minimaux attendus :
	•	user_id (PK/FK vers users.id)
	•	settings existants conservés si déjà utilisés
	•	created_at
	•	updated_at

4. cabinet_accounts

Rôle : entité cabinet / compte principal métier.

Champs minimaux attendus au sprint 1 :
	•	id (uuid, PK)
	•	name (nom visible du cabinet)
	•	legal_name (nullable)
	•	slug (unique, nullable si généré plus tard)
	•	website (nullable)
	•	country_code (nullable)
	•	main_city (nullable)
	•	size (nullable)
	•	owner_user_id (FK vers users.id)
	•	status (trial, active, disabled, défaut trial)
	•	trial_started_at
	•	trial_ends_at
	•	created_at
	•	updated_at

5. cabinet_members

Rôle : lien entre users et cabinets.

Champs minimaux attendus :
	•	id (uuid, PK)
	•	cabinet_account_id (FK)
	•	user_id (FK)
	•	role (owner, admin, member ; au sprint 1 on utilise surtout owner)
	•	status (active, invited, disabled)
	•	created_at
	•	updated_at

Contraintes attendues :
	•	unicité (cabinet_account_id, user_id)

⸻

Provisioning attendu à la création d’un compte

Cas nominal

Quand un nouveau auth.users est confirmé et se connecte pour la première fois :
	1.	Créer / upsert users
	2.	Créer user_settings si absent
	3.	Créer un cabinet_accounts si aucun cabinet n’existe pour ce user
	4.	Créer un cabinet_members avec rôle owner
	5.	Renseigner users.default_cabinet_account_id

Idempotence requise

Le provisioning doit être idempotent.
Si relancé une seconde fois, il ne doit pas :
	•	recréer un second cabinet,
	•	dupliquer le membership,
	•	casser les données existantes.

⸻

Règles métier validées

Période d’essai
	•	14 jours d’essai gratuit à la création.
	•	cabinet_accounts.status = trial
	•	trial_started_at = created_at
	•	trial_ends_at = created_at + 14 jours

Activation facturation ultérieure

Après les 14 jours :
	•	Lisa demande confirmation à l’utilisateur,
	•	si OK => création Stripe customer + abonnement,
	•	la vue Facturation devient reliée au vrai portail Stripe.

⸻

Ce qu’on ne fait PAS dans ce sprint
	•	Permissions fines par rôle
	•	Invitations collaborateurs complètes
	•	Stripe customer / subscription active
	•	Portail Stripe réel
	•	Billing webhook
	•	Multi-cabinet complet
	•	Gestion avancée des rôles médicaux

⸻

Questions déjà tranchées
	•	Le royaume de la connexion = Supabase Auth
	•	users reste la projection applicative du user auth
	•	users doit être reliée à cabinet_accounts
	•	Chaque cabinet doit avoir un owner/admin initial
	•	La facturation sera portée par le cabinet
	•	Stripe sera déclenché plus tard par Lisa, pas au signup

⸻

Étapes d’implémentation prévues

Étape 1

Valider la structure cible exacte des tables du sprint 1.

Étape 2

Créer/ajuster les colonnes, contraintes, index et FKs nécessaires.

Étape 3

Implémenter le provisioning automatique idempotent.

Étape 4

Brancher signup/login web sur ce modèle.

Étape 5

Brancher signup/login mobile sur le même modèle.

Étape 6

Tester les scénarios croisés web ↔ mobile.

⸻

Implémentation validée — étape SQL structure Sprint 1

Décision

Nettoyage assumé des tables héritées pour repartir sur un socle strictement utile au sprint 1.

Tables retenues
	•	users
	•	cabinet_accounts
	•	cabinet_members (recréée proprement)

Principes appliqués
	•	suppression des colonnes héritées inutiles au sprint 1
	•	suppression des triggers hérités liés à Stripe / affiliate / statut legacy
	•	ajout des colonnes minimales métier nécessaires
	•	ajout des FK, index et contraintes utiles
	•	pas de déduplication des cabinets par email owner
	•	un email = un compte auth unique, mais plusieurs entités/cabinets pourront être créés plus tard depuis ce compte

Points d’attention
	•	migration destructive assumée
	•	à exécuter d’abord en environnement dev/staging
	•	vérifier ensuite le provisioning automatique après email confirmé

TODO doc

À compléter après exécution :
	•	timestamp d’exécution de la migration
	•	environnement cible exécuté
	•	résultat des tests signup web
	•	résultat des tests signup mobile
	•	résultat des tests provisioning idempotent
	•	écarts éventuels découverts
=================================================























À froid, ton backlog se découpe très bien en 4 blocs de lancement :

Bloc 1 — garde-fous produit indispensables

C’est ce qui évite une app bancale ou incohérente au launch :
	1.	intent hors cadre pro/médical => DONE
	2.  Fix lisa is thinking chat intro
	3.	paywall essai gratuit → continuité ou blocage
	4.	mode preview → données fake au départ, disparition dès première vraie donnée
	5.	vue Support humain propre avec Calendly bien intégré
	  

Bloc 2 — tuyauterie d’orchestration interne

C’est ce qui rend Lisa exploitable côté ops :
5. payload + webhook pour brief automation
6. payload + webhook pour suivi des tâches
7. workflows n8n liés aux webhooks, y compris user_facts

Bloc 3 — capacités cœur produit

C’est ce qui transforme Lisa en vraie assistante cabinet :
8. PJ + notes audio
8bis. ajouter insight études sur symptomes (anatomie)
9. intégrations Google / Outlook / Doctolib
10. flow complet gestion des mails cabinet

Bloc 4 — profondeur produit + crédibilité

C’est ce qui fait monter le niveau perçu :
11. vue Patients réellement animée
12. vue Dashboard
13. documentation HeyLisa pour alimenter Lisa

Mon avis franc sur l’ordre de reprise

Au redémarrage, je te conseille qu’on reparte dans cet ordre précis :

A. Hors cadre + paywall + preview
B. Support humain
C. Webhooks internes automation / tâches / user_facts
D. PJ + audio
E. Agendas + mails cabinet
F. Patients + dashboard
G. Documentation HeyLisa

Pourquoi cet ordre ?
Parce que A+B+C sécurisent le launch.
Le reste augmente la puissance produit, mais ne doit pas casser le cadre.
























































































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


✅ 2026-02-12 — Onboarding / Activation d’agents (v1) + Push notif ✅

Objectif

Quand un user active un agent (ex: Personal Assistant, Ultimate, Medical Assistant…), Lisa doit :
	1.	relancer la conversation proactivement dans le chat (message écrit en DB),
	2.	envoyer une push notif fiable,
	3.	marquer l’onboarding de cet agent (state machine simple) pour piloter la suite via l’orchestrator.

⚠️ Règle produit : on ne parle jamais “d’abonnement / paiement / plan”.
On parle relation + nouveau champ des possibles.

⸻

Source of truth “abonnement agent”

La table public.lisa_user_agents est la source de vérité :
	•	À la création de compte : tous les agents sont créés en status='off'
	•	Un user a “vraiment” activé un agent uniquement si status='active'
	•	Onboarding attaché à chaque paire (user_id, agent_key) via :
	•	onboarding_status ∈ { NULL, started, complete }
	•	pas de pending (supprimé)

⸻

State machine onboarding_status

Backend tool : app/tools/onboarding_update.py

Règles :
	•	Valeurs autorisées : NULL | started | complete
	•	Jamais downgrade complete -> started
	•	complete gagne toujours
	•	started : set si NULL ou started
	•	NULL : autorisé uniquement si pas déjà complete

⸻

Déclencheur n8n (activation agent)

Un webhook n8n écoute les INSERT/UPDATE sur lisa_user_agents (payload pg_net).

On normalise l’événement et on déclenche un message uniquement dans ces cas :

Scénarios (v1)
	•	insert_fresh
type=INSERT AND status_new=active AND onboarding_new IS NULL
	•	update_fresh (cas le plus courant)
type=UPDATE AND status_old=off AND status_new=active AND onboarding_new IS NULL
	•	update_recover (correction / reprise)
type=UPDATE AND status_old=off AND status_new=active AND onboarding_old IS NOT NULL

Flag “nouvelle activation vs réactivation”
On dérive un bool “déjà connu” pour aider Lisa :
	•	is_reactivation = (onboarding_old = 'started' OR onboarding_old = 'complete')
	•	sinon is_reactivation = false

⸻

Génération du message (Lisa)

Lisa reçoit :
	•	agent_key activé
	•	scenario (insert_fresh / update_fresh / update_recover)
	•	is_reactivation (bool)
	•	les 10 derniers messages du chat (avec sent_at) pour respecter tutoiement/vouvoiement et continuité

But : un seul message chaleureux + 1 question claire qui oriente la suite.
	•	Personal Assistant : “never alone again” (connexion forte)
	•	Pro mode : “prise de poste maintenant ?” (oriente “intent=Onboarding”)
	•	Ultimate : “champ des possibles” + “on commence par quoi ?”
	•	Nuance subtile si réactivation (is_reactivation=true) : ton “content de te retrouver / on reprend”.

⸻

Écriture du message (DB source of truth)

On écrit le message dans public.conversation_messages (sender Lisa).

➡️ Ce write déclenche automatiquement :
	•	le trigger conversation_messages_enqueue_push
	•	qui appelle public.enqueue_push(...)
	•	qui insère un job dans public.push_outbox

On n’utilise pas proactive_messages_queue pour ce flow (mis de côté pour v1).

⸻

Push notifications (DEV et PROD)

Mécanisme : push_outbox + Edge Function “dispatcher” + cron Supabase.

Edge Function
	•	PROD : push-dispatcher
	•	DEV : push-dispatcher-dev
	•	Elle fait :
	1.	pop_push_outbox(p_limit=25)
	2.	should_send_push(user_id, kind)
	3.	récupère les tokens dans push_devices
	4.	envoie à Expo (https://exp.host/--/api/v2/push/send)
	5.	mark push_outbox.status='sent' ou failed

Cron Supabase
Un cron job appelle la function toutes les minutes.

Point critique (DEV)
La function doit avoir :
	•	verify_jwt = false

Sinon : 401 et aucun push ne part (la function ne s’exécute même pas).

⸻

Contrat de fin de flow (Definition of Done)

Le flow est considéré terminé quand :
	1.	un message Lisa est visible dans conversation_messages,
	2.	une ligne est créée dans push_outbox (status queued puis sent),
	3.	la push arrive sur le téléphone,
	4.	on set onboarding_status='started' pour (user_id, agent_key) via onboarding_update.

⸻

Files / composants impliqués (v1)
	•	Backend:
	•	app/tools/onboarding_update.py
	•	DB:
	•	public.lisa_user_agents
	•	public.conversation_messages
	•	public.push_outbox
	•	triggers conversation_messages_enqueue_push
	•	RPC: enqueue_push, pop_push_outbox, should_send_push
	•	Supabase Edge:
	•	supabase/functions/push-dispatcher-dev/index.ts (DEV)
	•	cron “push-dispatcher-dev” (every minute)
	•	n8n:
	•	Webhook onboarding-start + normalizer + writer

✅ Checklist migration DEV → PROD (zéro surprise)

1) Base de données (PROD)
	•	Vérifier que les triggers existent sur public.conversation_messages :
	•	conversation_messages_enqueue_push
	•	(outbox_on_lisa_tech_issue si tu veux garder le monitoring)
	•	(trg_update_intro_smalltalk si toujours utilisé)
	•	Vérifier que les RPC existent :
	•	enqueue_push, pop_push_outbox, should_send_push, upsert_push_device_safe

2) Edge Function (PROD)
	•	Déployer la function push-dispatcher (ou vérifier qu’elle est bien la bonne version)
	•	Vérifier les env vars côté Supabase :
	•	SUPABASE_URL
	•	SUPABASE_SERVICE_ROLE_KEY
	•	Vérifier que verify_jwt = false (sinon 401 silencieux)

3) Cron Supabase (PROD)
	•	Vérifier le cron job push-dispatcher :
	•	schedule * * * * * (every minute)
	•	type = “Supabase Edge Function”
	•	edge function = push-dispatcher
	•	method POST
	•	timeout OK (1000ms suffit)

4) n8n (PROD)
	•	Le webhook DB → n8n (trigger lisa_user_agents) pointe bien sur l’URL prod (pas dev)
	•	Les credentials Supabase utilisés dans n8n = service role prod (sinon insert bloqué par RLS)

5) Test “bout en bout” avant d’ouvrir les vannes
	1.	Dans PROD, force un agent status: off -> active pour ton user test
	2.	Attends :
	•	1 ligne dans conversation_messages
	•	1 ligne push_outbox queued puis sent
	3.	Confirme : push reçue sur le tel
	4.	Confirme : onboarding_status passé à started

6) Plan B (si push ne part pas)
	•	Si push_outbox reste en queued :
	•	regarder les logs Edge Function : erreur 401 / no_tokens / expo_XXX
	•	Si status=failed + error=no_tokens :
	•	le souci est côté push_devices (token absent ou pas “ExponentPushToken…”)

7) Règle anti-casse (très importante)
	•	On migre en copiant strictement :
	•	edge function + cron
	•	triggers + RPC
	•	et on teste avec un user test avant toute activation réelle.

8) Definition of Done PROD

✅ Push reçue + ✅ message chat écrit + ✅ onboarding_status set started


✅ Convention unique ajout webhook N8N (obligatoire)

	1.	Créer le path env

	•	N8N_<EVENT>_WEBHOOK_PATH=<path-sans-leading-slash>

	2.	Créer un wrapper python

	•	app/integrations/n8n_<event>.py :
	•	appelle fire_n8n_webhook(... path_env="N8N_<EVENT>_WEBHOOK_PATH")

	3.	Appel dans le code

	•	fire-and-forget si non critique :
	•	asyncio.create_task(fire_<event>_webhook(payload))

	4.	n8n

	•	Le webhook node utilise exactement le même path que N8N_<EVENT>_WEBHOOK_PATH
	•	(optionnel) si N8N_WEBHOOK_SECRET est défini, vérifier X-Webhook-Secret



⚠️ NOTE DÉPLOIEMENT SUPABASE FUNCTIONS

Toujours utiliser --use-api pour éviter dépendance Docker
Toujours utiliser --prune en DEV uniquement (supabase functions deploy --use-api --prune)

=====================================

NOTE POUR LE 1ER PUSH PROD BACKEND DB

N1.
en PROD, il faudra exécuter la même migration SQL (table app_config + fonctions + trigger rewrite) et mettre app_config.n8n_webhook_base_url = https://n8n.heylisa.io/webhook.
(update public.app_config
set value = 'https://n8n.heylisa.io/webhook',
    updated_at = now()
where key = 'n8n_webhook_base_url';)

Voilà ce qui a été fait en DEV : 
ce trigger crée la config + les fonctions + remplace le trigger existant.


-------------
-- 1) Table de config (1 ligne)
create table if not exists public.app_config (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);

-- Base URL pour DEV
insert into public.app_config(key, value)
values ('n8n_webhook_base_url', 'https://n8n-dev.heylisa.io/webhook')
on conflict (key) do update set
  value = excluded.value,
  updated_at = now();

-- 2) Helper: récupérer une valeur de config
create or replace function public.get_app_config(p_key text, p_default text default null)
returns text
language sql
stable
as $$
  select coalesce(
    (select value from public.app_config where key = p_key),
    p_default
  );
$$;

-- 3) Helper: construire l'URL finale (base + path)
create or replace function public.n8n_webhook_url(p_path text)
returns text
language plpgsql
stable
as $$
declare
  base_url text;
  clean_base text;
  clean_path text;
begin
  base_url := public.get_app_config('n8n_webhook_base_url', null);
  if base_url is null or length(trim(base_url)) = 0 then
    raise exception 'Missing app_config.n8n_webhook_base_url';
  end if;

  -- normalisation simple des slashes
  clean_base := regexp_replace(trim(base_url), '/+$', '');
  clean_path := regexp_replace(coalesce(trim(p_path), ''), '^/+', '');

  return clean_base || '/' || clean_path;
end;
$$;

-- 4) Caller: wrapper autour de supabase_functions.http_request
-- Note: http_request attend headers/body en TEXT (JSON string)
create or replace function public.call_n8n_webhook(
  p_path text,
  p_payload jsonb,
  p_timeout_ms int default 5000
)
returns void
language plpgsql
as $$
declare
  url text;
  headers text;
  body text;
begin
  url := public.n8n_webhook_url(p_path);

  headers := '{"Content-type":"application/json"}';
  body := coalesce(p_payload, '{}'::jsonb)::text;

  perform supabase_functions.http_request(
    url,
    'POST',
    headers,
    body,
    p_timeout_ms::text
  );
end;
$$;

-- 5) Trigger function spécifique pour onboarding-start
create or replace function public.trg_lisa_user_agents_onboarding_start()
returns trigger
language plpgsql
as $$
begin
  -- payload = NEW row + action
  perform public.call_n8n_webhook(
    'onboarding-start',
    jsonb_build_object(
      'table', TG_TABLE_NAME,
      'op', TG_OP,
      'new', to_jsonb(NEW),
      'old', case when TG_OP = 'UPDATE' then to_jsonb(OLD) else null end
    ),
    5000
  );

  return NEW;
end;
$$;

-- 6) Remplacer le trigger existant (celui qui a l'URL en dur)
drop trigger if exists "addon_onboarding-start" on public.lisa_user_agents;

create trigger "addon_onboarding-start"
after insert or update on public.lisa_user_agents
for each row
execute function public.trg_lisa_user_agents_onboarding_start();
--------


====================================

N2. NOTE (push prod checklist) : supprimer progressivement les variables legacy N8N_*_WEBHOOK_URL une fois que base+path est validé partout (sinon un jour quelqu’un remet une URL complète “au hasard” et tu reperds la standardisation).

N3. NOTE (push prod checklist) : vérifier que N8N_WEBHOOK_BASE_URL diffère bien entre Railway DEV et PROD (n8n-dev vs n8n).

N4. NOTE (push prod checklist) : s’assurer que le webhook user-fact/catcher existe côté n8n prod avec le même path, et que le secret correspond.

N5. NOTE (push prod checklist) : vérifier que N8N_WEBHOOK_BASE_URL est bien https://n8n.heylisa.io/webhook sur Railway PROD.

N6. NOTE (push prod checklist)
	•	DROP sur PROD au moment du push (ou écrasement via migrations DEV), sinon PROD continuera d’appeler des webhooks morts/externes.
	•	Rotate le secret x-addon-secret qui apparaît dans le SQL dump (il a fuité dans ton diff local, donc par principe on le considère compromis).

Je te donne déjà le SQL “propre” à garder pour le jour du push prod (tu ne l’exécutes pas maintenant si tu veux garder l’état PROD intact jusqu’au go-live).

-- NOTE PUSH PROD: cleanup legacy n8n triggers (neatik-ai.app.n8n.cloud)

drop trigger if exists addon_event on public.lisa_user_agents;
drop trigger if exists new_prospect_email_chat on public.users;
drop trigger if exists proactive_messages on public.proactive_events_outbox;
drop trigger if exists send_proactive_messages on public.proactive_messages_queue;
drop trigger if exists tool_event on public.lisa_user_integrations;


📜 Journal d’implémentation

✅ 2026-02-14 — RevenueCat Offerings + Supabase Realtime + app_config (standardisation PROD-ready)

Contexte / Pourquoi
On a observé deux problèmes “invisibles mais mortels” :
	1.	RevenueCat : un produit peut exister (products + entitlements OK) mais ne pas être présent dans l’Offering → le paywall / pricing / purchase se comportent mal (fallback, produit manquant, confusion côté UI).
	2.	Supabase Realtime : le front peut afficher SUBSCRIBED côté channel, mais ne recevoir aucun event si la table n’est pas ajoutée à la publication supabase_realtime → donc pas de toast, pas de sync instant, et debug très trompeur.

En parallèle, on a acté une standardisation propre pour les webhooks n8n via public.app_config afin d’éviter les URLs hardcodées et les divergences DEV/PROD.

⸻

1) RevenueCat — Règle Offering (piège confirmé)

Fait important :
	•	Avoir un Product + un Entitlement ne suffit pas.
	•	Pour être “achetable/affichable” correctement, le produit doit être ajouté dans l’Offering active (ex: live_default), via un Package.

Symptômes typiques quand le produit n’est pas dans l’Offering :
	•	Produit manquant dans la liste offerings.current.availablePackages
	•	Prix incohérent (fallback ou mapping sur un autre produit)
	•	Comportement “ça marche pour 3 modules mais pas pour Ultimate” → exactement ce qu’on a vu.

Note UI RevenueCat (nouveau champ Identifier) :
RevenueCat a introduit/renforcé la notion d’Identifier pour les packages.
Tu n’es pas obligé d’utiliser les “preset” type monthly si RC ne te le propose pas : tu peux créer un identifier custom (ex: ultimate_monthly) et l’utiliser en code via l’identifiant du package (RC loggue d’ailleurs : custom duration).

DoD RC :
	•	offerings.current.availablePackages contient bien le produit attendu
	•	le log products liste bien le produit (ultimate_assistant etc.)
	•	le paywall propose le bon prix et l’achat fonctionne

⸻

2) Supabase Realtime — Pourquoi le toast ne s’affichait pas

Ce qui était trompeur :
	•	côté app : logs subscribe status SUBSCRIBED ✅
	•	côté Supabase Dashboard (Replication view) : rien (normal, car ce screen “Replication” ≠ “Realtime”)
	•	résultat : aucun event reçu, donc aucun toast.

Cause racine :
La table public.lisa_user_agents n’était pas incluse dans la publication supabase_realtime.

✅ Fix appliqué :
alter publication supabase_realtime add table public.lisa_user_agents;

Important :
	•	alter table ... replica identity full; est utile dans certains cas (UPDATE/DELETE complets), mais ne suffit pas si la table n’est pas dans supabase_realtime.
	•	Le fait que la “vue replication” soit “vide” n’est pas un indicateur fiable pour Realtime.

DoD Realtime :
	•	l’app reçoit bien les events postgres_changes sur lisa_user_agents
	•	le toast peut se déclencher (activation/désactivation)

⸻

3) Toast “Mode activé” — Règle anti-faux-positif (sécurité produit)

Objectif : aucun toast ne doit s’afficher “par erreur”.

Décision actée :
	•	Le toast est déclenché sur event Realtime DB (lisa_user_agents status change)
	•	MAIS on ne “célèbre” l’activation que si RevenueCat confirme que l’entitlement est actif.

Donc :
	•	DB dit active ✅
	•	RC dit entitlement actif ✅ → toast success
	•	sinon → toast skip + log debug

Cela évite :
	•	activation fantôme (DB activée mais achat non confirmé)
	•	race conditions
	•	incohérences RC/DB

⸻

4) Standardisation Webhooks n8n via public.app_config (DEV/PROD clean)

But :
Ne plus hardcoder des URLs n8n dans des triggers SQL.
Avoir :
	•	1 base URL configurable par environnement (DEV vs PROD)
	•	des paths stables (onboarding-start, etc.)
	•	un point de vérité unique.

✅ Implémenté en DEV :
	•	public.app_config (key/value)
	•	public.get_app_config(key, default)
	•	public.n8n_webhook_url(path)
	•	public.call_n8n_webhook(path, payload)
	•	trigger addon_onboarding-start basé sur call_n8n_webhook('onboarding-start', payload)

Règle PROD (au moment du push) :
Mettre n8n_webhook_base_url à la valeur PROD :
update public.app_config
set value = 'https://n8n.heylisa.io/webhook',
    updated_at = now()
where key = 'n8n_webhook_base_url';


⸻

5) Checklist rapide DEV → PROD (sur ce scope)

Realtime
	•	public.lisa_user_agents est dans supabase_realtime

RevenueCat
	•	produits ajoutés dans l’Offering active
	•	packages identifiers cohérents (ex: ultimate_monthly)
	•	paywall affiche prix correct

n8n + app_config
	•	app_config.n8n_webhook_base_url = PROD
	•	triggers SQL pointent sur call_n8n_webhook() (pas URL en dur)
	•	paths n8n PROD existants (ex: onboarding-start)

Sécurité
	•	plan de rotation du secret webhook si une valeur a fuité dans un dump/diff

⸻

6) Décisions actées (à ne pas rediscuter au prochain bug 😄)
	•	RevenueCat : Offering obligatoire sinon produit invisible/mal mappé.
	•	Supabase : Realtime = publication supabase_realtime, pas l’écran “Replication”.
	•	UI : toast “Mode activé” = DB event + validation RC, jamais seulement DB.
	•	Webhooks : URLs n8n centralisées via app_config, base+path, pas de hardcode.



---

## ✅ Décisions actées — Chat Flow, State Resolver, Discovery (février 2026)

Ce bloc sert de **référence** : si un bug revient, on compare au présent document avant de “réinventer”.

---

### 1) Pipeline Chat (v1) — source of truth DB

**Entrée unique**
- `POST /v1/chat/message` avec `{ conversation_id, user_message_id }`

**Source de vérité**
- Les messages (user + Lisa) sont **persistés en DB** (`public.conversation_messages`).
- Le front est **aligné DB** (UI optimiste, puis reload DB).

**Étapes de traitement backend**
1. Charge le message user (DB) + checks (ownership best-effort)
2. Idempotence (si `assistant_message_id` déjà en metadata → renvoie la réponse existante)
3. Charge le contexte (`load_context_light` minimum pour router)
4. Résout l’état (`resolve_state`) + gates (`apply_gates`)
5. Construit un plan (fastpath ou orchestrator)
6. Exécute le plan via `PlanExecutor`
7. Nettoie les flags de fin de message (`extract_and_clean_message_flags`)
8. Persiste le message Lisa + metadata
9. Post-actions (update discovery_status / smalltalk state) + webhooks n8n (fire-and-forget)

---

### 2) State Resolver (v1) — déterministe, avant LLM

**Objectif**
- Déterminer l’état conversationnel **sans** dépendre du LLM.
- Autoriser des “fastpaths” sur des cas simples et stables.

**États clés**
- `smalltalk_intro`
- `discovery`
- `quota_blocked`

**Règle**
- `resolve_state(ctx)` produit une décision avec :
  - `state`
  - `fastpath_allowed` (bool)
  - `quota_blocked` (bool)
  - `transition_window` / `transition_reason` (facultatif)

**Gates**
- `apply_gates(ctx)` applique les règles business non négociables (ex: warning soft paywall).

---

### 3) Fastpath (v0) — plans figés, low-risk

Quand `fastpath_allowed = true`, on ne demande pas à l’orchestrator de “réinventer le plan”.
On génère un plan **déterministe** :

- `A: tool.db_load_context` (light)
- (optionnel) `S: tool.docs_chunks` (uniquement si docs nécessaires)
- `D: agent.response_writer`

But : **stabilité**, latence basse, moins de surface de bug.

---

### 4) Discovery — règles de statut et séquence AHA

Discovery est pilotée par `public.user_settings.discovery_status`.

**États autorisés**
- `to_do` (par défaut)
- `pending` (la séquence est engagée : on envoie la mini-démo)
- `complete` (validé)
- `aborted` (user a dit non)

**Transitions (source de vérité = flags du message Lisa)**
- Quand Lisa **POSE** la question de démo → `aha_request=true`
  - Backend : `discovery_status` passe de `to_do` → `pending`
- Quand Lisa **TERMINE** la mini-démo → `aha_moment=true`
  - Backend : `discovery_status` passe → `complete` + `discovery_completed_at=now()`
- Si user refuse → `onboarding_abort=true`
  - Backend : `discovery_status` passe → `aborted` (sauf si déjà complete)

**Important**
- Les flags `aha_request / aha_moment / onboarding_abort` :
  - ne doivent **jamais** être stockés dans `conversation_messages.content`
  - sont **strippés** avant persistance (via `extract_and_clean_message_flags`)
  - sont stockés en metadata : `provider.flags`

---

### 5) Docs (RAG light) — règle stricte : seulement quand utile

**Objectif**
- Injecter de la doc produit uniquement quand ça apporte quelque chose, sans polluer les échanges trivials.

**Source**
- `ctx.docs.scopes_all` = liste des scopes disponibles (ex: `discovery.value_proposition`, etc.)

**Règle de sécurité**
- Le ResponseWriter ne reçoit des docs **que** lorsque `discovery_status == 'pending'`.
- Pas de docs pour “poser la question AHA” (intent `aha_request`) : docs inutiles à ce moment.

**Sélection de scopes (discovery)**
- On choisit **exactement 2 scopes** :
  1) `discovery.value_proposition` (toujours)
  2) `discovery.<agent_key>` si un seul agent actif et scope existant, sinon `discovery.default_all_profiles`

Implémentation : `_pick_discovery_doc_scopes(ctx)`

---

### 6) Plan “Discovery Pending” (v1) — stable et tracé

Quand `discovery_status == pending`, le plan exécuté est :

- `A: tool.db_load_context` (medium possible via orchestrator, sinon light)
- `B: tool.quota_check`
- `S: tool.docs_chunks` (scopes sélectionnés)
- `D: agent.response_writer` (intent = `discovery_pending`)

Le log doit montrer :
- `chat.docs_chunks.db` avec `rows_count > 0`
- `chat.response_writer.docs_chunks` avec `dc_ok=true`

---

### 7) Ce qu’on accepte “imparfait” (pour avancer vite)

- Le style de la phrase d’ouverture Discovery peut être perfectible.
  - Cause connue : contrainte prompt “1 phrase d’ouverture personnalisée”.
  - On bétonnera après plusieurs runs.
- On privilégie :
  - la stabilité du flow,
  - la bonne transition des statuts,
  - la bonne injection docs uniquement en pending,
  - la traçabilité par logs.

---

---

## 🔒 Contrat de déclenchement — States & Flags (v1)

Cette section décrit **quand** chaque state / flag doit s’activer.
👉 Source of truth : `ctx` (chargé par context_loader) + `resolve_state()` + `apply_gates()`.

---

### A) `state = smalltalk_intro`

**Déclenchement (conditions minimales)**
- `ctx.gates.smalltalk_intro_eligible (derived)== true`

**Intuition**
- L’utilisateur n’a pas encore “le socle minimum” (facts manquants), donc on privilégie une intro guidée.

**Effets**
- `mode = "smalltalk_intro"`
- `intent = "smalltalk_intro"`
- `context_level` forcé à `light` (pas besoin de charger le monde entier)
- Pas d’injection docs / web (sauf évolution future explicitement décidée)

**Override (même si eligible)**
- Si `resolve_state()` détecte un état prioritaire (ex: `quota_blocked`) → smalltalk_intro saute.
- (Option future) urgences / questions sensibles peuvent bypass l’intro.

---

### B) `state = discovery`

**Déclenchement**
- `ctx.settings.discovery_status` ∈ {`"pending"`, `"to_do"`} **ET** règles de sequencing discovery satisfaites
  - Dans notre flow actuel : on entre en discovery dès qu’on a basculé dans la séquence (pending ou forced)

**Règle importante**
- `discovery_status == "pending"` ⇒ intent final attendu côté writer : `discovery_pending`
- `discovery_status != "pending"` (ex: `to_do`) ⇒ intent final attendu : `discovery` (question AHA / cadrage)

**Effets**
- `mode = "discovery"`
- Le plan peut inclure `docs_chunks` **uniquement** si on est en `pending` (cf. section “Docs gating”).

---

### C) `state = quota_blocked`

**Déclenchement**
- `ctx.user_status.free_quota_used >= ctx.user_status.free_quota_limit`
  - Exemple : limit=8 → blocked à partir de 8 (ou +)

**Effets**
- `mode = "paywall"`
- intent typique : `quota_blocked`
- Le ResponseWriter doit produire une réponse courte + UX paywall (selon conventions front).

---

### D) `fastpath_allowed`

**Déclenchement**
- `resolve_state()` positionne `fastpath_allowed=true` **uniquement** sur des états “low risk” :
  - `smalltalk_intro`
  - `quota_blocked`
  - (éventuellement) `discovery` si on décide de le rendre déterministe plus tard

**Effet**
- On n’appelle pas l’orchestrator.
- On construit un plan stable (A → (S?) → D).

---

## 🧩 Flags / Decisions secondaires (v1)

### 1) `soft_paywall_warning`

**Déclenchement**
- `apply_gates(ctx).soft_paywall_warning == true`
- Cas typique :
  - user non-pro
  - `free_quota_used == free_quota_limit - 1`
  - Exemple : limit=8 → warning à used=7

**But**
- Prévenir **sans bloquer** (message “dernier message gratuit” / warning soft).

**Effet**
- Transmis au ResponseWriter via `inputs.soft_paywall_warning`
- N’impacte pas le state (on peut être en discovery/smalltalk/normal avec warning).

---

### 2) `transition_window` + `transition_reason`

**Déclenchement**
- `resolve_state()` met `transition_window=true` quand on est dans une zone où :
  - l’utilisateur est en train de changer de phase,
  - et on veut “aider la transition” (ex: bascule onboarding → normal, ou activation agent → reprise).
- `transition_reason` est une string courte explicative (debug + guidance writer).

**But**
- Aider Lisa à être fluide (“OK, on passe à…”), sans que le LLM invente une logique.

**Effet**
- Transmis au ResponseWriter :
  - `inputs.transition_window`
  - `inputs.transition_reason`

---

### 3) `need_web`

**Déclenchement**
- Décidé par l’orchestrator (LLM) **ou** forcé par règles futures.
- v1 : si `need_web=true` alors le plan inclut un node `tool.web_search`.

**Règle**
- En fastpath : `need_web=false` (forcé)

---

## 🏁 Flags fin de message (Discovery AHA)

Ces flags sont **écrits dans la sortie brute du ResponseWriter** puis **strippés** avant persistance.

### `aha_request=true`
**Déclenchement**
- Quand Lisa pose la question “mini-démo / AHA” (le moment où elle demande l’autorisation/validation).

**Effet DB**
- Backend met `user_settings.discovery_status = 'pending'`
  - seulement si status précédent ∈ {`to_do`, `""`, NULL}

---

### `aha_moment=true`
**Déclenchement**
- Quand le user a répondu “oui” et que Lisa a effectivement produit la mini-démo (moment “OK c’est bon, on passe à la suite”).

**Effet DB**
- Backend met :
  - `discovery_status = 'complete'`
  - `discovery_completed_at = now()`

---

### `onboarding_abort=true`
**Déclenchement**
- Quand le user refuse explicitement la mini-démo.

**Effet DB**
- Backend met `discovery_status = 'aborted'`
  - sauf si déjà `complete`

---

## 📌 Docs gating (règle non négociable)

**Le ResponseWriter ne reçoit `docs_chunks` que si :**
- `ctx.settings.discovery_status == 'pending'`

**Donc :**
- Pas de docs si intent = “poser la question AHA” (`aha_request`)
- Docs uniquement pendant l’exécution de la séquence `discovery_pending`

---


---

## 🧭 Onboarding State (v1) — Déterministe & Global

Onboarding est un state dominant déclenché uniquement si :

- has_paid_active == true
- ET onboarding_target != none
- ET discovery_status == "complete"

👉 Onboarding ne peut jamais coexister avec Discovery.
👉 Quota / paywall ne jouent aucun rôle dans le state machine.

---

### 🎯 Objectif Onboarding

Deux axes :

1. Compréhension capacités (ce que Lisa peut / ne peut pas faire)
2. Contexte minimum pour être pertinente

---

## 🧠 Modèle global

Table dédiée : `public.user_onboarding`

Champs clés :

- level_max: none | personal | pro  
  (pro est terminal, jamais downgradé)

- target: personal | pro | null  
  (null = pas d’onboarding actif)

- status: started | complete | null

- user_msgs_since_started: int  
  (compteur déterministe, reset à chaque completion)

---

## 🧩 Calcul déterministe de onboarding_target

À chaque tour :

1) Si discovery_status != complete → target = null
2) Sinon si has_paid_active == false → target = null
3) Sinon si level_max == 'pro' → target = null
4) Sinon si has_pro_mode_active == true → target = 'pro'
5) Sinon → target = 'personal'

---

## ✅ Completion Rules

### 🔹 Onboarding Personal

Condition unique :

- user_msgs_since_started > 10

→ level_max = personal  
→ status = complete  
→ user_msgs_since_started = 0

---

### 🔹 Onboarding Pro

Complete si l’un des cas suivants :

- action_request_detected == true
- OR connected_tools_count >= 1
- OR fallback : user_msgs_since_started > 10

→ level_max = pro (terminal)  
→ status = complete  
→ user_msgs_since_started = 0

---

## 🔁 Reset Logic

Le compteur user_msgs_since_started est utilisé pour personal ET pro.

Il doit être remis à 0 :

- quand onboarding personal passe complete
- quand onboarding pro passe complete

---

## 🔍 Données nécessaires (Context Loader)

Les champs suivants doivent être disponibles dans ctx.gates :

- has_paid_active  
  = (user_status.is_pro == true)

- has_pro_mode_active  
  = EXISTS (
        SELECT 1 FROM lisa_user_agents
        WHERE user_id = ...
        AND status = 'active'
        AND agent_key != 'personal_assistant'
    )

- connected_tools_count  
  = EXISTS (
        SELECT 1 FROM lisa_user_integrations
        WHERE user_id = ...
    )

⚠️ Important :
Même si un user déconnecte un tool, sa présence historique dans lisa_user_integrations suffit à valider connected_tools_count.

---

## 🏁 Priority Order (State Resolver)

1. onboarding
2. smalltalk_intro
3. discovery
4. ongoing_pro
5. ongoing_personal (fallback)

Impossible d’avoir un user sans state.


⚡ Fastpath / Orchestrator Split (v1) — Architecture d’Escalade Déterministe

Le moteur de conversation repose sur un double chemin contrôlé :
	1.	Fastpath (réponse rapide)
	2.	Orchestrator (planification complète)

L’objectif :
→ Minimiser la latence quand possible
→ Garantir cohérence state machine quand nécessaire

⸻

🧭 Router Global

Le Router décide du provider primaire :
	•	"fastpath"
	•	"orchestrator"

Ce choix est effectué avant l’appel au ResponseWriter.

⸻

⚡ Fastpath — Règle stricte

Le fastpath est utilisé uniquement pour des cas simples :
	•	small_talk
	•	amabilities
	•	general_question

Il fournit :
	•	contexte minimal
	•	10 derniers messages
	•	aucun plan
	•	aucun tool complexe

⚠️ Le fastpath n’interprète pas le state machine.
⚠️ Il ne décide pas d’intent.
⚠️ Il ne fait aucune orchestration.

⸻

🧠 ResponseWriter (Lisa) — Responsabilité exacte

Lisa ne route pas.

Elle fait uniquement :
	1.	Produire une réponse.
	2.	OU déclencher une escalade déterministe.

Elle n’appelle jamais l’orchestrator elle-même.

⸻

🚨 Escalade Déterministe (Fastpath uniquement)

Si Lisa estime que :
	•	la demande ne correspond pas strictement à
small_talk / amabilities / general_question
	•	OU que le contexte est insuffisant
	•	OU que la demande nécessite une logique plus complexe

[[ESCALATE]]

🔒 Sécurité Anti-Dérive

Règle absolue :

Si la chaîne [[ESCALATE]] apparaît N’IMPORTE OÙ dans la réponse du LLM
→ escalade immédiate.

Même si le LLM a ajouté du texte autour.

Aucune heuristique.
Aucune interprétation.
Aucun motif.

⸻

🔁 Cycle d’Escalade
	1.	Fastpath appelle ResponseWriter
	2.	ResponseWriter renvoie [[ESCALATE]]
	3.	PlanExecutor retourne { escalate: true }
	4.	chat.py relance automatiquement l’orchestrator
	5.	L’orchestrator choisit l’intent correct
	6.	Exécution complète avec plan + tools

⚠️ Important :
Escalade possible uniquement si route_source == fastpath.

L’orchestrator ne peut jamais escalader.
Donc aucune boucle infinie possible.

⸻

🧱 Séparation des Responsabilités

Router

Décide du provider primaire.

Fastpath

Réponse rapide, aucun raisonnement complexe.

Orchestrator
	•	Résout le state
	•	Détermine l’intent
	•	Prépare le plan
	•	Injecte tools/context/web/docs

ResponseWriter
	•	Génère la réponse
	•	OU déclenche l’escalade
	•	Ne fait aucune logique métier

⸻

🛡️ Garanties Architecture
	•	Pas de boucle possible
	•	Pas de double routage
	•	Pas d’auto-réinjection
	•	Pas d’ambiguïté de responsabilité
	•	Escalade déterministe
	•	State machine centralisée dans orchestrator

⸻

🧠 Résumé Conceptuel

Fastpath = Optimisation
Orchestrator = Intelligence
ResponseWriter = Production
Escalade = Garde-fou

🗺️ Diagramme Global — Flow Conversationnel

                    ┌────────────────────┐
                    │    USER MESSAGE     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │       ROUTER        │
                    │  (choix provider)   │
                    └───────┬───────┬────┘
                            │       │
                 fastpath ──┘       └── orchestrator ---------
                            │                                 |
                            ▼								  |
                ┌────────────────────┐						  |
                │  RESPONSE WRITER   │						  |
                │       (Lisa)       │						  |
                └───────┬────────────┘						  |
                        │									  |
         ┌──────────────┴──────────────┐					  |
         │                             │				      |
         ▼                             ▼					  |
   Réponse normale              [[ESCALATE]]				  |
         │                             │					  |	
         ▼                             ▼					  |
      USER                     ┌────────────────────┐		  |
                               │   PLAN EXECUTOR    │		  |
                               └─────────┬──────────┘		  |
                                         │ escalate:true	  |
                                         ▼					  |
                               ┌────────────────────┐		  |
                               │   ORCHESTRATOR     │_________|
                               │  (intent + plan)   │		 
                               └─────────┬──────────┘		 
                                         │
                                         ▼
                               ┌────────────────────┐
                               │   PLAN EXECUTOR    │
                               └─────────┬──────────┘
                                         │
                                         ▼
                               ┌────────────────────┐
                               │  RESPONSE WRITER   │
                               │     (orchestr.)    │
                               └─────────┬──────────┘
                                         │
                                         ▼
                                       USER


🧠 Garanties Structurelles
	•	Escalade possible uniquement si provider == fastpath
	•	Orchestrator ne peut jamais escalader
	•	Donc aucune boucle infinie
	•	State machine centralisée uniquement dans orchestrator
	•	Fastpath = optimisation, jamais décisionnel profond


# Registry
USER_BLOCKS_BY_INTENT: Dict[str, UserPromptBlock] = {
    "smalltalk_intro": SMALLTALK_INTRO,
    "discovery": DISCOVERY,
    "discovery_pending": DISCOVERY_PENDING,
    "onboarding": ONBOARDING,
    "action_request": ACTION_REQUEST,
    "functional_question": FUNCTIONAL_QUESTION,
    "general_question": GENERAL_QUESTION,
    "paywall_soft_warning": PAYWALL_SOFT_WARNING,
    "small_talk": SMALL_TALK,
}