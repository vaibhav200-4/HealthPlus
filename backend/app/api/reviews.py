import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.review_schema import DoctorReviewCreate, DoctorReviewResponse
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import require_patient_user, get_identity_context

router = APIRouter(prefix="/api/reviews", tags=["Doctor Reviews"])

def update_doctor_rating_stats(doctor_id: str):
    reviews = SupabaseService.get_records("doctor_reviews", {"doctor_id": doctor_id})
    if not reviews:
        return
    total_count = len(reviews)
    avg_rating = round(sum(r.get("rating", 5) for r in reviews) / total_count, 1)
    SupabaseService.update_record("doctors", doctor_id, {
        "rating": avg_rating,
        "total_reviews": total_count
    })

@router.post("", response_model=DoctorReviewResponse)
def submit_doctor_review(data: DoctorReviewCreate, identity: dict = Depends(require_patient_user)):
    user_id = identity["user_id"]
    
    # 1. Fetch appointment
    app = SupabaseService.get_record_by_id("appointments", data.appointment_id)
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # 2. Verify ownership
    if str(app.get("user_id")) != str(user_id) and identity["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Unauthorized: Appointment does not belong to this user")

    # 3. Server-side Enforcement: Review can only be submitted after completed appointment
    if app.get("status") != "completed":
        # Double-check if a completed session exists for appointment
        sessions = SupabaseService.get_records("sessions", {"appointment_id": data.appointment_id, "status": "completed"})
        if not sessions:
            raise HTTPException(status_code=400, detail="Reviews can only be submitted for completed appointments/sessions")

    doctor_id = app.get("doctor_id")
    pts = SupabaseService.get_records("patients", {"profile_id": user_id})
    patient_id = user_id

    # 4. Prevent duplicate review for same appointment
    existing = SupabaseService.get_records("doctor_reviews", {"appointment_id": data.appointment_id})
    if existing:
        raise HTTPException(status_code=400, detail="A review has already been submitted for this appointment")

    rev_id = str(uuid.uuid4())
    rev_rec = {
        "id": rev_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_id": data.appointment_id,
        "rating": data.rating,
        "review": data.review or ""
    }

    created = SupabaseService.insert_record("doctor_reviews", rev_rec)
    update_doctor_rating_stats(doctor_id)

    patient_code = pts[0].get("patient_code") if pts else None
    return DoctorReviewResponse(
        id=rev_id,
        patient_id=patient_id,
        patient_code=patient_code,
        doctor_id=doctor_id,
        appointment_id=data.appointment_id,
        rating=data.rating,
        review=data.review,
        created_at=created.get("created_at")
    )

@router.get("/doctor/{doctor_id}", response_model=List[DoctorReviewResponse])
def get_doctor_reviews(doctor_id: str):
    reviews = SupabaseService.get_records("doctor_reviews", {"doctor_id": doctor_id})
    res = []
    for r in reviews:
        p_rec = SupabaseService.get_record_by_id("patients", r.get("patient_id"))
        res.append(DoctorReviewResponse(
            id=r["id"],
            patient_id=r["patient_id"],
            patient_code=p_rec.get("patient_code") if p_rec else None,
            doctor_id=r["doctor_id"],
            appointment_id=r["appointment_id"],
            rating=r.get("rating", 5),
            review=r.get("review"),
            created_at=r.get("created_at")
        ))
    return res
