import time
import jwt
from typing import Dict, Any, Optional
from fastapi import HTTPException, Security, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from app.config import settings
from app.database.supabase_client import SupabaseService, get_supabase_client

from collections import defaultdict
from fastapi import Request

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class SimpleRateLimiter:
    """
    Lightweight in-memory rate limiter for auth endpoints.
    Enforces N requests per minute per IP.
    """
    def __init__(self, requests_per_minute: int = 5):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def check(self, request: Optional[Request] = None):
        if request is None:
            return
        client_ip = request.client.host if request and request.client else "127.0.0.1"
        now = time.time()
        window_start = now - 60.0
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication attempts. Please try again in 1 minute."
            )
        self.requests[client_ip].append(now)

auth_rate_limiter = SimpleRateLimiter(requests_per_minute=5)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, email: str, role: str, hospital_id: Optional[str] = None) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "hospital_id": hospital_id,
        "exp": time.time() + 86400 * 7 # 7 days validity
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("exp") and payload["exp"] < time.time():
            return None
        return payload
    except Exception:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    user_id = payload.get("user_id")
    profile = SupabaseService.get_record_by_id("profiles", user_id)
    if not profile:
        # Fallback to payload data if profile not created yet
        profile = {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "name": payload.get("email", "").split("@")[0]
        }
    return profile

def get_identity_context(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Resolves comprehensive identity context for authenticated request:
    user_id, email, role, is_super_admin, hospital_id, and hospital_memberships.
    """
    user_id = current_user["id"]
    role = current_user.get("role", "user")
    is_super_admin = (role == "super_admin") or (role == "admin" and user_id == settings.ADMIN_USER_ID)

    # 1. Resolve hospital_memberships
    memberships = []
    try:
        memberships = SupabaseService.get_records("hospital_members", {"user_id": user_id})
    except Exception:
        pass

    # 2. Resolve primary hospital_id
    hospital_id = None
    if memberships:
        hospital_id = memberships[0].get("hospital_id")
    elif role == "doctor":
        try:
            docs = SupabaseService.get_records("doctors", {"profile_id": user_id})
            if docs:
                hospital_id = docs[0].get("hospital_id")
        except Exception:
            pass
    elif role in ["user", "patient"]:
        try:
            pts = SupabaseService.get_records("patients", {"profile_id": user_id})
            if pts:
                hospital_id = pts[0].get("hospital_id")
        except Exception:
            pass

    return {
        "user": current_user,
        "user_id": user_id,
        "email": current_user.get("email"),
        "role": role,
        "is_super_admin": is_super_admin,
        "hospital_id": hospital_id,
        "hospital_memberships": memberships
    }

def require_super_admin(identity: Dict[str, Any] = Depends(get_identity_context)) -> Dict[str, Any]:
    if not identity["is_super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return identity

def require_hospital_admin(identity: Dict[str, Any] = Depends(get_identity_context)) -> Dict[str, Any]:
    if identity["is_super_admin"]:
        return identity

    is_admin_member = any(m.get("role") == "admin" for m in identity["hospital_memberships"])
    if identity["role"] != "admin" and not is_admin_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital admin privileges required"
        )
    return identity

def require_patient_user(identity: Dict[str, Any] = Depends(get_identity_context)) -> Dict[str, Any]:
    if identity["role"] not in ["user", "patient", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required"
        )
    return identity

def require_hospital_scope(identity: Dict[str, Any] = Depends(get_identity_context)) -> Optional[str]:
    """
    Enforces backend hospital-scoped query filtering. Returns requester's hospital_id.
    Never trusts frontend-supplied hospital_id unless requester is super_admin.
    """
    if identity["is_super_admin"]:
        return None  # Unrestricted global access for super_admin
    
    hospital_id = identity.get("hospital_id")
    if not hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any hospital entity"
        )
    return hospital_id

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def get_doctor_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") not in ["doctor", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required"
        )
    
    doctors = []
    try:
        doctors = SupabaseService.get_records("doctors", {"profile_id": current_user["id"]})
    except Exception:
        pass

    if not doctors:
        all_docs = SupabaseService.get_records("doctors")
        u_email = (current_user.get("email") or "").lower()
        u_name = (current_user.get("name") or "").lower()
        for d in all_docs:
            if d.get("profile_id") == current_user["id"]:
                doctors.append(d)
                break
            d_first = d.get("name", "").replace("Dr. ", "").split()[0].lower()
            if d_first and u_email.startswith(d_first):
                doctors.append(d)
                break

    if not doctors and current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No doctor profile associated with this account"
        )
    
    doc_record = doctors[0] if doctors else {
        "id": "D_SUPER",
        "name": current_user.get("name", "Super Doctor"),
        "specialization": "General"
    }
    return {
        "user": current_user,
        "doctor": doc_record
    }

require_doctor = get_doctor_user

def create_n8n_context_token(
    user_id: str,
    role: str,
    hospital_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> str:
    """
    Issues a short-lived signed JWT token (15-minute validity) specifically for n8n AI tool calls.
    Cryptographically binds user identity, role, and hospital scoping.
    """
    payload = {
        "user_id": user_id,
        "role": role,
        "hospital_id": hospital_id or "H001",
        "session_id": session_id or "",
        "exp": int(time.time()) + 900
    }
    return jwt.encode(payload, settings.N8N_JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_n8n_tool_context(
    x_n8n_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency that every n8n AI tool endpoint uses to cryptographically verify context.
    Derives user_id, role, and hospital_id strictly from this verified signed JWT,
    never relying on LLM-generated text arguments.
    """
    token = x_n8n_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signed n8n AI context token (X-N8n-Token header required)"
        )

    try:
        payload = jwt.decode(token, settings.N8N_JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {
            "user_id": payload.get("user_id"),
            "role": payload.get("role", "patient"),
            "hospital_id": payload.get("hospital_id"),
            "session_id": payload.get("session_id"),
            "is_super_admin": payload.get("role") == "super_admin"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="n8n AI context token has expired"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid n8n AI context token"
        )

verify_n8n_context_token = verify_n8n_tool_context

