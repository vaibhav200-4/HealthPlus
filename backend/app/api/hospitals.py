# backend/app/hospital.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.hospital_schema import HospitalBase
from app.database.supabase_client import SupabaseService

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])

@router.get("", response_model=List[HospitalBase])
def get_all_hospitals():
    return SupabaseService.get_records("hospitals")

@router.get("/{hospital_id}", response_model=HospitalBase)
def get_hospital_by_id(hospital_id: str):
    h = SupabaseService.get_record_by_id("hospitals", hospital_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return h
