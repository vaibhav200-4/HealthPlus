from pydantic import BaseModel
from typing import Optional

class DepartmentBase(BaseModel):
    id: str
    hospital_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DepartmentCreate(BaseModel):
    hospital_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
