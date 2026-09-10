import sys
import os
import uuid

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import hash_password, create_access_token
from app.schemas.user_schema import UserLogin, HospitalAdminCreate
from app.api.auth import login_user
from app.api.admin import create_or_update_hospital_admin, get_hospital_admin_credentials
from app.api.hospital_admin import get_hospital_admin_stats
from app.config import settings

def test_hospital_admin_flow():
    print("==========================================")
    print("TEST: Hospital Admin End-to-End Auth Flow")
    print("==========================================")

    # 1. Setup Test Hospital
    hospital_id = f"H_TEST_{uuid.uuid4().hex[:6].upper()}"
    hosp_data = {
        "id": hospital_id,
        "hospital_name": f"Test General Hospital {hospital_id}",
        "city": "Mumbai",
        "state": "Maharashtra",
        "status": "active"
    }
    SupabaseService.insert_record("hospitals", hosp_data)
    print(f"[Step 1] Created test hospital: {hospital_id}")

    # 2. System Admin Context
    admin_context = {
        "id": settings.ADMIN_USER_ID,
        "email": "admin@hospital.com",
        "role": "admin"
    }

    # 3. Create Hospital Admin Credentials
    admin_email = f"hadmin_{uuid.uuid4().hex[:6]}@test.com"
    admin_pwd = "HospitalAdminPass123!"
    create_payload = HospitalAdminCreate(
        email=admin_email,
        password=admin_pwd,
        name="Dr. Test Hospital Admin"
    )

    print(f"[Step 2] Creating Hospital Admin account for email: {admin_email}...")
    res_create = create_or_update_hospital_admin(
        hospital_id=hospital_id,
        data=create_payload,
        admin_user=admin_context
    )
    print(f" -> Create API response: {res_create}")
    assert res_create.get("success") is True, "Hospital Admin creation failed"

    # 4. Verify DB Persistence in profiles table
    print("\n[Step 3] Verifying database persistence in 'profiles' table...")
    profiles = SupabaseService.get_records("profiles", {"email": admin_email})
    assert len(profiles) > 0, "Hospital Admin profile not found in 'profiles' DB table!"
    p_rec = profiles[0]
    print(f" -> Profile DB Record: id={p_rec['id']}, role={p_rec.get('role')}, hospital_id={p_rec.get('hospital_id')}")
    assert p_rec.get("role") == "hospital_admin", f"Expected role 'hospital_admin', got '{p_rec.get('role')}'"
    assert p_rec.get("hospital_id") == hospital_id, f"Expected hospital_id '{hospital_id}', got '{p_rec.get('hospital_id')}'"
    print("[OK] Database persistence verified cleanly!")

    # 5. Test Credentials Inspection Endpoint
    print("\n[Step 4] Testing GET /api/admin/hospitals/{hospital_id}/admin-credentials...")
    res_creds = get_hospital_admin_credentials(hospital_id=hospital_id, admin_user=admin_context)
    has_adm = res_creds.get("has_admin") if isinstance(res_creds, dict) else res_creds.has_admin
    adm_usr = res_creds.get("admin_user") if isinstance(res_creds, dict) else res_creds.admin_user
    assert has_adm is True, "Credentials check returned has_admin=False"
    assert (adm_usr.get("email") if isinstance(adm_usr, dict) else adm_usr.email) == admin_email
    print("[OK] Admin credentials inspection endpoint verified!")

    # 6. Test Hospital Admin Login Flow
    print("\n[Step 5] Testing POST /api/auth/login with new Hospital Admin credentials...")
    login_payload = UserLogin(email=admin_email, password=admin_pwd)
    auth_res = login_user(data=login_payload)
    print(f" -> Login token received: {auth_res.access_token[:25]}...")
    print(f" -> Authenticated User: id={auth_res.user.id}, role={auth_res.user.role}, hospital_id={auth_res.user.hospital_id}")
    
    assert auth_res.user.role == "hospital_admin", f"Expected user.role 'hospital_admin', got '{auth_res.user.role}'"
    assert auth_res.user.hospital_id == hospital_id, f"Expected user.hospital_id '{hospital_id}', got '{auth_res.user.hospital_id}'"
    print("[OK] Hospital Admin authentication & JWT token generation verified!")

    # 7. Test Hospital Admin Scoped Dashboard API
    print("\n[Step 6] Testing GET /api/hospital-admin/stats with Hospital Admin token...")
    hadmin_user_context = {
        "id": auth_res.user.id,
        "email": admin_email,
        "role": "hospital_admin",
        "hospital_id": hospital_id
    }
    stats_res = get_hospital_admin_stats(admin_user=hadmin_user_context)
    print(f" -> Hospital Admin Stats Response: {stats_res}")
    assert "total_doctors" in stats_res or "doctors_count" in stats_res, "Stats response missing doctor count"
    print("[OK] Hospital Admin scoped dashboard access verified!")

    print("\n==========================================")
    print("ALL HOSPITAL ADMIN FLOW TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    test_hospital_admin_flow()
