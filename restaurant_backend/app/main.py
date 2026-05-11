#==================================#
#            MAIN APP              #
#==================================#

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import CORS_ALLOW_ORIGIN_REGEX, CORS_ALLOW_ORIGINS
from app.routes import auth, food, orders, delivery, admin_users, payment, profile


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Restaurant API",
    description="Backend API for managing food items, orders and authentication",
    version="1.0.0",
)

# Keep route matching strict and avoid implicit 307 slash redirects.
app.router.redirect_slashes = False


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(food.router)
app.include_router(orders.router)
app.include_router(delivery.router)
app.include_router(admin_users.router)
app.include_router(payment.router)
app.include_router(profile.router)


@app.get("/", tags=["Health"])
def health_check():
    """Check if the API is running."""
    return {"status": "ok", "message": "Restaurant API is running"}


@app.on_event("startup")
def verify_schema():
    from app.db.database import engine
    from sqlalchemy import inspect
    try:
        inspector = inspect(engine)
        users_table_exists = inspector.has_table("users")
        delivery_verifications_exists = inspector.has_table("delivery_verifications")

        if not users_table_exists:
            logger.error("SCHEMA MISMATCH DETECTED: Missing users table. Run migrations!")
            return

        columns = [col["name"] for col in inspector.get_columns("users")]
        required_cols = ["phone", "address", "first_name", "last_name", "is_email_verified", "is_profile_complete"]
        missing = [c for c in required_cols if c not in columns]
        if missing:
            logger.error(f"SCHEMA MISMATCH DETECTED: Missing columns in users table: {missing}. Run migrations!")

        if not delivery_verifications_exists:
            logger.error("SCHEMA MISMATCH DETECTED: Missing delivery_verifications table. Run migrations!")
            return

        delivery_columns = [col["name"] for col in inspector.get_columns("delivery_verifications")]
        if "otp_code" not in delivery_columns:
            logger.error("SCHEMA MISMATCH DETECTED: Missing otp_code in delivery_verifications table.")
            # Backward-compatible hotfix for environments where migration c4d5e6f7a8b9
            # has not yet been applied.
            try:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE delivery_verifications ADD COLUMN otp_code VARCHAR"))
                logger.warning("Auto-heal applied: added missing otp_code column to delivery_verifications.")
            except SQLAlchemyError as exc:
                logger.exception(
                    "Failed to auto-add otp_code column. Run migrations immediately. Error: %s",
                    exc,
                )
    except SQLAlchemyError as exc:
        logger.exception("Schema verification failed at startup. App will continue running. Error: %s", exc)

logger.info("Restaurant API started successfully")
