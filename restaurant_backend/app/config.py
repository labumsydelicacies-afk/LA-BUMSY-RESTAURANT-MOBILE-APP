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

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
if raw_origins.strip():
    CORS_ALLOW_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
else:
    CORS_ALLOW_ORIGINS = ["http://localhost:3000"]

# Optional regex for dynamic preview domains (e.g. Vercel previews).
CORS_ALLOW_ORIGIN_REGEX = os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app")
