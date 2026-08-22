import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from app.schemas.prescription_schema import PrescriptionResponse, PrescriptionCreate
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import get_identity_context, require_doctor

router = APIRouter(prefix="/api/prescriptions", tags=["Prescriptions"])

@router.post("", response_model=PrescriptionResponse)
def create_prescription(data: PrescriptionCreate, doctor_info: dict = Depends(require_doctor)):
    doc_id = doctor_info["doctor"]["id"]
    doc_name = doctor_info["doctor"].get("name", "Dr. Specialist")

    # 1. Ownership & Validity Verification: Doctor can create prescription ONLY for a patient with a valid appointment/session
    patient_rec = SupabaseService.get_record_by_id("patients", data.patient_id)
    if not patient_rec:
        # Fallback search by profile_id
        pts = SupabaseService.get_records("patients", {"profile_id": data.patient_id})
        if pts:
            patient_rec = pts[0]
        else:
            raise HTTPException(status_code=404, detail="Patient record not found")

    patient_profile_id = patient_rec.get("profile_id")
    doctor_apps = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    has_valid_appointment = any(str(app.get("user_id")) == str(patient_profile_id) for app in doctor_apps)

    doctor_sessions = SupabaseService.get_records("sessions", {"doctor_id": doc_id, "patient_id": patient_rec["id"]})
    has_valid_session = len(doctor_sessions) > 0

    if not has_valid_appointment and not has_valid_session and doctor_info["user"].get("role") != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Doctor can only create prescriptions for patients with whom they have an active or past appointment/session"
        )

    p_id = str(uuid.uuid4())
    p_rec = {
        "id": p_id,
        "patient_id": patient_rec["id"],
        "doctor_id": doc_id,
        "session_id": data.session_id,
        "notes": data.notes or ""
    }
    created_p = SupabaseService.insert_record("prescriptions", p_rec)

    items = []
    for item in data.items:
        item_rec = {
            "id": str(uuid.uuid4()),
            "prescription_id": p_id,
            "medicine_name": item.medicine_name,
            "dosage": item.dosage or "",
            "frequency": item.frequency or "",
            "duration": item.duration or "",
            "instructions": item.instructions or ""
        }
        created_item = SupabaseService.insert_record("prescription_items", item_rec)
        items.append(created_item)

    return PrescriptionResponse(
        id=p_id,
        patient_id=patient_rec["id"],
        patient_code=patient_rec.get("patient_code"),
        doctor_id=doc_id,
        doctor_name=doc_name,
        session_id=data.session_id,
        notes=data.notes,
        items=items,
        created_at=created_p.get("created_at")
    )

@router.get("", response_model=List[PrescriptionResponse])
def get_prescriptions(identity: dict = Depends(get_identity_context), patient_id: Optional[str] = None):
    role = identity["role"]
    user_id = identity["user_id"]

    prescriptions = []
    if role in ["user", "patient"]:
        pts = SupabaseService.get_records("patients", {"profile_id": user_id})
        if not pts:
            return []
        patient_id = pts[0]["id"]
        prescriptions = SupabaseService.get_records("prescriptions", {"patient_id": patient_id})
    elif role == "doctor":
        doc_res = SupabaseService.get_records("doctors", {"profile_id": user_id})
        if doc_res:
            doc_id = doc_res[0]["id"]
            filters = {"doctor_id": doc_id}
            if patient_id:
                filters["patient_id"] = patient_id
            prescriptions = SupabaseService.get_records("prescriptions", filters)
    else: # Admin
        filters = {}
        if patient_id:
            filters["patient_id"] = patient_id
        prescriptions = SupabaseService.get_records("prescriptions", filters if filters else None)

    res = []
    for p in prescriptions:
        p_items = SupabaseService.get_records("prescription_items", {"prescription_id": p["id"]})
        p_rec = SupabaseService.get_record_by_id("patients", p.get("patient_id"))
        doc_rec = SupabaseService.get_record_by_id("doctors", p.get("doctor_id"))

        res.append(PrescriptionResponse(
            id=p["id"],
            patient_id=p["patient_id"],
            patient_code=p_rec.get("patient_code") if p_rec else None,
            doctor_id=p["doctor_id"],
            doctor_name=doc_rec.get("name") if doc_rec else "Doctor",
            session_id=p.get("session_id"),
            notes=p.get("notes"),
            items=p_items,
            created_at=p.get("created_at")
        ))

    return res

@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription_by_id(prescription_id: str, identity: dict = Depends(get_identity_context)):
    p = SupabaseService.get_record_by_id("prescriptions", prescription_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prescription not found")

    role = identity["role"]
    user_id = identity["user_id"]
    p_rec = SupabaseService.get_record_by_id("patients", p.get("patient_id"))

    if role in ["user", "patient"]:
        if not p_rec or p_rec.get("profile_id") != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to prescription")

    p_items = SupabaseService.get_records("prescription_items", {"prescription_id": p["id"]})
    doc_rec = SupabaseService.get_record_by_id("doctors", p.get("doctor_id"))

    return PrescriptionResponse(
        id=p["id"],
        patient_id=p["patient_id"],
        patient_code=p_rec.get("patient_code") if p_rec else None,
        doctor_id=p["doctor_id"],
        doctor_name=doc_rec.get("name") if doc_rec else "Doctor",
        session_id=p.get("session_id"),
        notes=p.get("notes"),
        items=p_items,
        created_at=p.get("created_at")
    )
