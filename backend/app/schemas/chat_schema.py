from pydantic import BaseModel
from typing import Optional, List

class ChatMessageCreate(BaseModel):
    message: str
    session_id: str
    channel: str = "web" # web or telegram

class TelegramMessageCreate(BaseModel):
    telegram_id: str
    message: str
    role: str = "user" # user or assistant
    session_id: str

class ChatMessageResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    channel: str
    session_id: str
    role: str
    message: str
    telegram_id: Optional[str] = None
    created_at: Optional[str] = None

class ChatSendResponse(BaseModel):
    message: str
    session_id: str
    user_id: str
    qr_url: Optional[str] = None

