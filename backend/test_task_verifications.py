import os
import sys
import uuid
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.auth.auth_handler import create_n8n_context_token, create_access_token
from app.database.supabase_client import SupabaseService
from app.config import settings

client = TestClient(app)

def run_task_verification_tests():
    print("=" * 75)
    print("RUNNING ALL TASK VERIFICATION TESTS")
    print("=" * 75)

    # ----------------------------------------------------
    # TASK 1: Telegram Context Resolution Endpoint
    # ----------------------------------------------------
    print("\n[Task 1] Testing POST /api/telegram/resolve-context...")
    
    # 1.1 New User Resolution (neither profiles nor telegram_accounts row exists)
    tg_id_1 = f"tg_new_{uuid.uuid4().hex[:6]}"
    res_1 = client.post("/api/telegram/resolve-context", json={"telegram_id": tg_id_1, "full_name": "John Telegram"})
    assert res_1.status_code == 200, f"Expected 200, got {res_1.status_code}: {res_1.text}"
    data_1 = res_1.json()
    assert "user_id" in data_1 and "n8n_token" in data_1 and "hospital_id" in data_1
    user_id_1 = data_1["user_id"]
    print(" -> SUCCESS: Created new profile & telegram_accounts row atomically, returned valid token & context!")

    # Verify DB records for 1.1
    tg_accs_1 = SupabaseService.get_records("telegram_accounts", {"telegram_id": tg_id_1})
    profiles_1 = SupabaseService.get_records("profiles", {"id": user_id_1})
    assert len(tg_accs_1) > 0 and len(profiles_1) > 0
    assert profiles_1[0].get("role") == "patient"
    print(" -> SUCCESS: Verified database records created cleanly for new Telegram patient!")

    # 1.2 Lookup via telegram_accounts
    res_1_repeat = client.post("/api/telegram/resolve-context", json={"telegram_id": tg_id_1})
    assert res_1_repeat.status_code == 200
    assert res_1_repeat.json()["user_id"] == user_id_1
    print(" -> SUCCESS: Resolved existing user_id from telegram_accounts lookup!")

    # 1.3 Fallback to profiles.telegram_id when no telegram_accounts row exists
    user_id_2 = str(uuid.uuid4())
    tg_id_2 = f"tg_legacy_{uuid.uuid4().hex[:6]}"
    SupabaseService.insert_record("profiles", {"id": user_id_2, "email": f"pat2_{user_id_2[:4]}@h.com", "role": "patient", "name": "Legacy Patient", "telegram_id": tg_id_2})
    
    res_2 = client.post("/api/telegram/resolve-context", json={"telegram_id": tg_id_2})
    assert res_2.status_code == 200
    assert res_2.json()["user_id"] == user_id_2
    # Verify missing telegram_accounts row was auto-created for sync
    tg_accs_2 = SupabaseService.get_records("telegram_accounts", {"telegram_id": tg_id_2})
    assert len(tg_accs_2) > 0
    assert tg_accs_2[0]["user_id"] == user_id_2
    print(" -> SUCCESS: Fallback to profiles.telegram_id worked and auto-synced telegram_accounts table!")

    # ----------------------------------------------------
    # TASK 2: N8nService send_web_chat qr_url Handling
    # ----------------------------------------------------
    print("\n[Task 2] Testing Chat Response Model with optional qr_url...")
    # Register/Login user for chat endpoint
    email_chat = f"chat_user_{uuid.uuid4().hex[:6]}@hospital.com"
    pwd_chat = "testpass123"
    reg_chat = client.post("/api/auth/register", json={"name": "Chat User", "email": email_chat, "password": pwd_chat}).json()
    chat_token = reg_chat["access_token"]
    
    res_chat = client.post(
        "/api/chat/send",
        json={"message": "Hello AI", "session_id": "sess_chat_1", "channel": "web"},
        headers={"Authorization": f"Bearer {chat_token}"}
    )
    assert res_chat.status_code == 200, f"Expected 200, got {res_chat.status_code}: {res_chat.text}"
    chat_data = res_chat.json()
    assert "message" in chat_data and "session_id" in chat_data and "user_id" in chat_data and "qr_url" in chat_data
    print(" -> SUCCESS: POST /api/chat/send returns schema forwarding qr_url field cleanly!")

    # ----------------------------------------------------
    # TASK 3: Booking Endpoint Token & 403 Verification
    # ----------------------------------------------------
    print("\n[Task 3] Testing X-N8n-Token Verification & 403 user_id Mismatch on /api/ai-tools/book-appointment...")

    doc_id = f"D_BOOK_{uuid.uuid4().hex[:6]}"
    doc_prof_id = str(uuid.uuid4())
    SupabaseService.insert_record("profiles", {"id": doc_prof_id, "email": f"doc_{doc_prof_id[:4]}@h.com", "role": "doctor", "name": "Dr. Bob"})
    SupabaseService.insert_record("doctors", {"id": doc_id, "profile_id": doc_prof_id, "hospital_id": "H001", "name": "Dr. Bob", "specialization": "Cardiology"})
    SupabaseService.insert_record("schedules", {"doctor_id": doc_id, "day_of_week": "Monday", "start_time": "10:00", "end_time": "11:00", "slot_duration_minutes": 30, "is_active": True})

    booking_payload = {
        "doctor_id": doc_id,
        "date": "2026-09-01",
        "start_time": "10:00",
        "end_time": "10:30",
        "notes": "Test booking"
    }

    # 3.1 Missing token -> 401
    res_no_tok = client.post("/api/ai-tools/book-appointment", json=booking_payload)
    assert res_no_tok.status_code == 401, f"Expected 401 for missing token, got {res_no_tok.status_code}"
    print(" -> SUCCESS: Missing X-N8n-Token rejected with 401 Unauthorized!")

    # 3.2 Invalid token -> 401
    res_inv_tok = client.post("/api/ai-tools/book-appointment", json=booking_payload, headers={"X-N8n-Token": "invalid.jwt.token"})
    assert res_inv_tok.status_code == 401, f"Expected 401 for invalid token, got {res_inv_tok.status_code}"
    print(" -> SUCCESS: Invalid X-N8n-Token rejected with 401 Unauthorized!")

    # 3.3 Body user_id mismatch -> 403 Forbidden
    valid_token_user_a = create_n8n_context_token(user_id=user_id_1, role="patient", hospital_id="H001")
    mismatch_payload = dict(booking_payload)
    mismatch_payload["user_id"] = user_id_2  # Different user_id from token's user_id_1

    res_403 = client.post("/api/ai-tools/book-appointment", json=mismatch_payload, headers={"X-N8n-Token": valid_token_user_a})
    assert res_403.status_code == 403, f"Expected 403 for user_id mismatch, got {res_403.status_code}: {res_403.text}"
    print(" -> SUCCESS: Token user_id vs payload user_id mismatch rejected with 403 Forbidden!")

    # 3.4 Valid matching token & payload -> 200 Success
    valid_payload = dict(booking_payload)
    valid_payload["user_id"] = user_id_1  # Matches token user_id

    res_200 = client.post("/api/ai-tools/book-appointment", json=valid_payload, headers={"X-N8n-Token": valid_token_user_a})
    assert res_200.status_code == 200, f"Expected 200 for valid booking, got {res_200.status_code}: {res_200.text}"
    print(" -> SUCCESS: Valid X-N8n-Token and matching payload successfully booked appointment!")

    print("\n" + "=" * 75)
    print("ALL TASK VERIFICATION TESTS PASSED 100% CLEANLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_task_verification_tests()
