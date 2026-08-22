import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from app.schemas.session_schema import SessionBase, SessionCreate, SessionComplete
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import get_identity_context, require_doctor

router = APIRouter(prefix="/api/sessions", tags=["Medical Sessions"])

def get_patient_by_profile_or_id(patient_ref: str) -> Optional[Dict[str, Any]]:
    # Try finding patient by patients.id or profile_id
    pts = SupabaseService.get_records("patients", {"id": patient_ref})
    if pts:
        return pts[0]
    pts = SupabaseService.get_records("patients", {"profile_id": patient_ref})
    if pts:
        return pts[0]
    # Auto-create patient record if not exists
    p_code = f"PT-{len(SupabaseService.get_records('patients')) + 1:06d}"
    rec = {
        "id": str(uuid.uuid4()),
        "profile_id": patient_ref,
        "patient_code": p_code
    }
    return SupabaseService.insert_record("patients", rec)

@router.post("", response_model=SessionBase)
def create_session(data: SessionCreate, doctor_info: dict = Depends(require_doctor)):
    doc_id = doctor_info["doctor"]["id"]
    app = SupabaseService.get_record_by_id("appointments", data.appointment_id)
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if app.get("doctor_id") != doc_id and doctor_info["user"].get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Unauthorized: Doctor does not own this appointment")

    # Resolve patient_id (FK to patients.id)
    user_id = app.get("user_id")
    patient_rec = get_patient_by_profile_or_id(user_id)
    patient_id = patient_rec["id"]
    patient_code = patient_rec.get("patient_code")

    session_rec = {
        "id": str(uuid.uuid4()),
        "appointment_id": data.appointment_id,
        "doctor_id": doc_id,
        "patient_id": patient_id,
        "started_at": datetime.now().isoformat(),
        "status": "in_progress",
        "symptoms": data.symptoms or "",
        "diagnosis": data.diagnosis or "",
        "doctor_notes": data.doctor_notes or ""
    }

    created = SupabaseService.insert_record("sessions", session_rec)
    created["patient_code"] = patient_code
    return created

@router.patch("/{session_id}/complete", response_model=SessionBase)
def complete_session(session_id: str, data: SessionComplete, doctor_info: dict = Depends(require_doctor)):
    session = SupabaseService.get_record_by_id("sessions", session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Medical session not found")

    doc_id = doctor_info["doctor"]["id"]
    if session.get("doctor_id") != doc_id and doctor_info["user"].get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Unauthorized access to session")

    updates = {
        "status": "completed",
        "ended_at": datetime.now().isoformat()
    }
    if data.symptoms is not None:
        updates["symptoms"] = data.symptoms
    if data.diagnosis is not None:
        updates["diagnosis"] = data.diagnosis
    if data.doctor_notes is not None:
        updates["doctor_notes"] = data.doctor_notes

    updated = SupabaseService.update_record("sessions", session_id, updates)
    
    # Also update associated appointment status to completed
    if session.get("appointment_id"):
        SupabaseService.update_record("appointments", session["appointment_id"], {"status": "completed"})

    patient_rec = SupabaseService.get_record_by_id("patients", session.get("patient_id"))
    if updated and patient_rec:
        updated["patient_code"] = patient_rec.get("patient_code")
    return updated

@router.get("", response_model=List[SessionBase])
def get_sessions(identity: dict = Depends(get_identity_context), patient_id: Optional[str] = None):
    role = identity["role"]
    user_id = identity["user_id"]
    
    sessions = []
    if role in ["user", "patient"]:
        patient_rec = get_patient_by_profile_or_id(user_id)
        sessions = SupabaseService.get_records("sessions", {"patient_id": patient_rec["id"]})
    elif role == "doctor":
        doc_res = SupabaseService.get_records("doctors", {"profile_id": user_id})
        if doc_res:
            doc_id = doc_res[0]["id"]
            filters = {"doctor_id": doc_id}
            if patient_id:
                filters["patient_id"] = patient_id
            sessions = SupabaseService.get_records("sessions", filters)
    else: # admin / super_admin
        filters = {}
        if patient_id:
            filters["patient_id"] = patient_id
        sessions = SupabaseService.get_records("sessions", filters if filters else None)

    # Attach patient_code and strip doctor_notes for patient caller
    result = []
    for s in sessions:
        p_rec = SupabaseService.get_record_by_id("patients", s.get("patient_id"))
        s_copy = dict(s)
        s_copy["patient_code"] = p_rec.get("patient_code") if p_rec else None
        
        # Privacy isolation: Never expose doctor_notes to patients
        if role in ["user", "patient"]:
            s_copy["doctor_notes"] = None

        result.append(s_copy)

    return result

@router.get("/{session_id}", response_model=SessionBase)
def get_session_by_id(session_id: str, identity: dict = Depends(get_identity_context)):
    s = SupabaseService.get_record_by_id("sessions", session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Medical session not found")

    role = identity["role"]
    user_id = identity["user_id"]
    p_rec = SupabaseService.get_record_by_id("patients", s.get("patient_id"))

    if role in ["user", "patient"]:
        if not p_rec or p_rec.get("profile_id") != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to medical session")

    s_copy = dict(s)
    s_copy["patient_code"] = p_rec.get("patient_code") if p_rec else None
    if role in ["user", "patient"]:
        s_copy["doctor_notes"] = None
    return s_copy
