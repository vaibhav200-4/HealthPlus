from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any
from app.services.schedule_service import ScheduleService
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import get_admin_user

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])

@router.get("/doctor/{doctor_id}")
def get_doctor_slots(doctor_id: str, date: str = Query(..., description="YYYY-MM-DD")):
    slots = ScheduleService.get_doctor_available_slots(doctor_id=doctor_id, date_str=date)
    return {"doctor_id": doctor_id, "date": date, "slots": slots}

@router.get("")
def get_all_schedules():
    return SupabaseService.get_records("schedules")
