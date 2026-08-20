# backend/app/app/admin.py
import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.auth.auth_handler import get_admin_user
from app.database.supabase_client import SupabaseService
from app.schemas.doctor_schema import DoctorCreate, DoctorUpdate
from app.schemas.hospital_schema import HospitalCreate, HospitalUpdate
from app.schemas.appointment_schema import AppointmentStatusUpdate
from app.services.schedule_service import ScheduleService

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
    success = SupabaseService.delete_record("hospitals", hospital_id)
    return {"success": success}

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
