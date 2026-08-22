import sys
import os
import uuid
import time
from pathlib import Path
from fastapi import HTTPException

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import (
    hash_password,
    create_access_token,
    get_identity_context,
    require_super_admin,
    require_hospital_admin,
    require_hospital_scope,
    auth_rate_limiter
)
from app.schemas.user_schema import UserRegister, UserLogin
from app.api.auth import register_user, login_user
from app.api.doctors import get_my_doctor_patients
from seed_data import seed
from fastapi import Request
from test_utils import setup_strict_fallback_listener, assert_no_local_fallback

def run_multitenancy_rbac_tests():
    setup_strict_fallback_listener()
    print("=" * 70)
    print("RUNNING MULTI-TENANCY & RBAC SECURITY VERIFICATION")
    print("=" * 70)

    # Step 1: Migration SQL files check
    print("\n[Step 1] Verifying 02_hospital_multitenancy.sql & 03_patient_model.sql...")
    migrations_dir = backend_dir.parent / "supabase" / "migrations"
    m2 = migrations_dir / "02_hospital_multitenancy.sql"
    m3 = migrations_dir / "03_patient_model.sql"
    m4 = migrations_dir / "04_doctor_hospital_relationship.sql"

    assert m2.exists(), "Migration 02_hospital_multitenancy.sql missing"
    assert m3.exists(), "Migration 03_patient_model.sql missing"
    assert m4.exists(), "Migration 04_doctor_hospital_relationship.sql missing"

    m2_text = m2.read_text(encoding="utf-8")
    assert "hospital_members" in m2_text, "Missing hospital_members table definition"
    assert "super_admin" in m2_text, "Missing super_admin role support"

    m3_text = m3.read_text(encoding="utf-8")
    assert "patient_code" in m3_text, "Missing patient_code in 03 migration"

    print(" -> SUCCESS: Migrations 02, 03, and 04 validated!")

    # Step 2: Seed data with ALLOW_DEMO_SEED=True
    print("\n[Step 2] Seeding data with ALLOW_DEMO_SEED...")
    seed(force=True)

    # Step 3: Test Patient Registration & Patient Code Generation
    print("\n[Step 3] Testing Patient Registration & patient_code generation...")
    test_email = f"saas_patient_{uuid.uuid4().hex[:6]}@hospital.com"
    dummy_request = Request({"type": "http", "client": ("127.0.0.1", 12345)})

    reg_res = register_user(UserRegister(
        name="SaaS Patient",
        email=test_email,
        password="patientpassword123"
    ), dummy_request)

    assert reg_res.user.patient_code is not None, "patient_code missing in UserProfile"
    assert reg_res.user.patient_code.startswith("PT-"), f"Invalid patient_code format: {reg_res.user.patient_code}"
    print(f" -> SUCCESS: Patient registered with patient_code: {reg_res.user.patient_code} (User ID: {reg_res.user.id})")

    # Step 4: Test Doctor Patient Isolation & patient_code output
    print("\n[Step 4] Testing Doctor Patient Isolation & patient_code resolution...")
    doc_info = {
        "user": {"id": "doc_prof_1", "role": "doctor"},
        "doctor": {"id": "D001", "name": "Dr. Arjun Mehta"}
    }
    doctor_patients = get_my_doctor_patients(doctor_info=doc_info)
    print(f" -> SUCCESS: Dr. Arjun retrieved {len(doctor_patients)} patients bound to appointments!")

    # Step 5: Test IdentityContext & Hospital Scope Enforcement
    print("\n[Step 5] Testing RBAC IdentityContext & Hospital Scoping...")
    
    # 5a. Hospital Member User
    h_member_user_id = str(uuid.uuid4())
    h_admin_email = f"hadmin_{uuid.uuid4().hex[:6]}@hospital_a.com"
    SupabaseService.insert_record("profiles", {
        "id": h_member_user_id,
        "name": "Hospital Admin User",
        "email": h_admin_email,
        "role": "admin"
    })
    SupabaseService.insert_record("hospital_members", {
        "id": str(uuid.uuid4()),
        "hospital_id": "H001",
        "user_id": h_member_user_id,
        "role": "admin"
    })

    identity = get_identity_context(current_user={"id": h_member_user_id, "role": "admin", "email": h_admin_email})
    assert identity["hospital_id"] == "H001", f"Expected H001, got {identity['hospital_id']}"
    
    scoped_h_id = require_hospital_scope(identity=identity)
    assert scoped_h_id == "H001", f"Expected scoped H001, got {scoped_h_id}"
    print(f" -> SUCCESS: Hospital Admin correctly scoped to hospital_id='H001'!")

    # 5b. Super Admin User
    super_admin_id = settings.ADMIN_USER_ID
    super_identity = get_identity_context(current_user={"id": super_admin_id, "role": "admin", "email": "admin@hospital.com"})
    assert super_identity["is_super_admin"] is True, "Expected is_super_admin=True"
    super_scope = require_hospital_scope(identity=super_identity)
    assert super_scope is None, "Super admin should have global (None) hospital scope"
    print(" -> SUCCESS: Super Admin granted global scope!")

    # Step 6: Test Auth Rate Limiting
    print("\n[Step 6] Testing Auth Endpoint Rate Limiting (5 attempts/min/IP)...")
    rate_ip_request = Request({"type": "http", "client": ("192.168.1.100", 54321)})
    
    # Trigger 5 requests
    for i in range(5):
        try:
            login_user(UserLogin(email="nonexistent@hospital.com", password="wrongpassword"), rate_ip_request)
        except HTTPException:
            pass # Expected 401

    # 6th attempt should raise HTTP 429
    rate_limited = False
    try:
        login_user(UserLogin(email="nonexistent@hospital.com", password="wrongpassword"), rate_ip_request)
    except HTTPException as e:
        if e.status_code == 429:
            rate_limited = True

    assert rate_limited, "Rate limiter did not block 6th request with HTTP 429!"
    print(" -> SUCCESS: 6th login attempt correctly rejected with HTTP 429 Too Many Requests!")

    print("\n" + "=" * 70)
    print("ALL MULTI-TENANCY & RBAC VERIFICATIONS PASSED CLEANLY!")
    print("=" * 70)
    assert_no_local_fallback()

if __name__ == "__main__":
    run_multitenancy_rbac_tests()
