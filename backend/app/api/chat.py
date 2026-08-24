# backend/app/chat.py
import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from app.schemas.chat_schema import ChatMessageCreate, ChatMessageResponse, ChatSendResponse
from app.services.n8n_service import N8nService
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/send", response_model=ChatSendResponse)
async def send_web_chat_message(
    data: ChatMessageCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    session_id = data.session_id or f"session_{user_id[:8]}"

    # 1. Explicitly save user message to chat_messages table in Supabase
    user_msg_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": "web",
        "session_id": session_id,
        "role": "user",
        "message": data.message,
        "telegram_id": current_user.get("telegram_id")
    }
    SupabaseService.insert_record("chat_messages", user_msg_record)

    # 2. Forward to n8n webhook
    ai_res = await N8nService.send_web_chat(
        user_id=user_id,
        message=data.message,
        session_id=session_id
    )
    ai_response_text = ai_res.get("text", "")
    qr_url = ai_res.get("qr_url")

    # 3. Explicitly save assistant response to chat_messages table in Supabase
    assistant_msg_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": "web",
        "session_id": session_id,
        "role": "assistant",
        "message": ai_response_text,
        "telegram_id": current_user.get("telegram_id")
    }
    SupabaseService.insert_record("chat_messages", assistant_msg_record)

    return ChatSendResponse(
        message=ai_response_text,
        session_id=session_id,
        user_id=user_id,
        qr_url=qr_url
    )

@router.get("/history", response_model=List[ChatMessageResponse])
def get_chat_history(
    current_user: dict = Depends(get_current_user),
    session_id: Optional[str] = None
):
    user_id = current_user["id"]
    telegram_id = current_user.get("telegram_id")

    # Fetch all user messages (both web and telegram if telegram_id is linked)
    web_messages = SupabaseService.get_records("chat_messages", {"user_id": user_id})
    
    telegram_messages = []
    if telegram_id:
        tg_by_id = SupabaseService.get_records("chat_messages", {"telegram_id": telegram_id})
        # Filter out duplicates
        existing_ids = {m["id"] for m in web_messages}
        for tm in tg_by_id:
            if tm["id"] not in existing_ids:
                telegram_messages.append(tm)

    all_messages = web_messages + telegram_messages

    if session_id:
        all_messages = [m for m in all_messages if m.get("session_id") == session_id]

    # Sort chronologically
    all_messages.sort(key=lambda x: str(x.get("created_at", "")))
    return all_messages
