# backend/app/DoctorBase
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.doctor_schema import DoctorBase, DoctorSearchRequest
from app.database.supabase_client import SupabaseService
from app.services.pinecone_service import PineconeService

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

@router.get("", response_model=List[DoctorBase])
def get_all_doctors(
    specialization: Optional[str] = Query(None),
    hospital_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    doctors = SupabaseService.get_records("doctors")
    if specialization:
        doctors = [d for d in doctors if d.get("specialization", "").lower() == specialization.lower()]
    if hospital_id:
        doctors = [d for d in doctors if d.get("hospital_id") == hospital_id]
    if search:
        s_lower = search.lower()
        doctors = [
            d for d in doctors 
            if s_lower in d.get("name", "").lower() 
            or s_lower in d.get("specialization", "").lower()
            or s_lower in d.get("designation", "").lower()
        ]
    return doctors

@router.get("/{doctor_id}", response_model=DoctorBase)
def get_doctor_by_id(doctor_id: str):
    doctor = SupabaseService.get_record_by_id("doctors", doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.post("/search")
def search_doctors_vector(req: DoctorSearchRequest):
    """
    Semantic vector search across doctors and hospitals using Pinecone & Gemini.
    """
    vector_results = PineconeService.search_doctors(query=req.query, top_k=req.limit)
    return {"query": req.query, "results": vector_results}
