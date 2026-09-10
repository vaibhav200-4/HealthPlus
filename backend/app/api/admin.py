import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.auth.auth_handler import get_admin_user, hash_password
from app.database.supabase_client import SupabaseService
from app.schemas.doctor_schema import DoctorCreate, DoctorUpdate
from app.schemas.hospital_schema import HospitalCreate, HospitalUpdate
from app.schemas.appointment_schema import AppointmentStatusUpdate
from app.schemas.user_schema import HospitalAdminCreate, HospitalAdminResponse
from app.services.schedule_service import ScheduleService

logger = logging.getLogger("hospital_app.admin")

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])

@router.get("/stats")
def get_admin_stats(admin_user: dict = Depends(get_admin_user)):
    doctors = SupabaseService.get_records("doctors")
    hospitals = SupabaseService.get_records("hospitals")
    appointments = SupabaseService.get_records("appointments")
    users = SupabaseService.get_records("profiles")
    chats = SupabaseService.get_records("chat_messages")

    confirmed_app = len([a for a in appointments if a.get("status") == "confirmed"])
    pending_app = len([a for a in appointments if a.get("status") == "pending"])
    cancelled_app = len([a for a in appointments if a.get("status") == "cancelled"])

    return {
        "total_doctors": len(doctors),
        "total_hospitals": len(hospitals),
        "total_appointments": len(appointments),
        "confirmed_appointments": confirmed_app,
        "pending_appointments": pending_app,
        "cancelled_appointments": cancelled_app,
        "total_users": len(users),
        "total_chat_messages": len(chats)
    }

# 1. Doctors CRUD
@router.post("/doctors")
def create_doctor(data: DoctorCreate, admin_user: dict = Depends(get_admin_user)):
    existing = SupabaseService.get_record_by_id("doctors", data.id)
    if existing:
        raise HTTPException(status_code=400, detail="Doctor ID already exists")
    created = SupabaseService.insert_record("doctors", data.model_dump())
    return created

