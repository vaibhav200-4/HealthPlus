import uuid
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.schemas.chat_schema import TelegramMessageCreate
from app.database.supabase_client import SupabaseService
from app.config import settings

logger = logging.getLogger("hospital_app.telegram")

router = APIRouter(prefix="/api/telegram", tags=["Telegram Synchronization"])

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
