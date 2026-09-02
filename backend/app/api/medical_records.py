# api/medical_records.py
import uuid
import time
import jwt
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile, Form, Header
from typing import List, Optional, Dict, Any
from app.schemas.medical_record_schema import MedicalRecordBase, MedicalRecordCreate
from app.database.supabase_client import SupabaseService, get_supabase_client
from app.auth.auth_handler import get_identity_context, get_doctor_user
from app.config import settings

router = APIRouter(prefix="/api/medical-records", tags=["Medical Records"])

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

MIME_TO_EXT = {
    'application/pdf': 'pdf',
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp'
}

VALID_RECORD_TYPES = {'diagnosis', 'lab_report', 'xray', 'mri', 'blood_test', 'discharge_summary', 'other'}

def generate_signed_url(file_path: Optional[str]) -> Optional[str]:
    if not file_path:
        return None
    
    client = get_supabase_client()
    if client:
        try:
            res = client.storage.from_("medical-records").create_signed_url(file_path, 3600)
            if res and isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
        except Exception:
            pass

    exp = int(time.time()) + 3600
    token_payload = {"path": file_path, "exp": exp}
    signed_token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return f"/api/medical-records/file?path={file_path}&token={signed_token}"

from app.services.patient_service import PatientService

def resolve_patient_id(patient_identifier: str) -> str:
    p_rec = PatientService.resolve_patient(patient_identifier)
    return p_rec.get("id", "")

@router.post("/upload", response_model=MedicalRecordBase)
async def upload_medical_record(
    file: UploadFile = File(...),
    patient_identifier: str = Form(...),
    uploaded_by: str = Form("patient"),
    doctor_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    record_type: Optional[str] = Form(None),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    x_telegram_secret: Optional[str] = Header(None),
    x_n8n_secret: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    # TASK 1: Strict Auth Lockdown
    # n8n / Telegram server-to-server calls MUST provide X-Telegram-Secret matching TELEGRAM_WEBHOOK_SECRET.
    # n8n_token Bearer tokens are explicitly disabled for this endpoint to prevent false 401s on upstream context failures.
    # Browser web app / doctor portal calls send user JWT token via Authorization Bearer header.
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    provided_secret = x_telegram_secret or x_n8n_secret

    authenticated = False
    if provided_secret:
        if provided_secret == secret:
            authenticated = True
        else:
            raise HTTPException(status_code=401, detail="Invalid X-Telegram-Secret header")
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            # Strictly decode with user JWT_SECRET (rejecting n8n_token which uses N8N_JWT_SECRET)
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            if payload and payload.get("user_id"):
                authenticated = True
        except Exception:
            pass

    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized upload request. Valid X-Telegram-Secret header or user Bearer JWT token required."
        )

    if uploaded_by not in ['patient', 'doctor', 'admin']:
        raise HTTPException(status_code=400, detail="uploaded_by must be 'patient', 'doctor', or 'admin'")

    # TASK 2: Default record_type to "other" if omitted, empty, or unrecognised
    if not record_type or not record_type.strip() or record_type.strip().lower() not in VALID_RECORD_TYPES:
        final_record_type = "other"
    else:
        final_record_type = record_type.strip().lower()

    # TASK 3: File Extension & MIME Type extraction
    ext = ""
    if file.filename and "." in file.filename:
        ext = file.filename.split(".")[-1].lower()

    if not ext or ext not in ALLOWED_EXTENSIONS:
        content_type = (file.content_type or "").lower()
        if content_type in MIME_TO_EXT:
            ext = MIME_TO_EXT[content_type]

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '.{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 15MB")

    target_patient_id = resolve_patient_id(patient_identifier)

    rec_id = str(uuid.uuid4())
    storage_path = f"{target_patient_id}/{rec_id}.{ext}"

    client = get_supabase_client()
    if client:
        try:
            try:
                client.storage.create_bucket("medical-records", options={"public": False})
            except Exception:
                pass
            client.storage.from_("medical-records").upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": file.content_type or "application/octet-stream"}
            )
        except Exception:
            pass

    record_data = {
        "id": rec_id,
        "patient_id": target_patient_id,
        "doctor_id": doctor_id,
        "session_id": session_id,
        "record_type": final_record_type,
        "title": title,
        "description": description or "",
        "file_url": storage_path,
        "uploaded_by": uploaded_by,
        "file_type": ext,
        "file_size_bytes": file_size
    }

    created = SupabaseService.insert_record("medical_records", record_data)
    signed_url = generate_signed_url(storage_path)

    p_rec = SupabaseService.get_record_by_id("patients", target_patient_id)
    d_rec = SupabaseService.get_record_by_id("doctors", doctor_id) if doctor_id else None

    return MedicalRecordBase(
        id=rec_id,
        patient_id=target_patient_id,
        patient_code=p_rec.get("patient_code") if p_rec else None,
        doctor_id=doctor_id,
        doctor_name=d_rec.get("name") if d_rec else ("Doctor" if uploaded_by == "doctor" else None),
        session_id=session_id,
        record_type=final_record_type,
        title=title,
        description=description,
        file_url=storage_path,
        signed_file_url=signed_url,
        uploaded_by=uploaded_by,
        file_type=ext,
        file_size_bytes=file_size,
        created_at=created.get("created_at")
    )

