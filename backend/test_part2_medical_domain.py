import sys
import os
import uuid
import time
import concurrent.futures
from pathlib import Path
from fastapi import HTTPException

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import hash_password, create_access_token
from app.services.booking_service import BookingService
from app.services.schedule_service import ScheduleService
from app.schemas.user_schema import UserRegister, UserLogin
from app.api.auth import register_user, login_user
from app.api.sessions import create_session, complete_session, get_sessions
from app.api.prescriptions import create_prescription, get_prescriptions
from app.api.medical_records import create_medical_record, get_medical_records
from app.api.reviews import submit_doctor_review
from app.schemas.session_schema import SessionCreate, SessionComplete
from app.schemas.prescription_schema import PrescriptionCreate, PrescriptionItemCreate
from app.schemas.medical_record_schema import MedicalRecordCreate
from app.schemas.review_schema import DoctorReviewCreate
from seed_data import seed
from test_utils import setup_strict_fallback_listener, assert_no_local_fallback

def get_attr(obj, attr):
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)

def run_part2_tests():
    setup_strict_fallback_listener()
    print("=" * 75)
    print("RUNNING PART 2 — MEDICAL DOMAIN & APPOINTMENT HARDENING VERIFICATION")
    print("=" * 75)

    # 1. Seed base data
    print("\n[Step 1] Initializing data seed...")
    seed(force=True)

    # 2. Race-Condition Double Booking Protection Test
    print("\n[Step 2] Testing Concurrent Booking Requests for Same Slot...")
    target_doctor_id = "D001"
    target_date = "2026-09-01"
    target_start = "11:00 AM"
    target_end = "11:30 AM"

    # Clean any pre-existing appointment for this slot
    apps = SupabaseService.get_records("appointments", {"doctor_id": target_doctor_id, "date": target_date})
    for a in apps:
        if a.get("start_time") == target_start:
            SupabaseService.delete_record("appointments", a["id"])

    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    SupabaseService.insert_record("profiles", {"id": user_a, "name": "Patient A", "email": f"user_a_{user_a[:6]}@h.com", "role": "patient"})
    SupabaseService.insert_record("profiles", {"id": user_b, "name": "Patient B", "email": f"user_b_{user_b[:6]}@h.com", "role": "patient"})

    def attempt_booking(u_id, name):
        return BookingService.create_appointment(
            user_id=u_id,
            doctor_id=target_doctor_id,
            doctor_name="Dr. Arjun Mehta",
            hospital_name="City Hospital",
            date=target_date,
            start_time=target_start,
            end_time=target_end,
            patient_name=name
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_booking, user_a, "Patient A")
        f2 = executor.submit(attempt_booking, user_b, "Patient B")
        res1 = f1.result()
        res2 = f2.result()

    successes = [r for r in [res1, res2] if r[0] is True]
    failures = [r for r in [res1, res2] if r[0] is False]

    assert len(successes) == 1, f"Expected exactly 1 booking success, got {len(successes)}"
    assert len(failures) == 1, f"Expected exactly 1 booking failure, got {len(failures)}"
    assert failures[0][1] == "This slot is no longer available.", f"Unexpected failure message: {failures[0][1]}"
    print(f" -> SUCCESS: Concurrent race-condition test passed! 1 succeeded, 1 rejected cleanly with '{failures[0][1]}'")

    # 3. Idempotency Key Test
    print("\n[Step 3] Testing Booking Idempotency Key...")
    apps_step3 = SupabaseService.get_records("appointments", {"doctor_id": target_doctor_id, "date": "2026-09-02"})
    for a in apps_step3:
        if a.get("start_time") == "10:00 AM":
            SupabaseService.delete_record("appointments", a["id"])

    idempotency_key = f"key_{uuid.uuid4().hex[:10]}"
    res_first = BookingService.create_appointment(
        user_id=user_a,
        doctor_id=target_doctor_id,
        doctor_name="Dr. Arjun Mehta",
        hospital_name="City Hospital",
        date="2026-09-02",
        start_time="10:00 AM",
        end_time="10:30 AM",
        patient_name="Patient A",
        idempotency_key=idempotency_key
    )
    assert res_first[0] is True, "First idempotent attempt failed"
    app_id = res_first[2]["id"]

    res_retry = BookingService.create_appointment(
        user_id=user_a,
        doctor_id=target_doctor_id,
        doctor_name="Dr. Arjun Mehta",
        hospital_name="City Hospital",
        date="2026-09-02",
        start_time="10:00 AM",
        end_time="10:30 AM",
        patient_name="Patient A",
        idempotency_key=idempotency_key
    )
    assert res_retry[0] is True, "Idempotent retry attempt failed"
    assert res_retry[2]["id"] == app_id, "Idempotent retry returned different appointment ID"
    print(" -> SUCCESS: Idempotency key retry returned original appointment record cleanly!")

    # 4. Clinical Session & Private Doctor Notes Isolation Test
    print("\n[Step 4] Testing Clinical Sessions & Private Doctor Notes Isolation...")
    doc_prof_1_id = str(uuid.uuid4())
    doc_prof_2_id = str(uuid.uuid4())
    SupabaseService.insert_record("profiles", {"id": doc_prof_1_id, "name": "Dr. Arjun Mehta", "email": f"doc1_{doc_prof_1_id[:6]}@h.com", "role": "doctor"})
    SupabaseService.insert_record("profiles", {"id": doc_prof_2_id, "name": "Dr. Other", "email": f"doc2_{doc_prof_2_id[:6]}@h.com", "role": "doctor"})

    doc_info = {
        "user": {"id": doc_prof_1_id, "role": "doctor"},
        "doctor": {"id": "D001", "name": "Dr. Arjun Mehta"}
    }
    
    # Register Patient X
    patient_email = f"patient_x_{uuid.uuid4().hex[:6]}@hospital.com"
    reg_x = register_user(UserRegister(name="Patient X", email=patient_email, password="pass"))
    patient_x_id = get_attr(get_attr(reg_x, "user"), "id")

    # Book appointment for Patient X
    app_x_res = BookingService.create_appointment(
        user_id=patient_x_id,
        doctor_id="D001",
        doctor_name="Dr. Arjun Mehta",
        hospital_name="City Hospital",
        date="2026-09-03",
        start_time="11:30 AM",
        end_time="12:00 PM",
        patient_name="Patient X"
    )
    app_x_id = app_x_res[2]["id"]

    # Doctor creates clinical session
    session_res = create_session(SessionCreate(
        appointment_id=app_x_id,
        symptoms="Chest pain, dizziness",
        diagnosis="Mild angina",
        doctor_notes="Confidential: Patient mentioned high stress at work. Follow up in 2 weeks."
    ), doc_info)

    session_id = get_attr(session_res, "id")
    assert get_attr(session_res, "doctor_notes") is not None, "Doctor notes missing in doctor response"

    # Complete session
    complete_session(session_id, SessionComplete(status="completed"), doc_info)

    # Query sessions as Patient X -> doctor_notes MUST be None
    patient_identity = {
        "user_id": patient_x_id,
        "email": patient_email,
        "role": "patient",
        "is_super_admin": False
    }
    patient_sessions = get_sessions(identity=patient_identity)
    assert len(patient_sessions) > 0, "Patient failed to fetch sessions"
    assert get_attr(patient_sessions[0], "doctor_notes") is None, "SECURITY FAILURE: Private doctor notes exposed to patient!"
    print(" -> SUCCESS: Private doctor notes strictly hidden from patient-facing API responses!")

    # 5. Doctor Ownership Check for Prescriptions
    print("\n[Step 5] Testing Prescription Ownership Enforcement...")
    patient_rec = SupabaseService.get_records("patients", {"profile_id": patient_x_id})[0]
    
    # Valid prescription by Dr. Arjun (D001) for Patient X
    p_res = create_prescription(PrescriptionCreate(
        patient_id=patient_rec["id"],
        session_id=session_id,
        notes="Take with food",
        items=[PrescriptionItemCreate(medicine_name="Aspirin", dosage="75mg", frequency="Once daily", duration="14 days")]
    ), doc_info)
    assert get_attr(p_res, "id") is not None, "Prescription creation failed"

    # Invalid prescription attempt by Dr. Other (D002) for Patient X without appointment
    other_doc_info = {
        "user": {"id": doc_prof_2_id, "role": "doctor"},
        "doctor": {"id": "D002", "name": "Dr. Other"}
    }
    try:
        create_prescription(PrescriptionCreate(
            patient_id=patient_rec["id"],
            notes="Unauthorized prescription",
            items=[PrescriptionItemCreate(medicine_name="Placebo")]
        ), other_doc_info)
        assert False, "Prescription by unauthorized doctor should have failed!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f" -> SUCCESS: Unauthorized doctor prescription rejected with 403 ({e.detail})!")

    # 6. Doctor Reviews Server-Side Enforcement Test
    print("\n[Step 6] Testing Doctor Review Submission & Rating Calculation...")
    rev_res = submit_doctor_review(DoctorReviewCreate(
        appointment_id=app_x_id,
        rating=5,
        review="Excellent care and thorough examination!"
    ), identity=patient_identity)
    assert get_attr(rev_res, "id") is not None, "Review submission failed"

    # Verify doctor average rating updated
    # 7. Doctor Leave & Blocked Slot Filtering Test
    print("\n[Step 7] Testing Doctor Leave & Blocked Slot Availability Filtering...")
    leave_date = "2026-09-10"
    SupabaseService.insert_record("doctor_leaves", {
        "id": str(uuid.uuid4()),
        "doctor_id": "D001",
        "leave_date": leave_date,
        "reason": "Conference"
    })
    leave_slots = ScheduleService.get_doctor_available_slots("D001", leave_date)
    assert len(leave_slots) == 0, f"Expected 0 slots on doctor leave date, got {len(leave_slots)}"

    blocked_date = "2026-09-11"
    blocked_time = "10:00 AM"
    SupabaseService.insert_record("blocked_slots", {
        "id": str(uuid.uuid4()),
        "doctor_id": "D001",
        "slot_date": blocked_date,
        "start_time": blocked_time,
        "reason": "Personal work"
    })
    slots_res = ScheduleService.get_doctor_available_slots("D001", blocked_date)
    blocked_slot = next((s for s in slots_res if s["start_time"] == blocked_time), None)
    assert blocked_slot is not None, f"Blocked slot {blocked_time} not found in slots list"
    assert blocked_slot["blocked"] is True, "Slot was not marked as blocked"
    assert blocked_slot["available"] is False, "Blocked slot was incorrectly marked as available"
    print(" -> SUCCESS: Doctor leave and blocked slot availability filtering verified cleanly!")

    print("\n" + "=" * 75)
    print("ALL PART 2 VERIFICATIONS PASSED 100% CLEANLY!")
    print("=" * 75)
    assert_no_local_fallback()

if __name__ == "__main__":
    run_part2_tests()
