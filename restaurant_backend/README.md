# Restaurant Backend

FastAPI backend for the restaurant app, prepared for Railway deployment.

## Local Run

Run all backend Python commands from the `restaurant_backend` folder.

1. Install dependencies:
   - `uv sync`
2. Set environment variables in `.env`:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALGORITHM` (optional, defaults to `HS256`)
   - `CORS_ALLOW_ORIGINS` (optional, comma-separated origins)
3. Start server:
   - `uv run uvicorn app.main:app --reload`
4. Run migrations:
   - `uv run alembic -c app/db/migrations/alembic.ini upgrade head`

`uv` will manage the backend virtual environment in `restaurant_backend/.venv`. Do not run `uv sync` from the repository root.

## Railway Deployment

This project includes:
- `Procfile` for Railway process startup
- `railway.toml` with start command and healthcheck

### Required Railway Variables

- `DATABASE_URL` (Railway Postgres connection string)
- `SECRET_KEY` (strong random secret)
- `ALGORITHM` (recommended: `HS256`)
- `CORS_ALLOW_ORIGINS` (frontend URL, or comma-separated list)

### Deploy Notes

- Railway provides `PORT`; app is configured to bind `0.0.0.0:$PORT`.
- Healthcheck path is `/`.
- If you use Alembic migrations, run migration command during deploy/release workflow.
