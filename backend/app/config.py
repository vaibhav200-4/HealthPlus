import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Search for .env specifically in backend directory first, falling back to ROOT_DIR
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

backend_env_path = BACKEND_DIR / ".env"
root_env_path = ROOT_DIR / ".env"

if backend_env_path.exists():
    load_dotenv(dotenv_path=backend_env_path)
elif root_env_path.exists():
    load_dotenv(dotenv_path=root_env_path)
else:
    load_dotenv()

def require_env_var(key: str, default: str | None = None) -> str:
    val = os.getenv(key, default)
    if val is None or val.strip() == "":
        raise RuntimeError(f"[Config Error] Missing required environment variable: {key}")
    return val.strip()

class Settings:
    # Server & Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    ALLOW_DEMO_SEED: bool = os.getenv("ALLOW_DEMO_SEED", "false").lower() == "true"
    ALLOWED_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",") if o.strip()
    ]
    ALLOWED_ORIGIN_REGEX: str = os.getenv("ALLOWED_ORIGIN_REGEX", r"https://.*\.vercel\.app")

    # Supabase Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")

    # Security & Secrets
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-key-for-hospital-app-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    N8N_JWT_SECRET: str = os.getenv("N8N_JWT_SECRET", "super-secret-n8n-tool-context-key-2026")
    VOICE_SERVICE_SECRET: str = os.getenv("VOICE_SERVICE_SECRET", "super-secret-voice-service-key-2026")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "super-secret-telegram-webhook-key-2026")
    ENABLE_TELEGRAM_HMAC_VERIFICATION: bool = os.getenv("ENABLE_TELEGRAM_HMAC_VERIFICATION", "false").lower() == "true"

    # LLM Providers & AI Keys
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nvidia")  # "nvidia" | "gemini"
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_NIM_MODEL: str = os.getenv("NVIDIA_NIM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    CARTESIA_API_KEY: str = os.getenv("CARTESIA_API_KEY", "")

    # Vector Database (Pinecone)
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "hospital-doctors")
    USE_PINECONE_RAG: bool = os.getenv("USE_PINECONE_RAG", "false").lower() == "true"

    # External Integrations
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
    NGROCK_API_KEY: str = os.getenv("NGROCK_API_KEY", "")

    # App Identities
    ADMIN_USER_ID: str = os.getenv("ADMIN_USER_ID", "00000000-0000-0000-0000-000000000001")
    AGENT_USER_ID: str = os.getenv("AGENT_USER_ID", "0042bb23-509d-42e7-b05c-2a519f354c4b")

settings = Settings()

logger = logging.getLogger("hospital_app.config")
if not settings.RESEND_API_KEY:
    logger.warning("RESEND_API_KEY environment variable is not set. Resend email notifications will be skipped.")
