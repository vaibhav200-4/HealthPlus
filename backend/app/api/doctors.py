from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import date
from app.schemas.doctor_schema import DoctorBase, DoctorSearchRequest
from app.database.supabase_client import SupabaseService
from app.services.pinecone_service import PineconeService
from app.auth.auth_handler import get_doctor_user

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

@router.get("/me")
def get_my_doctor_profile(doctor_info: dict = Depends(get_doctor_user)):
    return doctor_info

@router.get("/me/appointments")
def get_my_doctor_appointments(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    return appointments

@router.get("/me/schedule")
def get_my_doctor_schedule(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    schedules = SupabaseService.get_records("schedules", {"doctor_id": doc_id})
    return schedules

@router.get("/me/patients")
def get_my_doctor_patients(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    seen_users = {}
    for app in appointments:
        uid = app.get("user_id")
        if uid and uid not in seen_users:
            patient_code = None
            p_id = None
            try:
                pts = SupabaseService.get_records("patients", {"profile_id": uid})
                if pts:
                    patient_code = pts[0].get("patient_code")
                    p_id = pts[0].get("id")
            except Exception:
                pass

            seen_users[uid] = {
                "patient_id": p_id or uid,
                "user_id": uid,
                "patient_code": patient_code or f"PT-REF{str(uid)[:6]}",
                "patient_name": app.get("patient_name"),
                "patient_email": app.get("patient_email"),
                "patient_phone": app.get("patient_phone"),
                "last_appointment_date": app.get("date"),
                "total_appointments": len([a for a in appointments if a.get("user_id") == uid])
            }
    return list(seen_users.values())

@router.get("/patients/{patient_id}/profile")
@router.get("/me/patients/{patient_id}")
def get_doctor_patient_profile(patient_id: str, doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    
    patient_rec = SupabaseService.get_record_by_id("patients", patient_id)
    profile_id = None
    real_patient_id = patient_id

    if patient_rec:
        profile_id = patient_rec.get("profile_id")
        real_patient_id = patient_rec.get("id")
    else:
        pts = SupabaseService.get_records("patients", {"profile_id": patient_id})
        if pts:
            patient_rec = pts[0]
            profile_id = patient_id
            real_patient_id = patient_rec["id"]
        else:
            profile_id = patient_id

    profile_rec = SupabaseService.get_record_by_id("profiles", profile_id) if profile_id else None

    all_doc_appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    patient_appointments = [
        a for a in all_doc_appointments 
        if (profile_id and a.get("user_id") == profile_id) or (a.get("user_id") == patient_id)
    ]

    p_name = profile_rec.get("name") if profile_rec else None
    p_email = profile_rec.get("email") if profile_rec else None
    p_phone = profile_rec.get("phone") if profile_rec else None

    if patient_appointments:
        if not p_name:
            p_name = patient_appointments[0].get("patient_name")
        if not p_email:
            p_email = patient_appointments[0].get("patient_email")
        if not p_phone:
            p_phone = patient_appointments[0].get("patient_phone")

    return {
        "patient_id": real_patient_id,
        "profile_id": profile_id or real_patient_id,
        "patient_code": patient_rec.get("patient_code") if patient_rec else f"PT-REF{str(real_patient_id)[:6]}",
        "name": p_name or "Patient",
        "email": p_email or "No email provided",
        "phone": p_phone or "No phone provided",
        "gender": patient_rec.get("gender") if patient_rec else None,
        "blood_group": patient_rec.get("blood_group") if patient_rec else None,
        "date_of_birth": patient_rec.get("date_of_birth") if patient_rec else None,
        "address": patient_rec.get("address") if patient_rec else None,
        "emergency_contact": patient_rec.get("emergency_contact") if patient_rec else None,
        "consultation_count": len(patient_appointments),
        "appointments": patient_appointments
    }

@router.get("/me/stats")
def get_my_doctor_stats(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    today_str = str(date.today())
    
    today_apps = [a for a in appointments if str(a.get("date")) == today_str]
    upcoming_apps = [a for a in appointments if a.get("status") in ["confirmed", "pending"]]
    completed_apps = [a for a in appointments if a.get("status") == "completed"]
    cancelled_apps = [a for a in appointments if a.get("status") == "cancelled"]
    unique_patients = len({a.get("user_id") for a in appointments if a.get("user_id")})

    return {
        "doctor": doctor_info["doctor"],
        "total_appointments": len(appointments),
        "today_appointments_count": len(today_apps),
        "upcoming_appointments_count": len(upcoming_apps),
        "completed_appointments_count": len(completed_apps),
        "cancelled_appointments_count": len(cancelled_apps),
        "total_patients_count": unique_patients
    }

@router.get("", response_model=List[DoctorBase])
def get_all_doctors(
    specialization: Optional[str] = Query(None),
    hospital_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    min_fee: Optional[float] = Query(None),
    max_fee: Optional[float] = Query(None),
    availability: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    doctors = SupabaseService.get_records("doctors")
    hospitals = {h["id"]: h for h in SupabaseService.get_records("hospitals")}
    departments = {d["id"]: d for d in SupabaseService.get_records("departments")}

    for d in doctors:
        dept_id = d.get("department_id")
        if dept_id and dept_id in departments:
            d["department_name"] = departments[dept_id].get("name")
        if d.get("languages") is None:
            d["languages"] = ["English", "Hindi"]
        if d.get("rating") is None:
            d["rating"] = 5.0
        if d.get("consultation_fee") is None:
            d["consultation_fee"] = 0.0
        if d.get("experience_years") is None:
            d["experience_years"] = 0
        if d.get("total_reviews") is None:
            d["total_reviews"] = 0

    if specialization:
        doctors = [d for d in doctors if d.get("specialization", "").lower() == specialization.lower()]
    if hospital_id:
        doctors = [d for d in doctors if d.get("hospital_id") == hospital_id]
    if department_id:
        doctors = [d for d in doctors if d.get("department_id") == department_id]
    if city:
        doctors = [
            d for d in doctors 
            if hospitals.get(d.get("hospital_id"), {}).get("city", "").lower() == city.lower()
        ]
    if min_rating is not None:
        doctors = [d for d in doctors if float(d.get("rating", 5.0)) >= min_rating]
    if min_fee is not None:
        doctors = [d for d in doctors if float(d.get("consultation_fee", 0)) >= min_fee]
    if max_fee is not None:
        doctors = [d for d in doctors if float(d.get("consultation_fee", 0)) <= max_fee]
    if availability:
        doctors = [d for d in doctors if availability.lower() in d.get("availability", "").lower()]
    if search:
        s_lower = search.lower()
        doctors = [
            d for d in doctors 
            if s_lower in d.get("name", "").lower() 
            or s_lower in d.get("specialization", "").lower()
            or s_lower in d.get("designation", "").lower()
            or s_lower in d.get("department_name", "").lower()
        ]
    return doctors

@router.get("/{doctor_id}", response_model=DoctorBase)
def get_doctor_by_id(doctor_id: str):
    doctor = SupabaseService.get_record_by_id("doctors", doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if doctor.get("department_id"):
        dept = SupabaseService.get_record_by_id("departments", doctor["department_id"])
        if dept:
            doctor["department_name"] = dept.get("name")
    return doctor

@router.post("/search")
def search_doctors_vector(req: DoctorSearchRequest):
    if req.query:
        vector_results = PineconeService.search_doctors(query=req.query, top_k=req.limit or 10)
    else:
        vector_results = []

    if vector_results:
        filtered = vector_results
        if req.department_id:
            filtered = [r for r in filtered if r.get("department_id") == req.department_id]
        if req.specialization:
            filtered = [r for r in filtered if req.specialization.lower() in r.get("specialization", "").lower()]
        if req.hospital_id:
            filtered = [r for r in filtered if r.get("hospital_id") == req.hospital_id]
        if req.city:
            filtered = [r for r in filtered if req.city.lower() in r.get("city", "").lower()]
        if req.min_rating is not None:
            filtered = [r for r in filtered if float(r.get("rating", 5.0)) >= req.min_rating]
        if req.min_fee is not None:
            filtered = [r for r in filtered if float(r.get("consultation_fee", 0)) >= req.min_fee]
        if req.max_fee is not None:
            filtered = [r for r in filtered if float(r.get("consultation_fee", 0)) <= req.max_fee]
        return {"query": req.query, "results": filtered}

    db_docs = get_all_doctors(
        specialization=req.specialization,
        hospital_id=req.hospital_id,
        department_id=req.department_id,
        city=req.city,
        min_rating=req.min_rating,
        min_fee=req.min_fee,
        max_fee=req.max_fee,
        availability=req.availability,
        search=req.query
    )
    return {"query": req.query, "results": db_docs}
