from pydantic import BaseModel, Field
from typing import Optional

class DoctorReviewCreate(BaseModel):
    appointment_id: str
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None

class DoctorReviewResponse(BaseModel):
    id: str
    patient_id: str
    patient_code: Optional[str] = None
    doctor_id: str
    appointment_id: str
    rating: int
    review: Optional[str] = None
    created_at: Optional[str] = None
