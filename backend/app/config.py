import os
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
    N8N_WEBHOOK_URL: str = os.getenv("N8N_WEBHOOK_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "hospital-doctors")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    ADMIN_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "super-secret-telegram-webhook-key-2026")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-key-for-hospital-app-2026")
    JWT_ALGORITHM: str = "HS256"

settings = Settings()
