import uuid
import time
import jwt
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from app.schemas.medical_record_schema import MedicalRecordBase, MedicalRecordCreate
from app.database.supabase_client import SupabaseService, get_supabase_client
from app.auth.auth_handler import get_identity_context, get_doctor_user
from app.config import settings

router = APIRouter(prefix="/api/medical-records", tags=["Medical Records"])

def generate_signed_url(file_path: Optional[str]) -> Optional[str]:
    if not file_path:
        return None
    
    # Try Supabase storage signed URL
    client = get_supabase_client()
    if client:
        try:
            res = client.storage.from_("medical-records").create_signed_url(file_path, 3600)
            if res and isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
        except Exception:
            pass

    # Fallback short-lived signed URL token
    exp = int(time.time()) + 3600
    token_payload = {"path": file_path, "exp": exp}
    signed_token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return f"/api/medical-records/file?path={file_path}&token={signed_token}"

@router.post("", response_model=MedicalRecordBase)
def create_medical_record(data: MedicalRecordCreate, doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    doc_name = doctor_info["doctor"].get("name", "Doctor")

    patient_rec = SupabaseService.get_record_by_id("patients", data.patient_id)
    if not patient_rec:
        pts = SupabaseService.get_records("patients", {"profile_id": data.patient_id})
        if pts:
            patient_rec = pts[0]
        else:
            raise HTTPException(status_code=404, detail="Patient record not found")

    rec_id = str(uuid.uuid4())
    record_data = {
        "id": rec_id,
        "patient_id": patient_rec["id"],
        "doctor_id": doc_id,
        "session_id": data.session_id,
        "record_type": data.record_type,
        "title": data.title,
        "description": data.description or "",
        "file_url": data.file_url or ""
    }

    created = SupabaseService.insert_record("medical_records", record_data)
    signed_url = generate_signed_url(created.get("file_url"))

    return MedicalRecordBase(
        id=rec_id,
        patient_id=patient_rec["id"],
        patient_code=patient_rec.get("patient_code"),
        doctor_id=doc_id,
        doctor_name=doc_name,
        session_id=data.session_id,
        record_type=data.record_type,
        title=data.title,
        description=data.description,
        file_url=data.file_url,
        signed_file_url=signed_url,
        created_at=created.get("created_at")
    )

@router.get("", response_model=List[MedicalRecordBase])
def get_medical_records(identity: dict = Depends(get_identity_context), patient_id: Optional[str] = None):
    role = identity["role"]
    user_id = identity["user_id"]

    records = []
    if role in ["user", "patient"]:
        pts = SupabaseService.get_records("patients", {"profile_id": user_id})
        if not pts:
            return []
        p_id = pts[0]["id"]
        records = SupabaseService.get_records("medical_records", {"patient_id": p_id})
    elif role == "doctor":
        doc_res = SupabaseService.get_records("doctors", {"profile_id": user_id})
        if doc_res:
            doc_id = doc_res[0]["id"]
            filters = {"doctor_id": doc_id}
            if patient_id:
                filters["patient_id"] = patient_id
            records = SupabaseService.get_records("medical_records", filters)
    else: # Admin / super_admin
        filters = {}
        if patient_id:
            filters["patient_id"] = patient_id
        records = SupabaseService.get_records("medical_records", filters if filters else None)

    res = []
    for r in records:
        p_rec = SupabaseService.get_record_by_id("patients", r.get("patient_id"))
        d_rec = SupabaseService.get_record_by_id("doctors", r.get("doctor_id"))
        signed_url = generate_signed_url(r.get("file_url"))

        res.append(MedicalRecordBase(
            id=r["id"],
            patient_id=r["patient_id"],
            patient_code=p_rec.get("patient_code") if p_rec else None,
            doctor_id=r.get("doctor_id"),
            doctor_name=d_rec.get("name") if d_rec else "Doctor",
            session_id=r.get("session_id"),
            record_type=r.get("record_type", "other"),
            title=r.get("title", "Medical Record"),
            description=r.get("description"),
            file_url=r.get("file_url"),
            signed_file_url=signed_url,
            created_at=r.get("created_at")
        ))

    return res

@router.get("/{record_id}", response_model=MedicalRecordBase)
def get_medical_record_by_id(record_id: str, identity: dict = Depends(get_identity_context)):
    r = SupabaseService.get_record_by_id("medical_records", record_id)
    if not r:
        raise HTTPException(status_code=404, detail="Medical record not found")

    role = identity["role"]
    user_id = identity["user_id"]
    p_rec = SupabaseService.get_record_by_id("patients", r.get("patient_id"))

    if role in ["user", "patient"]:
        if not p_rec or p_rec.get("profile_id") != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to medical record")

    d_rec = SupabaseService.get_record_by_id("doctors", r.get("doctor_id"))
    signed_url = generate_signed_url(r.get("file_url"))

    return MedicalRecordBase(
        id=r["id"],
        patient_id=r["patient_id"],
        patient_code=p_rec.get("patient_code") if p_rec else None,
        doctor_id=r.get("doctor_id"),
        doctor_name=d_rec.get("name") if d_rec else "Doctor",
        session_id=r.get("session_id"),
        record_type=r.get("record_type", "other"),
        title=r.get("title", "Medical Record"),
        description=r.get("description"),
        file_url=r.get("file_url"),
        signed_file_url=signed_url,
        created_at=r.get("created_at")
    )
