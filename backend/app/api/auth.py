# backend/app/auth.py
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.user_schema import UserRegister, UserLogin, AuthResponse, UserProfile, LinkTelegramRequest
from app.auth.auth_handler import hash_password, verify_password, create_access_token, get_current_user
from app.database.supabase_client import SupabaseService, get_supabase_client

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=AuthResponse)
def register_user(data: UserRegister):
    # Check if user email already exists
    existing = SupabaseService.get_records("profiles", {"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(data.password)

    profile_data = {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "phone": data.phone or "",
        "telegram_id": data.telegram_id,
        "password_hash": hashed_pwd,
        "role": "user"
    }

    created_profile = SupabaseService.insert_record("profiles", profile_data)
    token = create_access_token(user_id=user_id, email=data.email, role="user")

    user_obj = UserProfile(
        id=user_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        telegram_id=data.telegram_id,
        role="user"
    )

    return AuthResponse(access_token=token, user=user_obj)

@router.post("/login", response_model=AuthResponse)
def login_user(data: UserLogin):
    # Admin master login check
    if data.email == "admin@hospital.com" and data.password == "admin123":
        user_id = settings.ADMIN_USER_ID
        admin_profiles = SupabaseService.get_records("profiles", {"email": "admin@hospital.com"})
        if not admin_profiles:
            SupabaseService.insert_record("profiles", {
                "id": user_id,
                "name": "System Administrator",
                "email": "admin@hospital.com",
                "password_hash": hash_password("admin123"),
                "role": "admin"
            })
        else:
            user_id = admin_profiles[0]["id"]

        token = create_access_token(user_id=user_id, email="admin@hospital.com", role="admin")
        return AuthResponse(
            access_token=token,
            user=UserProfile(id=user_id, name="System Administrator", email="admin@hospital.com", role="admin")
        )

    profiles = SupabaseService.get_records("profiles", {"email": data.email})
    if not profiles:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_profile = profiles[0]
    stored_hash = user_profile.get("password_hash")

    if not stored_hash or not verify_password(data.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(
        user_id=user_profile["id"],
        email=user_profile["email"],
        role=user_profile.get("role", "user")
    )

    return AuthResponse(
        access_token=token,
        user=UserProfile(
            id=user_profile["id"],
            name=user_profile.get("name", data.email.split("@")[0]),
            email=user_profile["email"],
            phone=user_profile.get("phone"),
            telegram_id=user_profile.get("telegram_id"),
            role=user_profile.get("role", "user")
        )
    )

@router.get("/me", response_model=UserProfile)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return UserProfile(
        id=current_user["id"],
        name=current_user.get("name", ""),
        email=current_user.get("email", ""),
        phone=current_user.get("phone"),
        telegram_id=current_user.get("telegram_id"),
        role=current_user.get("role", "user")
    )

@router.post("/link-telegram", response_model=UserProfile)
def link_telegram(data: LinkTelegramRequest, current_user: dict = Depends(get_current_user)):
    updated = SupabaseService.update_record("profiles", current_user["id"], {"telegram_id": data.telegram_id})
    if not updated:
        current_user["telegram_id"] = data.telegram_id
        return UserProfile(**current_user)
    return UserProfile(**updated)
