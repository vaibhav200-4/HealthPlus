import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from app.auth.auth_handler import verify_n8n_tool_context
from app.database.supabase_client import SupabaseService
from app.services.booking_service import BookingService
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/api/ai-tools", tags=["AI Agent Role-Scoped Tools"])

# ==========================================
# PATIENT TOOLS
# ==========================================

@router.get("/search-doctors")
def ai_search_doctors(
    query: Optional[str] = None,
    specialization: Optional[str] = None,
    context: dict = Depends(verify_n8n_tool_context)
):
    # Server-side hospital_id injection from verified context
    h_id = context["hospital_id"]
    doctors = SupabaseService.get_records("doctors", {"hospital_id": h_id})
    if specialization:
        doctors = [d for d in doctors if d.get("specialization", "").lower() == specialization.lower()]
    if query:
        q = query.lower()
        doctors = [d for d in doctors if q in d.get("name", "").lower() or q in d.get("specialization", "").lower()]
    return doctors

@router.get("/search-hospitals")
def ai_search_hospitals(context: dict = Depends(verify_n8n_tool_context)):
    h_id = context["hospital_id"]
    hospitals = SupabaseService.get_records("hospitals", {"id": h_id})
    if not hospitals:
        hospitals = SupabaseService.get_records("hospitals")
    return hospitals

@router.get("/get-doctor-availability")
def ai_get_doctor_availability(
    doctor_id: str,
    date: str,
    context: dict = Depends(verify_n8n_tool_context)
):
    return ScheduleService.get_doctor_available_slots(doctor_id, date)

@router.post("/book-appointment")
def ai_book_appointment(
    payload: Dict[str, Any],
    context: dict = Depends(verify_n8n_tool_context)
):
    # Server-side user_id & hospital_id injection from verified context (LLM cannot forge identity)
    user_id = context["user_id"]
    
    # Resolve patient details
    profiles = SupabaseService.get_records("profiles", {"id": user_id})
    p_name = profiles[0].get("name", "Patient") if profiles else "Patient"
    p_phone = profiles[0].get("phone", "") if profiles else ""
    p_email = profiles[0].get("email", "") if profiles else ""

    doc_id = payload.get("doctor_id")
    doctor = SupabaseService.get_record_by_id("doctors", doc_id)
    doc_name = doctor.get("name", "Doctor") if doctor else "Doctor"

    hospitals = SupabaseService.get_records("hospitals", {"id": context["hospital_id"]})
    h_name = hospitals[0].get("hospital_name", "Hospital") if hospitals else "Hospital"

    success, msg, app_data = BookingService.create_appointment(
        user_id=user_id,
        doctor_id=doc_id,
        doctor_name=doc_name,
        hospital_name=h_name,
        date=payload.get("date"),
        start_time=payload.get("start_time"),
        end_time=payload.get("end_time", ""),
        patient_name=p_name,
        patient_phone=p_phone,
        patient_email=p_email,
        notes=payload.get("notes", "Booked via AI Assistant"),
        idempotency_key=payload.get("idempotency_key")
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return app_data

@router.post("/cancel-appointment")
def ai_cancel_appointment(
    payload: Dict[str, Any],
    context: dict = Depends(verify_n8n_tool_context)
):
    user_id = context["user_id"]
    app_id = payload.get("appointment_id")

    app = SupabaseService.get_record_by_id("appointments", app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if str(app.get("user_id")) != str(user_id) and not context["is_super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized to cancel this appointment")

    updated = SupabaseService.update_record("appointments", app_id, {"status": "cancelled"})
    return {"success": True, "appointment": updated}

@router.get("/my-appointments")
def ai_get_my_appointments(context: dict = Depends(verify_n8n_tool_context)):
    user_id = context["user_id"]
    return SupabaseService.get_records("appointments", {"user_id": user_id})

@router.get("/my-sessions")
def ai_get_my_sessions(context: dict = Depends(verify_n8n_tool_context)):
    user_id = context["user_id"]
    pts = SupabaseService.get_records("patients", {"profile_id": user_id})
    if not pts:
        return []
    patient_id = pts[0]["id"]
    sessions = SupabaseService.get_records("sessions", {"patient_id": patient_id})
    
    # Privacy isolation: Strip doctor_notes for patient AI session
    for s in sessions:
        s["doctor_notes"] = None
    return sessions

@router.get("/my-prescriptions")
def ai_get_my_prescriptions(context: dict = Depends(verify_n8n_tool_context)):
    user_id = context["user_id"]
    pts = SupabaseService.get_records("patients", {"profile_id": user_id})
    if not pts:
        return []
    patient_id = pts[0]["id"]
    prescriptions = SupabaseService.get_records("prescriptions", {"patient_id": patient_id})
    for p in prescriptions:
        p["items"] = SupabaseService.get_records("prescription_items", {"prescription_id": p["id"]})
    return prescriptions

@router.get("/my-profile")
def ai_get_my_profile(context: dict = Depends(verify_n8n_tool_context)):
    user_id = context["user_id"]
    profiles = SupabaseService.get_records("profiles", {"id": user_id})
    if not profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    p = profiles[0]
    pts = SupabaseService.get_records("patients", {"profile_id": user_id})
    if pts:
        p["patient_code"] = pts[0].get("patient_code")
    return p

# ==========================================
# DOCTOR TOOLS
# ==========================================

@router.get("/doctor-appointments")
def ai_get_doctor_appointments(context: dict = Depends(verify_n8n_tool_context)):
    if context["role"] not in ["doctor", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Doctor privileges required for AI tool")

    user_id = context["user_id"]
    docs = SupabaseService.get_records("doctors", {"profile_id": user_id})
    if not docs and not context["is_super_admin"]:
        raise HTTPException(status_code=403, detail="Doctor profile not found")

    doc_id = docs[0]["id"] if docs else "D001"
    return SupabaseService.get_records("appointments", {"doctor_id": doc_id})

@router.get("/doctor-patients")
def ai_get_doctor_patients(context: dict = Depends(verify_n8n_tool_context)):
    if context["role"] not in ["doctor", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Doctor privileges required for AI tool")

    user_id = context["user_id"]
    docs = SupabaseService.get_records("doctors", {"profile_id": user_id})
    if not docs and not context["is_super_admin"]:
        raise HTTPException(status_code=403, detail="Doctor profile not found")

    doc_id = docs[0]["id"] if docs else "D001"
    apps = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    patient_ids = {a.get("user_id") for a in apps if a.get("user_id")}

    result = []
    for pid in patient_ids:
        pts = SupabaseService.get_records("patients", {"profile_id": pid})
        profs = SupabaseService.get_records("profiles", {"id": pid})
        if profs:
            rec = dict(profs[0])
            if pts:
                rec["patient_code"] = pts[0].get("patient_code")
            result.append(rec)
    return result

# ==========================================
# ADMIN TOOLS
# ==========================================

@router.get("/hospital-stats")
def ai_get_hospital_stats(context: dict = Depends(verify_n8n_tool_context)):
    if context["role"] not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin privileges required for AI tool")

    h_id = context["hospital_id"]
    docs = SupabaseService.get_records("doctors", {"hospital_id": h_id} if not context["is_super_admin"] else None)
    apps = SupabaseService.get_records("appointments")

    return {
        "hospital_id": h_id,
        "total_doctors": len(docs),
        "total_appointments": len(apps),
        "confirmed_appointments": len([a for a in apps if a.get("status") == "confirmed"]),
        "completed_appointments": len([a for a in apps if a.get("status") == "completed"])
    }
