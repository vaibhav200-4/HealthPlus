import uuid
from typing import Dict, Any, Optional
from app.database.supabase_client import SupabaseService

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False

class PatientService:
    @staticmethod
    def resolve_patient(profile_or_patient_ref: str) -> Dict[str, Any]:
        """Returns the patients row, creating one if it doesn't exist. Single
        source of truth — medical_records.py, sessions.py, and agent/tools.py
        all call this instead of their own copies."""
        if not profile_or_patient_ref:
            return {}

        # 1. If reference is a valid UUID, check if it matches an existing patients.id
        if is_valid_uuid(profile_or_patient_ref):
            patient_rec = SupabaseService.get_record_by_id("patients", profile_or_patient_ref)
            if patient_rec:
                return patient_rec

        # 2. Check if reference matches an existing patients.profile_id
        pts = SupabaseService.get_records("patients", {"profile_id": str(profile_or_patient_ref)})
        if pts:
            return pts[0]

        # 3. Create a new patient record linked to this profile reference
        new_p_id = str(uuid.uuid4())
        all_pts = SupabaseService.get_records("patients")
        p_code = f"PT-{len(all_pts) + 1:06d}"
        new_p = {
            "id": new_p_id,
            "profile_id": str(profile_or_patient_ref),
            "patient_code": p_code
        }
        return SupabaseService.insert_record("patients", new_p)
