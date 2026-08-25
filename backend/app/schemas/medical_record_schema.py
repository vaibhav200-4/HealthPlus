from pydantic import BaseModel
from typing import Optional

class MedicalRecordBase(BaseModel):
    id: str
    patient_id: str
    patient_code: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    session_id: Optional[str] = None
    record_type: str
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    signed_file_url: Optional[str] = None
    uploaded_by: Optional[str] = "patient"
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MedicalRecordCreate(BaseModel):
    patient_id: str
    session_id: Optional[str] = None
    record_type: str = "diagnosis"
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    uploaded_by: Optional[str] = "patient"
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
