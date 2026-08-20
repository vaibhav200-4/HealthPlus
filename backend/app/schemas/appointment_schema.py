from pydantic import BaseModel
from typing import Optional

class AppointmentCreate(BaseModel):
    doctor_id: str
    doctor_name: str
    hospital_name: str
    date: str  # YYYY-MM-DD
    start_time: str # e.g. "10:00 AM"
    end_time: str   # e.g. "10:30 AM"
    patient_name: str
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    notes: Optional[str] = None

class AppointmentReschedule(BaseModel):
    date: str
    start_time: str
    end_time: str

class AppointmentStatusUpdate(BaseModel):
    status: str # pending, confirmed, cancelled, completed

class AppointmentResponse(BaseModel):
    id: str
    user_id: str
    doctor_id: Optional[str] = None
    doctor_name: str
    hospital_name: str
    date: str
    start_time: str
    end_time: str
    calendar_event_id: Optional[str] = None
    status: str
    patient_name: str
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
