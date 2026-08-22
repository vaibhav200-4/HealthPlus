import sys
import os
import uuid
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import hash_password, create_access_token, decode_access_token, get_doctor_user, get_admin_user
from app.schemas.user_schema import UserRegister, UserLogin
from app.api.auth import register_user, login_user
from app.api.doctors import get_my_doctor_profile, get_my_doctor_appointments, get_my_doctor_stats
from app.api.admin import get_admin_stats
from seed_data import seed
from fastapi import HTTPException
from test_utils import setup_strict_fallback_listener, assert_no_local_fallback

def test_portals_security():
    setup_strict_fallback_listener()
    print("=" * 70)
    print("RUNNING ROLE-BASED PORTALS & SECURITY VERIFICATION")
    print("=" * 70)

    # 1. Seed data idempotently
    print("\n[Step 1] Executing idempotent seed_data.py...")
    seed()
    print(" -> Seed complete!")

    # 2. Test Patient Auth & Role Isolation
    print("\n[Step 2] Testing Patient registration and authorization...")
    patient_email = f"patient_{uuid.uuid4().hex[:6]}@hospital.com"
    reg_res = register_user(UserRegister(
        name="John Patient",
        email=patient_email,
        password="patientpass123"
    ))
    patient_user = reg_res.user
    patient_token = reg_res.access_token
    assert patient_user.role in ["user", "patient"], f"Expected patient role, got {patient_user.role}"
    print(f" -> Registered Patient: {patient_email} (ID: {patient_user.id})")

    # Patient attempting Doctor endpoint -> Must fail with HTTP 403
    try:
        get_doctor_user(current_user={"id": patient_user.id, "email": patient_email, "role": patient_user.role})
        assert False, "Patient should not pass get_doctor_user!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f" -> SUCCESS: Patient rejected from Doctor endpoint with 403 ({e.detail})!")

    # Patient attempting Admin dependency -> Must fail with HTTP 403
    try:
        get_admin_user(current_user={"id": patient_user.id, "email": patient_email, "role": patient_user.role})
        assert False, "Patient should not pass get_admin_user!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f" -> SUCCESS: Patient rejected from Admin endpoint with 403 ({e.detail})!")

    # 3. Test Doctor Auth & Single-Doctor Data Isolation
    print("\n[Step 3] Testing Doctor Auth & Data Isolation (Dr. Arjun Mehta)...")
    arjun_login = login_user(UserLogin(email="arjun@hospital.com", password="doctor123"))
    arjun_user = arjun_login.user
    assert arjun_user.role == "doctor", f"Expected doctor role, got {arjun_user.role}"

    # Get Dr. Arjun's profile
    arjun_user_dict = {"id": arjun_user.id, "email": arjun_user.email, "role": arjun_user.role}
    doc_info = get_doctor_user(current_user=arjun_user_dict)
    assert doc_info["doctor"]["id"] == "D001", f"Expected D001 for Dr. Arjun, got {doc_info['doctor']['id']}"
    assert doc_info["doctor"]["name"] == "Dr. Arjun Mehta", f"Name mismatch: {doc_info['doctor']['name']}"
    print(f" -> SUCCESS: Logged in Dr. Arjun (Profile ID: {arjun_user.id} -> Doctor ID: D001)")

    # Doctor attempting Admin dependency -> Must fail with HTTP 403
    try:
        get_admin_user(current_user=arjun_user_dict)
        assert False, "Doctor should not pass get_admin_user!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print(f" -> SUCCESS: Doctor rejected from Admin endpoint with 403 ({e.detail})!")

    # 4. Cross-Doctor Access Security Test
    print("\n[Step 4] Testing Cross-Doctor Data Security...")
    # Dr. Arjun querying /api/doctors/me/appointments
    arjun_appointments = get_my_doctor_appointments(doctor_info=doc_info)
    for app in arjun_appointments:
        assert app.get("doctor_id") == "D001", f"Security failure! Found non-D001 appointment: {app}"
    print(f" -> SUCCESS: Dr. Arjun retrieved {len(arjun_appointments)} appointments strictly filtered to doctor_id='D001'!")

    # 5. Test Admin Master Auth
    print("\n[Step 5] Testing Admin Master Auth...")
    admin_login = login_user(UserLogin(email="admin@hospital.com", password="admin123"))
    admin_user = admin_login.user
    assert admin_user.role == "admin", f"Expected admin role, got {admin_user.role}"
    admin_user_dict = {"id": admin_user.id, "email": admin_user.email, "role": admin_user.role}
    admin_validated = get_admin_user(current_user=admin_user_dict)
    admin_stats = get_admin_stats(admin_user=admin_validated)
    assert "total_doctors" in admin_stats, "Admin stats missing total_doctors"
    print(f" -> SUCCESS: Admin logged in cleanly with ID: {admin_user.id} and retrieved hospital stats!")

    print("\n" + "=" * 70)
    print("ALL ROLE PORTALS & SECURITY VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    assert_no_local_fallback()

if __name__ == "__main__":
    test_portals_security()
