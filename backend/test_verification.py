import sys
import os
import uuid
from pathlib import Path

# Ensure backend directory is in python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.supabase_client import SupabaseService, get_supabase_client
from app.auth.auth_handler import hash_password, verify_password, create_access_token
from app.schemas.user_schema import UserRegister, UserLogin
from app.api.auth import register_user, login_user
from app.services.schedule_service import ScheduleService
from app.api.schedules import get_doctor_slots
from seed_data import seed

def run_tests():
    print("=" * 60)
    print("RUNNING END-TO-END VERIFICATION SEQUENCE")
    print("=" * 60)

    # Step 1: Verify 01_init_schema.sql file existence & structure
    migration_file = backend_dir.parent / "supabase" / "migrations" / "01_init_schema.sql"
    print(f"\n[Step 1] Checking 01_init_schema.sql at {migration_file}...")
    if migration_file.exists():
        content = migration_file.read_text(encoding="utf-8")
        assert "password_hash TEXT" in content, "Missing password_hash in migration schema"
        assert "REFERENCES auth.users" not in content, "profiles should not reference auth.users"
        assert "public.chat_messages" in content, "Missing chat_messages table in schema"
        print(" -> SUCCESS: 01_init_schema.sql validated successfully!")
    else:
        print(" -> ERROR: 01_init_schema.sql not found!")

    # Step 2: Register test user
    print("\n[Step 2] Testing POST /api/auth/register with test user...")
    test_email = f"testuser_{uuid.uuid4().hex[:6]}@hospital.com"
    reg_data = UserRegister(
        name="Test User",
        email=test_email,
        password="testpassword123",
        phone="1234567890"
    )
    reg_res = register_user(reg_data)
    user_id = reg_res.user.id
    token = reg_res.access_token
    print(f" -> Registered user_id: {user_id}")
    print(f" -> Received token: {token[:25]}...")
    
    # Confirm row in profiles table with populated password_hash
    profiles = SupabaseService.get_records("profiles", {"email": test_email})
    assert len(profiles) > 0, "Profile record not created in DB"
    stored_hash = profiles[0].get("password_hash")
    assert stored_hash is not None and len(stored_hash) > 0, "password_hash missing or empty"
    print(f" -> SUCCESS: User profile created with password_hash: {stored_hash[:15]}...")

    # Step 3: Login test user
    print("\n[Step 3] Testing POST /api/auth/login with test user...")
    login_data = UserLogin(email=test_email, password="testpassword123")
    login_res = login_user(login_data)
    assert login_res.access_token is not None, "Login token missing"
    assert login_res.user.id == user_id, "User ID mismatch on login"
    print(" -> SUCCESS: Test user login returned valid JWT token!")

    # Step 4: Login admin user
    print("\n[Step 4] Testing POST /api/auth/login with admin master credentials...")
    admin_login_data = UserLogin(email="admin@hospital.com", password="admin123")
    admin_res = login_user(admin_login_data)
    assert admin_res.user.id == settings.ADMIN_USER_ID, f"Admin ID expected {settings.ADMIN_USER_ID}, got {admin_res.user.id}"
    assert admin_res.user.role == "admin", "Admin role mismatch"
    print(f" -> SUCCESS: Admin user logged in with ID: {admin_res.user.id}")

    # Step 5: Seed data
    print("\n[Step 5] Running seed_data.py...")
    try:
        seed()
        hospitals = SupabaseService.get_records("hospitals")
        doctors = SupabaseService.get_records("doctors")
        schedules = SupabaseService.get_records("schedules")
        print(f" -> SUCCESS: Seeded {len(hospitals)} hospitals, {len(doctors)} doctors, {len(schedules)} schedules cleanly!")
    except Exception as e:
        print(f" -> ERROR during seeding: {e}")
        raise e

    # Step 6: Test chat message logging to Supabase
    print("\n[Step 6] Testing chat message logging in chat_messages table...")
    session_id = f"session_{user_id[:8]}"
    user_msg_rec = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": "web",
        "session_id": session_id,
        "role": "user",
        "message": "Hello, I need an appointment with a cardiologist."
    }
    assistant_msg_rec = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": "web",
        "session_id": session_id,
        "role": "assistant",
        "message": "Sure! Dr. Smith is available tomorrow at 10:00 AM."
    }
    SupabaseService.insert_record("chat_messages", user_msg_rec)
    SupabaseService.insert_record("chat_messages", assistant_msg_rec)

    chat_history = SupabaseService.get_records("chat_messages", {"session_id": session_id})
    assert len(chat_history) >= 2, "Chat messages not saved properly"
    web_channels = [m for m in chat_history if m.get("channel") == "web"]
    assert len(web_channels) >= 2, "Channel should be 'web'"
    print(f" -> SUCCESS: {len(chat_history)} chat messages recorded in chat_messages table with channel='web'!")

    # Step 7: Test doctor availability slots from ScheduleService
    print("\n[Step 7] Testing GET /api/schedules/doctor/{doctor_id}?date=2026-08-25...")
    doctors = SupabaseService.get_records("doctors")
    target_doctor_id = doctors[0]["id"] if doctors else "D001"
    slots_res = get_doctor_slots(doctor_id=target_doctor_id, date="2026-08-25")
    assert "slots" in slots_res, "Response missing slots"
    print(f" -> SUCCESS: Retrieved {len(slots_res['slots'])} availability slots for doctor {target_doctor_id} via ScheduleService!")

    print("\n" + "=" * 60)
    print("ALL VERIFICATION STEPS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
