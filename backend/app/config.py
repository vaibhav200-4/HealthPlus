import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current file's parent or root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
env_path = ROOT_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "hospital-doctors")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    ADMIN_USER_ID: str = os.getenv("ADMIN_USER_ID", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "super-secret-telegram-webhook-key-2026")
    N8N_JWT_SECRET: str = os.getenv("N8N_JWT_SECRET", "super-secret-n8n-tool-context-key-2026")
    VOICE_SERVICE_SECRET: str = os.getenv("VOICE_SERVICE_SECRET", "super-secret-voice-service-key-2026")
    ENABLE_TELEGRAM_HMAC_VERIFICATION: bool = os.getenv("ENABLE_TELEGRAM_HMAC_VERIFICATION", "false").lower() == "true"
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-key-for-hospital-app-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ALLOW_DEMO_SEED: bool = os.getenv("ALLOW_DEMO_SEED", "false").lower() == "true"
    ALLOWED_ORIGINS: list = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",") if o.strip()
    ]
    ALLOWED_ORIGIN_REGEX: str = os.getenv("ALLOWED_ORIGIN_REGEX", r"https://.*\.vercel\.app")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    # LangGraph Agent Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nvidia")  # "nvidia" | "gemini"
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    USE_PINECONE_RAG: bool = os.getenv("USE_PINECONE_RAG", "false").lower() == "true"
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

settings = Settings()

logger = logging.getLogger("hospital_app.config")
if not settings.RESEND_API_KEY:
    logger.warning("RESEND_API_KEY environment variable is not set. Resend email notifications will be skipped.")

