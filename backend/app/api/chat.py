# backend/app/api/chat.py
import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional

from app.schemas.chat_schema import ChatMessageCreate, ChatMessageResponse, ChatSendResponse
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import get_current_user
from app.config import settings

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

    # 2. Invoke LangGraph agent directly
    from langchain_core.messages import HumanMessage
    from app.agent.graph import get_agent_graph

    agent_graph = await get_agent_graph()
    config = {"configurable": {"thread_id": session_id}}

    agent_input = {
        "messages": [HumanMessage(content=data.message)],
        "user_id": user_id,
        "channel": "web",
        "thread_id": session_id
    }

    res = await agent_graph.ainvoke(agent_input, config=config)
    messages = res.get("messages", [])
    ai_response_text = ""
    qr_url = None

    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, str):
                    parts.append(p)
                elif isinstance(p, dict) and p.get("type") == "text":
                    parts.append(p.get("text", ""))
            return "\n".join(parts)
        return str(content) if content is not None else ""

    if messages:
        last_msg = messages[-1]
        ai_response_text = _extract_text(getattr(last_msg, "content", ""))

    # Inspect tool messages for payment QR URL if generated
    for msg in messages:
        msg_content_str = _extract_text(getattr(msg, "content", ""))
        if "qr_code_url" in msg_content_str:
            try:
                import json
                parsed = json.loads(msg_content_str)
                if isinstance(parsed, dict) and parsed.get("qr_code_url"):
                    qr_url = parsed["qr_code_url"]
            except Exception:
                pass

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
        existing_ids = {m["id"] for m in web_messages}
        for tm in tg_by_id:
            if tm["id"] not in existing_ids:
                telegram_messages.append(tm)

    all_messages = web_messages + telegram_messages

    if session_id:
        all_messages = [m for m in all_messages if m.get("session_id") == session_id]

    all_messages.sort(key=lambda x: str(x.get("created_at", "")))
    return all_messages
