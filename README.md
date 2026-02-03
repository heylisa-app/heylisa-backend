# HeyLisa Backend

Backend Python (FastAPI) pour HeyLisa - Assistante IA exécutive.

## Setup local

```bash
# 1. Installer dépendances
pip install -r requirements.txt

# 2. Configurer environnement
cp .env.example .env

# 3. Lancer serveur dev
uvicorn app.main:app --reload