@router.get("/patient/{patient_id}", response_model=List[MedicalRecordBase])
def get_patient_medical_records(patient_id: str, identity: dict = Depends(get_identity_context)):
    candidate_ids = {patient_id}
    p_rec = SupabaseService.get_record_by_id("patients", patient_id)
    if not p_rec:
        pts = SupabaseService.get_records("patients", {"profile_id": patient_id})
        if pts:
            p_rec = pts[0]
            candidate_ids.add(p_rec["id"])
            if p_rec.get("profile_id"):
                candidate_ids.add(p_rec["profile_id"])
    else:
        if p_rec.get("profile_id"):
            candidate_ids.add(p_rec["profile_id"])

    records_dict = {}
    for cid in candidate_ids:
        recs = SupabaseService.get_records("medical_records", {"patient_id": cid})
        for r in recs:
            records_dict[r["id"]] = r

    records = list(records_dict.values())

    def get_sort_key(r):
        return r.get("created_at") or ""
    
    records = sorted(records, key=get_sort_key, reverse=True)

    res = []
    for r in records:
        d_rec = SupabaseService.get_record_by_id("doctors", r.get("doctor_id")) if r.get("doctor_id") else None
        p_info = p_rec or SupabaseService.get_record_by_id("patients", r.get("patient_id"))
        signed_url = generate_signed_url(r.get("file_url"))

        res.append(MedicalRecordBase(
            id=r["id"],
            patient_id=r["patient_id"],
            patient_code=p_info.get("patient_code") if p_info else None,
            doctor_id=r.get("doctor_id"),
            doctor_name=d_rec.get("name") if d_rec else None,
            session_id=r.get("session_id"),
            record_type=r.get("record_type", "other"),
            title=r.get("title", "Medical Record"),
            description=r.get("description"),
            file_url=r.get("file_url"),
            signed_file_url=signed_url,
            uploaded_by=r.get("uploaded_by", "patient"),
            file_type=r.get("file_type"),
            file_size_bytes=r.get("file_size_bytes"),
            created_at=r.get("created_at")
        ))

    return res

@router.get("/patient/{patient_id}/summary")
def get_patient_clinical_summary(
    patient_id: str,
    identity: dict = Depends(get_identity_context)
):
    """
    Get doctor-facing patient clinical summary synthesized from intake notes,
    medical records, and appointments with MAX(created_at) caching.
    """
    from app.services.summary_service import SummaryService
    return SummaryService.generate_patient_summary(patient_id)


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
        "file_url": data.file_url or "",
        "uploaded_by": data.uploaded_by or "doctor",
        "file_type": data.file_type,
        "file_size_bytes": data.file_size_bytes
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
        uploaded_by=data.uploaded_by or "doctor",
        file_type=data.file_type,
        file_size_bytes=data.file_size_bytes,
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
    else:
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
            uploaded_by=r.get("uploaded_by", "patient"),
            file_type=r.get("file_type"),
            file_size_bytes=r.get("file_size_bytes"),
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
        uploaded_by=r.get("uploaded_by", "patient"),
        file_type=r.get("file_type"),
        file_size_bytes=r.get("file_size_bytes"),
        created_at=r.get("created_at")
    )
