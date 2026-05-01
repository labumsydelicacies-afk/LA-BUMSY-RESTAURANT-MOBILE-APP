#==================================#
#            MAIN APP              #
#==================================#

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ALLOW_ORIGIN_REGEX, CORS_ALLOW_ORIGINS
from app.routes import auth, food, orders, delivery, admin_users


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


@app.get("/", tags=["Health"])
def health_check():
    """Check if the API is running."""
    return {"status": "ok", "message": "Restaurant API is running"}


logger.info("Restaurant API started successfully")