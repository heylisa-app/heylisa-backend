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