@router.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: str, data: DoctorUpdate, admin_user: dict = Depends(get_admin_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = SupabaseService.update_record("doctors", doctor_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return updated

@router.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: str, admin_user: dict = Depends(get_admin_user)):
    success = SupabaseService.delete_record("doctors", doctor_id)
    return {"success": success}

# 2. Hospitals CRUD
@router.post("/hospitals")
def create_hospital(data: HospitalCreate, admin_user: dict = Depends(get_admin_user)):
    existing = SupabaseService.get_record_by_id("hospitals", data.id)
    if existing:
        raise HTTPException(status_code=400, detail="Hospital ID already exists")
    created = SupabaseService.insert_record("hospitals", data.model_dump())
    return created

@router.put("/hospitals/{hospital_id}")
def update_hospital(hospital_id: str, data: HospitalUpdate, admin_user: dict = Depends(get_admin_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = SupabaseService.update_record("hospitals", hospital_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return updated

@router.delete("/hospitals/{hospital_id}")
def delete_hospital(hospital_id: str, admin_user: dict = Depends(get_admin_user)):
    linked_admins = SupabaseService.get_records("profiles", {"hospital_id": hospital_id, "role": "hospital_admin"})
    for adm in linked_admins:
        SupabaseService.delete_record("profiles", adm["id"])
    success = SupabaseService.delete_record("hospitals", hospital_id)
    return {"success": success}

def _find_hospital_admin_profiles(hospital_id: str) -> List[Dict[str, Any]]:
    admins = []
    seen_ids = set()

    # Strategy 1: Check profiles table if hospital_id column exists
    try:
        profs = SupabaseService.get_records("profiles", {"hospital_id": hospital_id, "role": "hospital_admin"})
        for p in profs:
            if p.get("id") and p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                admins.append(p)
    except Exception:
        pass

    # Strategy 2: Check hospital_members table
    try:
        members = SupabaseService.get_records("hospital_members", {"hospital_id": hospital_id, "role": "admin"})
        for m in members:
            uid = m.get("user_id")
            if uid and uid not in seen_ids:
                p = SupabaseService.get_record_by_id("profiles", uid)
                if p:
                    seen_ids.add(uid)
                    admins.append(p)
    except Exception:
        pass

    return admins

@router.get("/hospitals/{hospital_id}/admin-credentials", response_model=HospitalAdminResponse)
def get_hospital_admin_credentials(hospital_id: str, admin_user: dict = Depends(get_admin_user)):
    hospital = SupabaseService.get_record_by_id("hospitals", hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    linked_admins = _find_hospital_admin_profiles(hospital_id)
    if not linked_admins:
        return {"has_admin": False, "admin_user": None}
    
    adm = linked_admins[0]
    sanitized_user = {
        "id": adm["id"],
        "name": adm.get("name"),
        "email": adm.get("email"),
        "role": adm.get("role"),
        "hospital_id": adm.get("hospital_id") or hospital_id,
        "created_at": str(adm.get("created_at")) if adm.get("created_at") else None
    }
    return {"has_admin": True, "admin_user": sanitized_user}

@router.post("/hospitals/{hospital_id}/admin-credentials")
def create_or_update_hospital_admin(hospital_id: str, data: HospitalAdminCreate, admin_user: dict = Depends(get_admin_user)):
    hospital = SupabaseService.get_record_by_id("hospitals", hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    existing_email_user = SupabaseService.get_records("profiles", {"email": data.email})
    linked_admins = _find_hospital_admin_profiles(hospital_id)

    hashed_pwd = hash_password(data.password)
    admin_name = data.name or f"Admin ({hospital.get('hospital_name', 'Hospital')})"

    if linked_admins:
        admin_id = linked_admins[0]["id"]
        if existing_email_user and existing_email_user[0]["id"] != admin_id:
            raise HTTPException(status_code=400, detail="Email is already in use by another account")
        
        update_payload = {
            "name": admin_name,
            "email": data.email,
            "password_hash": hashed_pwd,
            "hospital_id": hospital_id,
            "role": "hospital_admin"
        }
        try:
            SupabaseService.update_record("profiles", admin_id, update_payload)
        except Exception:
            update_payload.pop("hospital_id", None)
            SupabaseService.update_record("profiles", admin_id, update_payload)

        existing_members = SupabaseService.get_records("hospital_members", {"hospital_id": hospital_id, "user_id": admin_id})
        if not existing_members:
            SupabaseService.insert_record("hospital_members", {
                "id": str(uuid.uuid4()),
                "hospital_id": hospital_id,
                "user_id": admin_id,
                "role": "admin"
            })

        return {"success": True, "message": "Hospital admin credentials updated successfully"}
    else:
        if existing_email_user:
            raise HTTPException(status_code=400, detail="Email is already in use by another account")
        
        user_id = str(uuid.uuid4())
        new_profile = {
            "id": user_id,
            "name": admin_name,
            "email": data.email,
            "password_hash": hashed_pwd,
            "role": "hospital_admin"
        }

        try:
            profile_payload = dict(new_profile)
            profile_payload["hospital_id"] = hospital_id
            SupabaseService.insert_record("profiles", profile_payload)
        except Exception as err:
            logger.warning(f"Insert to profiles with hospital_id failed, attempting without hospital_id: {err}")
            SupabaseService.insert_record("profiles", new_profile)
        
        SupabaseService.insert_record("hospital_members", {
            "id": str(uuid.uuid4()),
            "hospital_id": hospital_id,
            "user_id": user_id,
            "role": "admin"
        })

        return {"success": True, "message": "Hospital admin created successfully", "user_id": user_id}


# 3. Schedule Management
@router.post("/schedules")
def create_or_update_schedule(
    doctor_id: str,
    day_of_week: str,
    start_time: str,
    end_time: str,
    slot_duration_minutes: int = 30,
    admin_user: dict = Depends(get_admin_user)
):
    schedule_data = {
        "id": str(uuid.uuid4()),
        "doctor_id": doctor_id,
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
        "slot_duration_minutes": slot_duration_minutes,
        "is_active": True
    }
    created = SupabaseService.insert_record("schedules", schedule_data)
    return {"success": True, "message": "Schedule updated successfully", "schedule": created}

@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: str, admin_user: dict = Depends(get_admin_user)):
    success = SupabaseService.delete_record("schedules", schedule_id)
    return {"success": success}

# 4. Appointments Management
@router.get("/appointments")
def get_all_appointments(admin_user: dict = Depends(get_admin_user)):
    return SupabaseService.get_records("appointments")

@router.patch("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: str,
    data: AppointmentStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    updated = SupabaseService.update_record("appointments", appointment_id, {"status": data.status})
    if not updated:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"success": True, "appointment": updated}

# 5. Users Management
@router.get("/users")
def get_all_users(admin_user: dict = Depends(get_admin_user)):
    return SupabaseService.get_records("profiles")

# 6. Chat Logs Management
@router.get("/chat-history")
def get_all_chat_logs(admin_user: dict = Depends(get_admin_user)):
    return SupabaseService.get_records("chat_messages")
