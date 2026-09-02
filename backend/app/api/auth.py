import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from app.schemas.user_schema import UserRegister, UserLogin, AuthResponse, UserProfile, LinkTelegramRequest, PatientProfileUpdate
from app.auth.auth_handler import (
    hash_password, verify_password, create_access_token, get_current_user,
    auth_rate_limiter, create_voice_service_token, verify_voice_service_token,
    verify_voice_bootstrap_secret, find_or_create_caller_by_phone, normalize_phone_e164
)
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

def build_user_profile_response(user_data: dict) -> UserProfile:
    role = user_data.get("role", "user")
    patient_code = None
    dob = None
    gender = None
    blood_group = None
    address = None
    emergency_contact = None

    if role in ["user", "patient"]:
        pts = SupabaseService.get_records("patients", {"profile_id": user_data["id"]})
        if pts:
            p_rec = pts[0]
            patient_code = p_rec.get("patient_code")
            dob = p_rec.get("date_of_birth")
            gender = p_rec.get("gender")
            blood_group = p_rec.get("blood_group")
            address = p_rec.get("address")
            emergency_contact = p_rec.get("emergency_contact")
        else:
            patient_code = get_or_create_patient_code(user_data["id"])

    return UserProfile(
        id=user_data["id"],
        name=user_data.get("name", ""),
        email=user_data.get("email", ""),
        phone=user_data.get("phone"),
        telegram_id=user_data.get("telegram_id"),
        role=role,
        patient_code=patient_code,
        date_of_birth=str(dob) if dob else None,
        gender=gender,
        blood_group=blood_group,
        address=address,
        emergency_contact=emergency_contact,
        created_at=str(user_data.get("created_at")) if user_data.get("created_at") else None
    )

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
    token = create_access_token(user_id=user_id, email=data.email, role="user")
    user_obj = build_user_profile_response(created_profile or profile_data)

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
    token = create_access_token(
        user_id=user_profile["id"],
        email=user_profile["email"],
        role=role
    )

    return AuthResponse(
        access_token=token,
        user=build_user_profile_response(user_profile)
    )

@router.get("/me", response_model=UserProfile)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return build_user_profile_response(current_user)

@router.post("/voice-token")
def issue_voice_token(current_user: dict = Depends(get_current_user)):
    """
    Issues a short-lived Voice Service Token (X-Voice-Token) for the authenticated browser user.
    Integrates existing HealthPulse JWT authentication to establish verified user identity.
    """
    user_id = current_user["id"]
    role = current_user.get("role", "patient")
    token = create_voice_service_token(user_id=user_id, role=role)
    return {
        "voice_token": token,
        "user_id": user_id,
        "expires_in": 900
    }

@router.post("/voice-token-by-phone")
def issue_voice_token_by_phone(
    payload: dict,
    service_auth: bool = Depends(verify_voice_bootstrap_secret)
):
    """
    Issues a short-lived Voice Service Token (X-Voice-Token) for a PSTN caller identified by phone.
    Service-authenticated via X-Voice-Token service header.
    Resolves or auto-creates the caller profile using Option (b) placeholder email format (f"{phone}@voice.local").
    """
    raw_phone = payload.get("phone")
    if not raw_phone:
        raise HTTPException(status_code=400, detail="Missing required 'phone' parameter")

    profile = find_or_create_caller_by_phone(raw_phone)
    user_id = profile["id"]
    role = profile.get("role", "patient")
    token = create_voice_service_token(user_id=user_id, role=role)
    return {
        "voice_token": token,
        "user_id": user_id,
        "phone": profile.get("phone"),
        "expires_in": 900
    }

@router.put("/patient-profile", response_model=UserProfile)
def update_patient_profile(data: PatientProfileUpdate, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    # 1. Update phone in profiles table if provided
    if data.phone is not None:
        SupabaseService.update_record("profiles", user_id, {"phone": data.phone})
        current_user["phone"] = data.phone

    # 2. Get or create patient record for user_id
    pts = SupabaseService.get_records("patients", {"profile_id": user_id})
    patient_updates = {}
    if data.gender is not None:
        patient_updates["gender"] = data.gender
    if data.blood_group is not None:
        patient_updates["blood_group"] = data.blood_group
    if data.date_of_birth is not None:
        patient_updates["date_of_birth"] = data.date_of_birth
    if data.address is not None:
        patient_updates["address"] = data.address
    if data.emergency_contact is not None:
        patient_updates["emergency_contact"] = data.emergency_contact

    if pts:
        patient_id = pts[0]["id"]
        if patient_updates:
            SupabaseService.update_record("patients", patient_id, patient_updates)
    else:
        all_pts = SupabaseService.get_records("patients")
        p_code = f"PT-{len(all_pts) + 1:06d}"
        new_patient = {
            "id": str(uuid.uuid4()),
            "profile_id": user_id,
            "patient_code": p_code,
            **patient_updates
        }
        SupabaseService.insert_record("patients", new_patient)

    updated_profile = SupabaseService.get_record_by_id("profiles", user_id) or current_user
    return build_user_profile_response(updated_profile)

@router.post("/link-telegram", response_model=UserProfile)
def link_telegram(data: LinkTelegramRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    updated = SupabaseService.update_record("profiles", user_id, {"telegram_id": data.telegram_id})

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

    profile_data = SupabaseService.get_record_by_id("profiles", user_id) or current_user
    return build_user_profile_response(profile_data)

