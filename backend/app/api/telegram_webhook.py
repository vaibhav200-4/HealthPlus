import uuid
import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from app.schemas.chat_schema import TelegramMessageCreate
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import create_n8n_context_token, auth_rate_limiter
from app.api.auth import get_or_create_patient_code
from app.config import settings

logger = logging.getLogger("hospital_app.telegram")

router = APIRouter(prefix="/api/telegram", tags=["Telegram Synchronization"])

class TelegramResolveContextRequest(BaseModel):
    telegram_id: str
    full_name: Optional[str] = None

@router.post("/resolve-context")
def resolve_telegram_context(
    data: TelegramResolveContextRequest,
    request: Request = None
):
    """
    Telegram context-resolution endpoint:
    - Look up public.telegram_accounts by telegram_id first; fall back to profiles.telegram_id.
    - If neither exists, create both a profiles row (role='patient') and a matching telegram_accounts row.
    - Generate an n8n_token using existing create_n8n_context_token.
    - Rate limited per IP/client.
    """
    if request:
        auth_rate_limiter.check(request)

    telegram_id = data.telegram_id.strip()
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id is required")

    user_id = None
    role = "patient"
    hospital_id = "H001"

    # 1. Look up public.telegram_accounts by telegram_id first
    tg_accounts = SupabaseService.get_records("telegram_accounts", {"telegram_id": telegram_id})
    if tg_accounts:
        user_id = tg_accounts[0].get("user_id")
        profiles = SupabaseService.get_records("profiles", {"id": user_id}) if user_id else []
        if profiles:
            role = profiles[0].get("role", "patient")
    else:
        # 2. Fall back to profiles.telegram_id if no telegram_accounts row exists
        profiles = SupabaseService.get_records("profiles", {"telegram_id": telegram_id})
        if profiles:
            user_id = profiles[0].get("id")
            role = profiles[0].get("role", "patient")
            # Sync missing telegram_accounts row
            SupabaseService.insert_record("telegram_accounts", {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "telegram_id": telegram_id,
                "status": "active"
            })
        else:
            # 3. Neither exists: create both profiles row and telegram_accounts row
            user_id = str(uuid.uuid4())
            name = data.full_name.strip() if data.full_name and data.full_name.strip() else f"Telegram Patient {telegram_id[-4:]}"
            profile_data = {
                "id": user_id,
                "name": name,
                "email": f"telegram_{telegram_id}@telegram.user",
                "telegram_id": telegram_id,
                "password_hash": "",
                "role": "patient"
            }
            SupabaseService.insert_record("profiles", profile_data)
            get_or_create_patient_code(user_id)
            SupabaseService.insert_record("telegram_accounts", {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "telegram_id": telegram_id,
                "status": "active"
            })

    # Resolve primary hospital_id
    members = SupabaseService.get_records("hospital_members", {"user_id": user_id})
    if members:
        hospital_id = members[0].get("hospital_id", "H001")
    else:
        docs = SupabaseService.get_records("doctors", {"profile_id": user_id})
        if docs:
            hospital_id = docs[0].get("hospital_id", "H001")
        else:
            pts = SupabaseService.get_records("patients", {"profile_id": user_id})
            if pts and pts[0].get("hospital_id"):
                hospital_id = pts[0].get("hospital_id")

    n8n_token = create_n8n_context_token(
        user_id=user_id,
        role=role,
        hospital_id=hospital_id
    )

    return {
        "user_id": user_id,
        "n8n_token": n8n_token,
        "hospital_id": hospital_id
    }

@router.post("/log-message")
def log_telegram_message(
    data: TelegramMessageCreate,
    x_telegram_secret: Optional[str] = Header(None)
):
    """
    Endpoint called by n8n workflow or Telegram bot to explicitly log Telegram messages to Supabase.
    Maps telegram_id to application user_id if linked in profiles table.
    """
    if x_telegram_secret != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    telegram_id = data.telegram_id
    user_id = None

    # Check if a profile exists for this telegram_id
    profiles = SupabaseService.get_records("profiles", {"telegram_id": telegram_id})
    if profiles:
        user_id = profiles[0]["id"]
        logger.info(f"Telegram message mapped to linked application user_id {user_id}")
    else:
        logger.info(f"Telegram message received for unlinked telegram_id {telegram_id}")

    msg_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": "telegram",
        "session_id": data.session_id,
        "role": data.role,
        "message": data.message,
        "telegram_id": telegram_id
    }

    created = SupabaseService.insert_record("chat_messages", msg_record)
    return {
        "success": True,
        "user_id": user_id,
        "message_id": created.get("id"),
        "channel": "telegram"
    }

