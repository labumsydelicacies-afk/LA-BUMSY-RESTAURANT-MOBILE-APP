# LA BUMSY Restaurant App

This repository has two separate app folders:

- `restaurant_backend` for the FastAPI backend
- `restaurant_frontend` for the Vite/React frontend

The backend is the only Python project in this repo.

## Backend Setup

Run Python and Alembic commands from `restaurant_backend`:

```powershell
cd restaurant_backend
uv sync
uv run uvicorn app.main:app --reload
```

For migrations:

```powershell
cd restaurant_backend
uv run alembic -c app/db/migrations/alembic.ini upgrade head
```

## Frontend Setup

Run Node commands from `restaurant_frontend`:

```powershell
cd restaurant_frontend
npm install
npm run dev
```

## Why The Extra `.venv` Happened

There used to be a second Python project definition at the repo root. Running `uv` there created a different `.venv` from the backend one. The root Python manifests were removed so `restaurant_backend` is now the single source of truth.
