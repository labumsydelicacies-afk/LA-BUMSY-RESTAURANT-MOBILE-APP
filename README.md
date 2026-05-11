# LA BUMSY RESTAURANT MOBILE APP

Full-stack restaurant ordering platform with a FastAPI backend and a React + Vite frontend.

## Project Structure

- `restaurant_backend` - FastAPI API, business logic, database models, Alembic migrations, and tests.
- `restaurant_frontend` - React client built with Vite and Tailwind.

## Tech Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL (recommended)

### Frontend
- React
- Vite
- Tailwind CSS

## Local Setup

## 1) Backend

1. Open a terminal in `restaurant_backend`.
2. Create and activate a virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Create/update `.env` from your environment template and set required values (database URL, auth secrets, etc.).
5. Run migrations.
6. Start the API:
   - `uvicorn app.main:app --reload`

## 2) Frontend

1. Open a terminal in `restaurant_frontend`.
2. Install dependencies:
   - `npm install`
3. Configure frontend environment values (`.env.development` / `.env.production`) as needed.
4. Start development server:
   - `npm run dev`

## Testing

From `restaurant_backend`:

- Run all tests:
  - `pytest`
- Run unit tests:
  - `pytest app/tests/unit`
- Run integration tests:
  - `pytest app/tests/integration`

## Notes

- Keep secrets out of version control (`.env` files should remain local).
- Run backend and frontend together for full end-to-end flow.
