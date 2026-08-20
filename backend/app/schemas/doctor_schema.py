from pydantic import BaseModel
from typing import List, Optional

class DoctorBase(BaseModel):
    id: str
    hospital_id: str
    name: str
    degree: Optional[str] = None
    specialization: str
    experience_years: int = 0
    designation: Optional[str] = None
    languages: List[str] = []
    consultation_fee: float = 0.0
    availability: Optional[str] = None
    image_url: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    designation: Optional[str] = None
    languages: Optional[List[str]] = None
    consultation_fee: Optional[float] = None
    availability: Optional[str] = None
    image_url: Optional[str] = None

class DoctorSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
