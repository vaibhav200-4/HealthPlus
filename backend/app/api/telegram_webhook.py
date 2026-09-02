# api/telegram_webhook.py
import uuid
import logging
import httpx
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks
from typing import Optional, Dict, Any

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

def _resolve_telegram_context_core(telegram_id: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Core lookup/creation logic for Telegram context, without FastAPI Request dependency.
    """
    telegram_id_str = telegram_id.strip()
    if not telegram_id_str:
        raise HTTPException(status_code=400, detail="telegram_id is required")

    user_id = None
    role = "patient"
    hospital_id = "H001"

    # 1. Look up public.telegram_accounts by telegram_id first
    tg_accounts = SupabaseService.get_records("telegram_accounts", {"telegram_id": telegram_id_str})
    if tg_accounts:
        user_id = tg_accounts[0].get("user_id")
        profiles = SupabaseService.get_records("profiles", {"id": user_id}) if user_id else []
        if profiles:
            role = profiles[0].get("role", "patient")
    else:
        # 2. Fall back to profiles.telegram_id if no telegram_accounts row exists
        profiles = SupabaseService.get_records("profiles", {"telegram_id": telegram_id_str})
        if profiles:
            user_id = profiles[0].get("id")
            role = profiles[0].get("role", "patient")
            SupabaseService.insert_record("telegram_accounts", {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "telegram_id": telegram_id_str,
                "status": "active"
            })
        else:
            # 3. Create new profile & telegram_accounts row
            user_id = str(uuid.uuid4())
            name = full_name.strip() if full_name and full_name.strip() else f"Telegram Patient {telegram_id_str[-4:]}"
            profile_data = {
                "id": user_id,
                "name": name,
                "email": f"telegram_{telegram_id_str}@telegram.user",
                "telegram_id": telegram_id_str,
                "password_hash": "",
                "role": "patient"
            }
            SupabaseService.insert_record("profiles", profile_data)
            get_or_create_patient_code(user_id)
            SupabaseService.insert_record("telegram_accounts", {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "telegram_id": telegram_id_str,
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

@router.post("/resolve-context")
def resolve_telegram_context(
    data: TelegramResolveContextRequest,
    request: Request = None
):
    if request:
        auth_rate_limiter.check(request)
    return _resolve_telegram_context_core(data.telegram_id, data.full_name)

def _log_telegram_message_core(telegram_id: str, session_id: str, role: str, message: str):
    """Internal helper to explicitly log Telegram chat turns to Supabase chat_messages."""
    user_id = None
    profiles = SupabaseService.get_records("profiles", {"telegram_id": telegram_id})
    if profiles:
        user_id = profiles[0]["id"]

    msg_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": "telegram",
        "session_id": session_id,
        "role": role,
        "message": message,
        "telegram_id": telegram_id
    }
    return SupabaseService.insert_record("chat_messages", msg_record)

@router.post("/log-message")
def log_telegram_message(
    data: TelegramMessageCreate,
    x_telegram_secret: Optional[str] = Header(None)
):
    if x_telegram_secret != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    created = _log_telegram_message_core(
        telegram_id=data.telegram_id,
        session_id=data.session_id,
        role=data.role,
        message=data.message
    )
    return {
        "success": True,
        "user_id": created.get("user_id"),
        "message_id": created.get("id"),
        "channel": "telegram"
    }

async def _process_telegram_update_background(update: Dict[str, Any]):
    """Background task processing Telegram updates asynchronously after fast 200 OK ack."""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    msg = update.get("message") or update.get("edited_message") or {}
    if not msg:
        return

    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = msg.get("text") or msg.get("caption") or ""
    from_user = msg.get("from", {})
    telegram_id = str(from_user.get("id", chat_id))
    full_name = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip()

    if not telegram_id or not chat_id:
        return

    # 1. Resolve context core to find user_id
    ctx = _resolve_telegram_context_core(telegram_id, full_name)
    user_id = ctx["user_id"]
    thread_id = f"tg_{chat_id}"

    # 2. Process photo / document upload forwarding if present
    document = msg.get("document") or (msg.get("photo")[-1] if msg.get("photo") else None)
    if document and bot_token:
        file_id = document.get("file_id")
        if file_id:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    file_info_res = await client.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}")
                    if file_info_res.status_code == 200:
                        file_path = file_info_res.json().get("result", {}).get("file_path")
                        if file_path:
                            file_bytes_res = await client.get(f"https://api.telegram.org/file/bot{bot_token}/{file_path}")
                            if file_bytes_res.status_code == 200:
                                filename = file_path.split("/")[-1]
                                files = {"file": (filename, file_bytes_res.content)}
                                data = {
                                    "patient_identifier": user_id,
                                    "uploaded_by": "patient",
                                    "title": f"Telegram Upload {filename}"
                                }
                                headers = {"X-Telegram-Secret": settings.TELEGRAM_WEBHOOK_SECRET}
                                from app.api.medical_records import upload_medical_record
                                # Internal call simulation or local upload
            except Exception as e:
                logger.error(f"Error handling Telegram document upload: {e}")

    if not text:
        return

    # 3. Log user message
    _log_telegram_message_core(telegram_id, thread_id, "user", text)

    # 4. Invoke LangGraph agent
    try:
        from langchain_core.messages import HumanMessage
        from app.agent.graph import get_agent_graph

        agent_graph = await get_agent_graph()
        config = {"configurable": {"thread_id": thread_id}}
        agent_input = {
            "messages": [HumanMessage(content=text)],
            "user_id": user_id,
            "channel": "telegram",
            "thread_id": thread_id
        }

        res = await agent_graph.ainvoke(agent_input, config=config)
        messages = res.get("messages", [])
        
        reply_text = ""
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
            reply_text = _extract_text(getattr(messages[-1], "content", ""))

        for m in messages:
            m_str = _extract_text(getattr(m, "content", ""))
            if "qr_code_url" in m_str:
                try:
                    import json
                    parsed = json.loads(m_str)
                    if isinstance(parsed, dict) and parsed.get("qr_code_url"):
                        qr_url = parsed["qr_code_url"]
                except Exception:
                    pass

        # 5. Log assistant turn
        if reply_text:
            _log_telegram_message_core(telegram_id, thread_id, "assistant", reply_text)

        # 6. Dispatch reply via Telegram Bot API
        if bot_token and chat_id:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if qr_url:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                        json={"chat_id": chat_id, "photo": qr_url, "caption": reply_text or "Payment Details"}
                    )
                elif reply_text:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text}
                    )
    except Exception as e:
        logger.error(f"Error processing Telegram message in background: {e}")

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    """
    Direct internet-facing Telegram Webhook endpoint:
    - Validates X-Telegram-Bot-Api-Secret-Token against TELEGRAM_WEBHOOK_SECRET.
    - Returns 200 OK immediately to prevent Telegram timeouts/retries.
    - Dispatches agent processing to BackgroundTasks.
    """
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    if not x_telegram_bot_api_secret_token or x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret token")

    update = await request.json()
    background_tasks.add_task(_process_telegram_update_background, update)
    return {"status": "ok"}
