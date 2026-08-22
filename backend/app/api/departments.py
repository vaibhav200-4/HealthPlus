import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.schemas.department_schema import DepartmentBase, DepartmentCreate, DepartmentUpdate
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import get_admin_user

router = APIRouter(prefix="/api/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentBase])
def get_departments(hospital_id: Optional[str] = Query(None)):
    filters = {}
    if hospital_id:
        filters["hospital_id"] = hospital_id
    departments = SupabaseService.get_records("departments", filters if filters else None)
    return departments

@router.get("/{department_id}", response_model=DepartmentBase)
def get_department_by_id(department_id: str):
    dept = SupabaseService.get_record_by_id("departments", department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept

@router.post("", response_model=DepartmentBase)
def create_department(data: DepartmentCreate, admin_user: dict = Depends(get_admin_user)):
    dept_rec = {
        "id": str(uuid.uuid4()),
        "hospital_id": data.hospital_id,
        "name": data.name,
        "description": data.description or "",
        "status": data.status or "active"
    }
    created = SupabaseService.insert_record("departments", dept_rec)
    return created

@router.put("/{department_id}", response_model=DepartmentBase)
def update_department(department_id: str, data: DepartmentUpdate, admin_user: dict = Depends(get_admin_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = SupabaseService.update_record("departments", department_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Department not found")
    return updated

@router.delete("/{department_id}")
def delete_department(department_id: str, admin_user: dict = Depends(get_admin_user)):
    success = SupabaseService.delete_record("departments", department_id)
    return {"success": success}
