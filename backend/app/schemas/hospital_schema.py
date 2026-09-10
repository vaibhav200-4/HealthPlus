from pydantic import BaseModel, field_validator
from typing import List, Optional

class HospitalBase(BaseModel):
    id: str
    hospital_name: str
    street: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    phone: Optional[str] = None
    email: Optional[str] = None
    departments: List[str] = []

    @field_validator('departments', mode='before')
    @classmethod
    def normalize_departments(cls, v):
        if v is None:
            return []
        return v

class HospitalCreate(HospitalBase):
    pass

class HospitalUpdate(BaseModel):
    hospital_name: Optional[str] = None
    street: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    departments: Optional[List[str]] = None
