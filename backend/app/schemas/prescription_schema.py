from pydantic import BaseModel
from typing import List, Optional

class PrescriptionItemBase(BaseModel):
    id: Optional[str] = None
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

class PrescriptionItemCreate(BaseModel):
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

class PrescriptionCreate(BaseModel):
    patient_id: str
    session_id: Optional[str] = None
    notes: Optional[str] = None
    items: List[PrescriptionItemCreate] = []

class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    patient_code: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    session_id: Optional[str] = None
    notes: Optional[str] = None
    items: List[PrescriptionItemBase] = []
    created_at: Optional[str] = None
