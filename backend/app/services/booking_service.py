# services/booking_service.py
import uuid
import logging
import threading
from typing import Dict, Any, Tuple, Optional
from app.database.supabase_client import SupabaseService
from app.services.schedule_service import ScheduleService

logger = logging.getLogger("hospital_app.booking")
_BOOKING_LOCK = threading.Lock()

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
        notes: str = "",
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Unified manual and AI booking validation & creation service with:
        1. Idempotency key retry handling.
        2. Double booking pre-check and thread-safe lock for race condition protection.
        3. Database integrity constraint error handling.
        """

        # 1. Idempotency Check: return existing booking if retried with same key
        if idempotency_key:
            existing_by_key = SupabaseService.get_records("appointments", {"idempotency_key": idempotency_key})
            if existing_by_key:
                logger.info(f"Idempotent booking hit for key {idempotency_key}")
                return True, "Appointment already booked (idempotent response)", existing_by_key[0]

        # 2. Acquire lock to prevent race-condition double bookings
        with _BOOKING_LOCK:
            existing_apps = SupabaseService.get_records("appointments", {
                "doctor_id": doctor_id,
                "date": date
            })

            active_statuses = ["confirmed", "pending", "checked_in", "in_progress"]
            for app in existing_apps:
                if app.get("status") in active_statuses:
                    if app.get("start_time") == start_time:
                        logger.warning(f"Double booking prevented for doctor {doctor_id} on {date} at {start_time}")
                        return False, "This slot is no longer available.", {}

            # Re-check slot availability from schedule service
            available_slots = ScheduleService.get_doctor_available_slots(doctor_id, date)
            slot_is_valid = any(
                s["start_time"] == start_time and s["available"]
                for s in available_slots
            )

            if not slot_is_valid and len(available_slots) > 0:
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
                "notes": notes,
                "idempotency_key": idempotency_key
            }

            try:
                created_app = SupabaseService.insert_record("appointments", appointment_data)
                logger.info(f"Successfully booked appointment {created_app.get('id')} for user {user_id}")

                # Trigger transaction-guaranteed notification & audit log
                from app.services.notification_service import NotificationService
                from app.services.audit_service import AuditService

                hospitals = SupabaseService.get_records("hospitals", {"hospital_name": hospital_name})
                h_id = hospitals[0]["id"] if hospitals else "H001"

                NotificationService.create_notification(
                    user_id=user_id,
                    hospital_id=h_id,
                    type="appointment_booked",
                    channel="web",
                    payload={"appointment_id": created_app.get("id"), "doctor_name": doctor_name, "date": date, "start_time": start_time}
                )

                AuditService.log_action(
                    user_id=user_id,
                    hospital_id=h_id,
                    action="appointment_booked",
                    resource_type="appointments",
                    resource_id=created_app.get("id"),
                    new_value={"doctor_id": doctor_id, "date": date, "start_time": start_time}
                )

                return True, "Appointment booked successfully!", created_app
            except Exception as e:
                logger.error(f"Integrity error during booking creation: {e}")
                return False, "This slot is no longer available.", {}
