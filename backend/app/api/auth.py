import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from app.schemas.user_schema import UserRegister, UserLogin, AuthResponse, UserProfile, LinkTelegramRequest
from app.auth.auth_handler import hash_password, verify_password, create_access_token, get_current_user, auth_rate_limiter
from app.database.supabase_client import SupabaseService, get_supabase_client
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

def get_or_create_patient_code(user_id: str) -> Optional[str]:
    pts = SupabaseService.get_records("patients", {"profile_id": user_id})
    if pts:
        return pts[0].get("patient_code")
    
    # Generate new patient code e.g. PT-000001
    all_pts = SupabaseService.get_records("patients")
    count = len(all_pts) + 1
    p_code = f"PT-{count:06d}"
    patient_rec = {
        "id": str(uuid.uuid4()),
        "profile_id": user_id,
        "patient_code": p_code
    }
    SupabaseService.insert_record("patients", patient_rec)
    return p_code

@router.post("/register", response_model=AuthResponse)
def register_user(data: UserRegister, request: Request = None):
    auth_rate_limiter.check(request)

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
    patient_code = get_or_create_patient_code(user_id)
    token = create_access_token(user_id=user_id, email=data.email, role="user")

    user_obj = UserProfile(
        id=user_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        telegram_id=data.telegram_id,
        role="user",
        patient_code=patient_code
    )

    return AuthResponse(access_token=token, user=user_obj)

@router.post("/login", response_model=AuthResponse)
def login_user(data: UserLogin, request: Request = None):
    auth_rate_limiter.check(request)

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

    role = user_profile.get("role", "user")
    patient_code = get_or_create_patient_code(user_profile["id"]) if role in ["user", "patient"] else None
    token = create_access_token(
        user_id=user_profile["id"],
        email=user_profile["email"],
        role=role
    )

    return AuthResponse(
        access_token=token,
        user=UserProfile(
            id=user_profile["id"],
            name=user_profile.get("name", data.email.split("@")[0]),
            email=user_profile["email"],
            phone=user_profile.get("phone"),
            telegram_id=user_profile.get("telegram_id"),
            role=role,
            patient_code=patient_code
        )
    )

@router.get("/me", response_model=UserProfile)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role", "user")
    patient_code = get_or_create_patient_code(current_user["id"]) if role in ["user", "patient"] else None
    return UserProfile(
        id=current_user["id"],
        name=current_user.get("name", ""),
        email=current_user.get("email", ""),
        phone=current_user.get("phone"),
        telegram_id=current_user.get("telegram_id"),
        role=role,
        patient_code=patient_code
    )

@router.post("/link-telegram", response_model=UserProfile)
def link_telegram(data: LinkTelegramRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    updated = SupabaseService.update_record("profiles", user_id, {"telegram_id": data.telegram_id})

    # Also populate dedicated telegram_accounts table
    existing_accs = SupabaseService.get_records("telegram_accounts", {"telegram_id": data.telegram_id})
    if existing_accs:
        SupabaseService.update_record("telegram_accounts", existing_accs[0]["id"], {"user_id": user_id, "status": "active"})
    else:
        SupabaseService.insert_record("telegram_accounts", {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "telegram_id": data.telegram_id,
            "status": "active"
        })

    role = current_user.get("role", "user")
    patient_code = get_or_create_patient_code(user_id) if role in ["user", "patient"] else None
    if not updated:
        current_user["telegram_id"] = data.telegram_id
        current_user["patient_code"] = patient_code
        return UserProfile(**current_user)
    updated["patient_code"] = patient_code
    return UserProfile(**updated)
