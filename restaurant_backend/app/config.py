#===========================#
#    CONFIGURATION FILE     #
#===========================#



import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None

# Load environment variables from the backend .env file when python-dotenv is installed.
if load_dotenv is not None:
    ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=ENV_PATH)

def _clean_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


DATABASE_URL = _clean_env("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy expects postgresql://, while some platforms expose postgres://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
SECRET_KEY = _clean_env("SECRET_KEY")
ALGORITHM = _clean_env("ALGORITHM", "HS256")
SMTP_EMAIL = _clean_env("SMTP_EMAIL")
SMTP_PASSWORD = _clean_env("SMTP_PASSWORD")
SMTP_HOST = _clean_env("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_clean_env("SMTP_PORT", "465") or "465")
GOOGLE_APPS_SCRIPT_URL = _clean_env("GOOGLE_APPS_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbxL-cvzoUaj5D0gYBZV6tuoXTh_kLykWIksb7Qjvz1-VkHKzDxdF_YH5m6XWcQN1TnV/exec")

# Flutterwave payment credentials
FLUTTERWAVE_SECRET_KEY = _clean_env("FLUTTERWAVE_SECRET_KEY", "") or ""
FLUTTERWAVE_PUBLIC_KEY = _clean_env("FLUTTERWAVE_PUBLIC_KEY", "") or ""
FLUTTERWAVE_SECRET_HASH = _clean_env("FLUTTERWAVE_SECRET_HASH", "") or ""
FLUTTERWAVE_BASE_URL = _clean_env("FLUTTERWAVE_BASE_URL", "https://api.flutterwave.com/v3") or "https://api.flutterwave.com/v3"

# Frontend base URL — used to build the payment redirect/callback URL
FRONTEND_URL = _clean_env("FRONTEND_URL", "http://localhost:5173") or "http://localhost:5173"

raw_origins = _clean_env("CORS_ALLOW_ORIGINS", "") or ""
if raw_origins.strip():
    CORS_ALLOW_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
else:
    CORS_ALLOW_ORIGINS = ["http://localhost:3000"]

# Optional regex for dynamic preview domains (e.g. Vercel previews).
CORS_ALLOW_ORIGIN_REGEX = _clean_env("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app") or r"https://.*\.vercel\.app"
