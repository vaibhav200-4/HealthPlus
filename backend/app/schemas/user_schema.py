from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    telegram_id: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    role: str = "user"
    created_at: Optional[str] = None

class LinkTelegramRequest(BaseModel):
    telegram_id: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
