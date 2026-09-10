# backend/app/api/hospital_admin.py
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.auth.auth_handler import get_hospital_admin_user
from app.database.supabase_client import SupabaseService
from app.schemas.doctor_schema import DoctorCreate, DoctorUpdate
from app.schemas.hospital_schema import HospitalUpdate, HospitalBase
from app.schemas.department_schema import DepartmentCreate, DepartmentUpdate, DepartmentBase
from app.schemas.appointment_schema import AppointmentStatusUpdate

router = APIRouter(prefix="/api/hospital-admin", tags=["Hospital Admin Panel"])


def verify_doctor_hospital_ownership(doctor_id: str, hospital_id: str) -> Dict[str, Any]:
    doctor = SupabaseService.get_record_by_id("doctors", doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if doctor.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=403, detail="Doctor does not belong to your hospital")
    return doctor


def verify_department_hospital_ownership(department_id: str, hospital_id: str) -> Dict[str, Any]:
    department = SupabaseService.get_record_by_id("departments", department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    if department.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=403, detail="Department does not belong to your hospital")
    return department


def verify_appointment_hospital_ownership(appointment_id: str, hospital_id: str) -> Dict[str, Any]:
    appointment = SupabaseService.get_record_by_id("appointments", appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    doc_id = appointment.get("doctor_id")
    if doc_id:
        doctor = SupabaseService.get_record_by_id("doctors", doc_id)
        if doctor and doctor.get("hospital_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Appointment does not belong to your hospital")
    elif appointment.get("hospital_id") and appointment.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=403, detail="Appointment does not belong to your hospital")
    
    return appointment


# 1. Hospital Stats Scoped Endpoint
@router.get("/stats")
def get_hospital_admin_stats(admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    
    hospital_doctors = SupabaseService.get_records("doctors", {"hospital_id": hospital_id})
    doc_ids = {d["id"] for d in hospital_doctors}

    all_departments = SupabaseService.get_records("departments", {"hospital_id": hospital_id})
    all_appointments = SupabaseService.get_records("appointments")

    hospital_appointments = [
        a for a in all_appointments
        if (a.get("doctor_id") in doc_ids) or (a.get("hospital_id") == hospital_id)
    ]

    confirmed_app = len([a for a in hospital_appointments if a.get("status") == "confirmed"])
    pending_app = len([a for a in hospital_appointments if a.get("status") == "pending"])
    cancelled_app = len([a for a in hospital_appointments if a.get("status") == "cancelled"])
    completed_app = len([a for a in hospital_appointments if a.get("status") == "completed"])

    return {
        "hospital_id": hospital_id,
        "total_doctors": len(hospital_doctors),
        "total_departments": len(all_departments),
        "total_appointments": len(hospital_appointments),
        "confirmed_appointments": confirmed_app,
        "pending_appointments": pending_app,
        "cancelled_appointments": cancelled_app,
        "completed_appointments": completed_app
    }


# 2. Doctors CRUD Scoped
@router.get("/doctors")
def get_hospital_doctors(admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    return SupabaseService.get_records("doctors", {"hospital_id": hospital_id})


@router.post("/doctors")
def create_hospital_doctor(data: DoctorCreate, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    
    # Force hospital_id ownership
    doc_dict = data.model_dump()
    doc_dict["hospital_id"] = hospital_id

    existing = SupabaseService.get_record_by_id("doctors", data.id)
    if existing:
        raise HTTPException(status_code=400, detail="Doctor ID already exists")

    created = SupabaseService.insert_record("doctors", doc_dict)
    return created


@router.put("/doctors/{doctor_id}")
def update_hospital_doctor(doctor_id: str, data: DoctorUpdate, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    verify_doctor_hospital_ownership(doctor_id, hospital_id)

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["hospital_id"] = hospital_id  # Prevent changing hospital_id
    
    updated = SupabaseService.update_record("doctors", doctor_id, updates)
    return updated


@router.delete("/doctors/{doctor_id}")
def delete_hospital_doctor(doctor_id: str, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    verify_doctor_hospital_ownership(doctor_id, hospital_id)

    success = SupabaseService.delete_record("doctors", doctor_id)
    return {"success": success}


# 3. Departments CRUD Scoped
@router.get("/departments")
def get_hospital_departments(admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    return SupabaseService.get_records("departments", {"hospital_id": hospital_id})


@router.post("/departments")
def create_hospital_department(data: DepartmentCreate, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    
    dept_rec = {
        "id": str(uuid.uuid4()),
        "hospital_id": hospital_id,
        "name": data.name,
        "description": data.description or "",
        "status": data.status or "active"
    }
    created = SupabaseService.insert_record("departments", dept_rec)
    return created


@router.put("/departments/{department_id}")
def update_hospital_department(department_id: str, data: DepartmentUpdate, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    verify_department_hospital_ownership(department_id, hospital_id)

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["hospital_id"] = hospital_id

    updated = SupabaseService.update_record("departments", department_id, updates)
    return updated


@router.delete("/departments/{department_id}")
def delete_hospital_department(department_id: str, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    verify_department_hospital_ownership(department_id, hospital_id)

    success = SupabaseService.delete_record("departments", department_id)
    return {"success": success}


# 4. Schedules Scoped Management
@router.post("/schedules")
def create_or_update_hospital_schedule(
    doctor_id: str,
    day_of_week: str,
    start_time: str,
    end_time: str,
    slot_duration_minutes: int = 30,
    admin_user: dict = Depends(get_hospital_admin_user)
):
    hospital_id = admin_user["hospital_id"]
    verify_doctor_hospital_ownership(doctor_id, hospital_id)

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
    return {"success": True, "message": "Schedule slot updated successfully", "schedule": created}


@router.delete("/schedules/{schedule_id}")
def delete_hospital_schedule(schedule_id: str, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    schedule = SupabaseService.get_record_by_id("schedules", schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    doc_id = schedule.get("doctor_id")
    if doc_id:
        verify_doctor_hospital_ownership(doc_id, hospital_id)

    success = SupabaseService.delete_record("schedules", schedule_id)
    return {"success": success}


# 5. Appointments Scoped Management
@router.get("/appointments")
def get_hospital_appointments(admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    
    hospital_doctors = SupabaseService.get_records("doctors", {"hospital_id": hospital_id})
    doc_ids = {d["id"] for d in hospital_doctors}

    all_appointments = SupabaseService.get_records("appointments")
    hospital_appointments = [
        a for a in all_appointments
        if (a.get("doctor_id") in doc_ids) or (a.get("hospital_id") == hospital_id)
    ]
    return hospital_appointments


@router.patch("/appointments/{appointment_id}/status")
def update_hospital_appointment_status(
    appointment_id: str,
    data: AppointmentStatusUpdate,
    admin_user: dict = Depends(get_hospital_admin_user)
):
    hospital_id = admin_user["hospital_id"]
    verify_appointment_hospital_ownership(appointment_id, hospital_id)

    updated = SupabaseService.update_record("appointments", appointment_id, {"status": data.status})
    return {"success": True, "appointment": updated}


# 6. Hospital Profile Scoped Info
@router.get("/profile")
def get_hospital_profile(admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    hospital = SupabaseService.get_record_by_id("hospitals", hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital record not found")
    return hospital


@router.put("/profile")
def update_hospital_profile(data: HospitalUpdate, admin_user: dict = Depends(get_hospital_admin_user)):
    hospital_id = admin_user["hospital_id"]
    hospital = SupabaseService.get_record_by_id("hospitals", hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital record not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    # Ensure ID remains untouched
    updated = SupabaseService.update_record("hospitals", hospital_id, updates)
    return updated
