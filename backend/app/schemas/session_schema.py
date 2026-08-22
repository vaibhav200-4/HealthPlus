from pydantic import BaseModel
from typing import Optional

class SessionBase(BaseModel):
    id: str
    appointment_id: Optional[str] = None
    doctor_id: str
    patient_id: str
    patient_code: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    status: str = "in_progress"
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SessionCreate(BaseModel):
    appointment_id: str
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None

class SessionComplete(BaseModel):
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None
