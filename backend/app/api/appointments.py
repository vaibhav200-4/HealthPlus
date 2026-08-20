# backend/app/appointment.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from app.schemas.appointment_schema import AppointmentCreate, AppointmentReschedule, AppointmentResponse
from app.services.booking_service import BookingService
from app.auth.auth_handler import get_current_user
from app.database.supabase_client import SupabaseService

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

@router.post("", response_model=Dict[str, Any])
def create_manual_appointment(data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    success, message, app_data = BookingService.create_appointment(
        user_id=user_id,
        doctor_id=data.doctor_id,
        doctor_name=data.doctor_name,
        hospital_name=data.hospital_name,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        patient_name=data.patient_name,
        patient_phone=data.patient_phone or current_user.get("phone", ""),
        patient_email=data.patient_email or current_user.get("email", ""),
        notes=data.notes or ""
    )

    if not success:
        return {
            "success": False,
            "message": message
        }

    return {
        "success": True,
        "message": message,
        "appointment": app_data
    }

@router.get("/my", response_model=List[AppointmentResponse])
def get_user_appointments(current_user: dict = Depends(get_current_user)):
    appointments = SupabaseService.get_records("appointments", {"user_id": current_user["id"]})
    return appointments

@router.patch("/{appointment_id}/cancel")
def cancel_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    app = SupabaseService.get_record_by_id("appointments", appointment_id)
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if app["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access to appointment")

    updated = SupabaseService.update_record("appointments", appointment_id, {"status": "cancelled"})
    return {"success": True, "message": "Appointment cancelled successfully", "appointment": updated}

@router.patch("/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: str,
    data: AppointmentReschedule,
    current_user: dict = Depends(get_current_user)
):
    app = SupabaseService.get_record_by_id("appointments", appointment_id)
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if app["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access to appointment")

    # Double-booking check for new date/time
    conflict = SupabaseService.get_records("appointments", {
        "doctor_id": app["doctor_id"],
        "date": data.date
    })
    for c in conflict:
        if c["id"] != appointment_id and c["status"] in ["confirmed", "pending"] and c["start_time"] == data.start_time:
            return {"success": False, "message": "This slot is no longer available."}

    updated = SupabaseService.update_record("appointments", appointment_id, {
        "date": data.date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "status": "confirmed"
    })
    return {"success": True, "message": "Appointment rescheduled successfully", "appointment": updated}
