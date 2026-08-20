# Note: n8n's AI Agent workflow must be updated manually to replace its Google Sheets nodes ('Get row(s) google sheet' and 'Append row in sheet in Google Sheets') with a Postgres node pointed at this same Supabase schedules/appointments tables, using the Supabase connection pooler credentials. The AI Agent's booking tool should call this backend's POST /api/appointments endpoint instead of writing directly to Postgres, so that BookingService's double-booking validation applies to AI-made bookings too.

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.database.supabase_client import SupabaseService

logger = logging.getLogger("hospital_app.schedules")

class ScheduleService:
    """
    Schedule Integration Service using Supabase schedules as the single source of truth.
    Calculates doctor slot availability cross-referencing active schedules and confirmed appointments.
    """

    @staticmethod
    def get_doctor_available_slots(doctor_id: str, date_str: str) -> List[Dict[str, Any]]:
        """
        Calculates available time slots for a given doctor on a specific date,
        cross-referencing active schedules and already confirmed appointments.
        """
        # Fetch doctor schedule
        schedules = SupabaseService.get_records("schedules", {"doctor_id": doctor_id, "is_active": True})
        
        # Default working slots if schedule not explicitly configured in DB
        default_slots = [
            {"start_time": "10:00 AM", "end_time": "10:30 AM"},
            {"start_time": "10:30 AM", "end_time": "11:00 AM"},
            {"start_time": "11:00 AM", "end_time": "11:30 AM"},
            {"start_time": "11:30 AM", "end_time": "12:00 PM"},
            {"start_time": "12:00 PM", "end_time": "12:30 PM"},
            {"start_time": "03:00 PM", "end_time": "03:30 PM"},
            {"start_time": "03:30 PM", "end_time": "04:00 PM"},
            {"start_time": "04:00 PM", "end_time": "04:30 PM"},
            {"start_time": "04:30 PM", "end_time": "05:00 PM"},
        ]

        if not schedules:
            doctor = SupabaseService.get_record_by_id("doctors", doctor_id)
            if doctor and doctor.get("availability"):
                logger.info(f"Using default availability for doctor {doctor_id}")
            slots_to_check = default_slots
        else:
            slots_to_check = []
            for s in schedules:
                slots_to_check.append({
                    "start_time": s.get("start_time"),
                    "end_time": s.get("end_time")
                })

        # Fetch existing confirmed appointments for doctor on date_str
        existing_appointments = SupabaseService.get_records("appointments", {
            "doctor_id": doctor_id,
            "date": date_str
        })
        
        booked_times = {
            f"{app.get('start_time')}-{app.get('end_time')}" 
            for app in existing_appointments 
            if app.get("status") in ["confirmed", "pending"]
        }

        slot_results = []
        for slot in slots_to_check:
            key = f"{slot['start_time']}-{slot['end_time']}"
            slot_results.append({
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "available": key not in booked_times
            })
        return slot_results
