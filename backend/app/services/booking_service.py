import uuid
import logging
from typing import Dict, Any, Tuple
from app.database.supabase_client import SupabaseService
from app.services.schedule_service import ScheduleService

logger = logging.getLogger("hospital_app.booking")

class BookingService:
    @staticmethod
    def create_appointment(
        user_id: str,
        doctor_id: str,
        doctor_name: str,
        hospital_name: str,
        date: str,
        start_time: str,
        end_time: str,
        patient_name: str,
        patient_phone: str = "",
        patient_email: str = "",
        notes: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Unified manual and AI booking validation & creation service.
        1. Validates server-side availability to prevent double-booking.
        2. Saves confirmed record to Supabase.
        3. Returns (success: bool, message: str, appointment_data: dict).
        """

        # 1. Double Booking Check: Query Supabase for active appointments matching doctor, date, start_time
        existing_apps = SupabaseService.get_records("appointments", {
            "doctor_id": doctor_id,
            "date": date
        })

        for app in existing_apps:
            if app.get("status") in ["confirmed", "pending"]:
                if app.get("start_time") == start_time:
                    logger.warning(f"Double booking prevented for doctor {doctor_id} on {date} at {start_time}")
                    return False, "This slot is no longer available.", {}

        # 2. Re-check slot availability from schedule service
        available_slots = ScheduleService.get_doctor_available_slots(doctor_id, date)
        slot_is_valid = any(
            s["start_time"] == start_time and s["available"]
            for s in available_slots
        )

        # Allow booking if default schedule matches or slot is free
        if not slot_is_valid and len(available_slots) > 0:
            # Double check if explicit conflict exists
            has_conflict = any(
                s["start_time"] == start_time and not s["available"]
                for s in available_slots
            )
            if has_conflict:
                return False, "This slot is no longer available.", {}

        # 3. Create appointment record
        calendar_event_id = f"gcal_{uuid.uuid4().hex[:10]}"
        appointment_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "hospital_name": hospital_name,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "calendar_event_id": calendar_event_id,
            "status": "confirmed",
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "patient_email": patient_email,
            "notes": notes
        }

        created_app = SupabaseService.insert_record("appointments", appointment_data)
        logger.info(f"Successfully booked appointment {created_app.get('id')} for user {user_id}")
        return True, "Appointment booked successfully!", created_app
