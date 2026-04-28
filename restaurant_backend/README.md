# Restaurant Backend

FastAPI backend for the restaurant app, prepared for Railway deployment.

## Local Run

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Set environment variables in `.env`:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALGORITHM` (optional, defaults to `HS256`)
   - `CORS_ALLOW_ORIGINS` (optional, comma-separated origins)
4. Start server:
   - `uvicorn app.main:app --reload`

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
