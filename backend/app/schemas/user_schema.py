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
    patient_code: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: Optional[str] = None

class PatientProfileUpdate(BaseModel):
    phone: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class LinkTelegramRequest(BaseModel):
    telegram_id: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
