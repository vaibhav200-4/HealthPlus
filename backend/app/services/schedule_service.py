# services/schedule_service.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.database.supabase_client import SupabaseService

logger = logging.getLogger("hospital_app.schedules")

class ScheduleService:
    """
    Schedule Integration Service using Supabase schedules as the single source of truth.
    Calculates doctor slot availability cross-referencing active schedules, doctor leaves,
    blocked slots, capacity limits, and confirmed appointments.
    """

    @staticmethod
    def get_doctor_available_slots(doctor_id: str, date_str: str) -> List[Dict[str, Any]]:
        """
        Calculates available time slots for a given doctor on a specific date,
        cross-referencing active schedules, doctor leaves, holidays, blocked slots,
        and already confirmed/pending appointments.
        """

        # 1. Check if doctor is on leave on date_str
        leaves = SupabaseService.get_records("doctor_leaves", {"doctor_id": doctor_id, "leave_date": date_str})
        if leaves:
            logger.info(f"Doctor {doctor_id} is on leave on {date_str}")
            return []

        # 2. Check if date is a hospital holiday
        doctor = SupabaseService.get_record_by_id("doctors", doctor_id)
        hospital_id = doctor.get("hospital_id") if doctor else None
        if hospital_id:
            holidays = SupabaseService.get_records("hospital_holidays", {"hospital_id": hospital_id, "holiday_date": date_str})
            if holidays:
                logger.info(f"Hospital {hospital_id} is closed on holiday {date_str}")
                return []

        # 3. Fetch doctor active schedule
        schedules = SupabaseService.get_records("schedules", {"doctor_id": doctor_id, "is_active": True})
        
        default_slots = [
            {"start_time": "10:00 AM", "end_time": "10:30 AM", "capacity": 1},
            {"start_time": "10:30 AM", "end_time": "11:00 AM", "capacity": 1},
            {"start_time": "11:00 AM", "end_time": "11:30 AM", "capacity": 1},
            {"start_time": "11:30 AM", "end_time": "12:00 PM", "capacity": 1},
            {"start_time": "12:00 PM", "end_time": "12:30 PM", "capacity": 1},
            {"start_time": "03:00 PM", "end_time": "03:30 PM", "capacity": 1},
            {"start_time": "03:30 PM", "end_time": "04:00 PM", "capacity": 1},
            {"start_time": "04:00 PM", "end_time": "04:30 PM", "capacity": 1},
            {"start_time": "04:30 PM", "end_time": "05:00 PM", "capacity": 1},
        ]

        if not schedules:
            slots_to_check = default_slots
        else:
            slots_to_check = []
            for s in schedules:
                slots_to_check.append({
                    "start_time": s.get("start_time"),
                    "end_time": s.get("end_time"),
                    "capacity": s.get("slot_capacity", 1)
                })

        # 4. Fetch blocked slots override
        blocked_records = SupabaseService.get_records("blocked_slots", {"doctor_id": doctor_id, "slot_date": date_str})
        blocked_times = {b.get("start_time") for b in blocked_records}

        # 5. Fetch existing active appointments
        existing_appointments = SupabaseService.get_records("appointments", {
            "doctor_id": doctor_id,
            "date": date_str
        })
        
        active_statuses = ["confirmed", "pending", "checked_in", "in_progress"]
        booked_counts = {}
        for app in existing_appointments:
            if app.get("status") in active_statuses:
                st = app.get("start_time")
                booked_counts[st] = booked_counts.get(st, 0) + 1

        slot_results = []
        for slot in slots_to_check:
            st = slot["start_time"]
            cap = slot.get("capacity", 1)
            is_blocked = st in blocked_times
            current_bookings = booked_counts.get(st, 0)
            is_available = (not is_blocked) and (current_bookings < cap)

            slot_results.append({
                "start_time": st,
                "end_time": slot["end_time"],
                "capacity": cap,
                "booked": current_bookings,
                "blocked": is_blocked,
                "available": is_available
            })
        return slot_results

    @staticmethod
    def detect_affected_appointments(doctor_id: str, date_str: str, new_valid_start_times: List[str]) -> List[Dict[str, Any]]:
        """
        Identifies active appointments that fall outside valid schedule slots when an admin modifies schedules.
        """
        existing = SupabaseService.get_records("appointments", {"doctor_id": doctor_id, "date": date_str})
        active_statuses = ["confirmed", "pending", "checked_in", "in_progress"]
        affected = []
        valid_set = set(new_valid_start_times)
        
        for app in existing:
            if app.get("status") in active_statuses:
                if app.get("start_time") not in valid_set:
                    affected.append(app)
        return affected
