from pydantic import BaseModel
from typing import List, Optional

class DoctorBase(BaseModel):
    id: str
    profile_id: Optional[str] = None
    hospital_id: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    name: str
    degree: Optional[str] = None
    specialization: str
    experience_years: Optional[int] = 0
    designation: Optional[str] = None
    languages: Optional[List[str]] = []
    consultation_fee: Optional[float] = 0.0
    availability: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = 5.0
    total_reviews: Optional[int] = 0

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    profile_id: Optional[str] = None
    hospital_id: Optional[str] = None
    department_id: Optional[str] = None
    name: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    designation: Optional[str] = None
    languages: Optional[List[str]] = None
    consultation_fee: Optional[float] = None
    availability: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None

class DoctorSearchRequest(BaseModel):
    query: Optional[str] = None
    department_id: Optional[str] = None
    specialization: Optional[str] = None
    hospital_id: Optional[str] = None
    city: Optional[str] = None
    min_rating: Optional[float] = None
    min_fee: Optional[float] = None
    max_fee: Optional[float] = None
    availability: Optional[str] = None
    limit: Optional[int] = 10
