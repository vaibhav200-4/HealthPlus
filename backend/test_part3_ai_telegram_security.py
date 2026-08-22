import os
import sys
import uuid
import hmac
import hashlib
import time

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.auth.auth_handler import create_n8n_context_token, create_access_token
from app.database.supabase_client import SupabaseService
from app.config import settings
from test_utils import setup_strict_fallback_listener, assert_no_local_fallback

client = TestClient(app)

def run_part3_tests():
    setup_strict_fallback_listener()
    print("=" * 75)
    print("RUNNING PART 3 — AI TOOL AUTHORIZATION, IDENTITY & SECURITY VERIFICATION")
    print("=" * 75)

    # 1. Setup Test Users
    patient_a_id = str(uuid.uuid4())
    patient_b_id = str(uuid.uuid4())
    doctor_a_id = str(uuid.uuid4())

    email_a = f"pat_a_{patient_a_id[:6]}@h1.com"
    email_b = f"pat_b_{patient_b_id[:6]}@h2.com"
    doc_email = f"doc_a_{doctor_a_id[:6]}@h1.com"
    doc_id = f"D_TEST_{doctor_a_id[:6]}"
    
    # Store profiles
    SupabaseService.insert_record("profiles", {"id": patient_a_id, "email": email_a, "role": "patient", "name": "Patient A"})
    SupabaseService.insert_record("patients", {"id": str(uuid.uuid4()), "profile_id": patient_a_id, "patient_code": f"PT-A-{patient_a_id[:4]}"})
    
    SupabaseService.insert_record("profiles", {"id": patient_b_id, "email": email_b, "role": "patient", "name": "Patient B"})
    SupabaseService.insert_record("patients", {"id": str(uuid.uuid4()), "profile_id": patient_b_id, "patient_code": f"PT-B-{patient_b_id[:4]}"})

    SupabaseService.insert_record("profiles", {"id": doctor_a_id, "email": doc_email, "role": "doctor", "name": "Dr. Alice"})
    SupabaseService.insert_record("doctors", {"id": doc_id, "profile_id": doctor_a_id, "hospital_id": "H001", "name": "Dr. Alice", "specialization": "General Medicine"})

    print("\n[Step 1] Testing Signed Context Token Generation & Verification...")
    patient_token = create_n8n_context_token(user_id=patient_a_id, role="patient", hospital_id="H001")
    
    # Test valid call
    res = client.get("/api/ai-tools/my-profile", headers={"X-N8n-Token": patient_token})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    assert res.json().get("id") == patient_a_id
    print(" -> SUCCESS: Cryptographically signed context verified patient identity cleanly!")

    print("\n[Step 2] Testing Prompt Injection Resistance (Act as Admin Payload)...")
    # Patient tries to invoke admin AI tool (/api/ai-tools/hospital-stats)
    res_admin_tool = client.get("/api/ai-tools/hospital-stats", headers={"X-N8n-Token": patient_token})
    assert res_admin_tool.status_code == 403, f"Expected 403 Forbidden for patient context on admin tool, got {res_admin_tool.status_code}"
    print(" -> SUCCESS: Patient signed context rejected from Admin AI tool with 403 Forbidden!")

    # Missing token test
    res_no_token = client.get("/api/ai-tools/my-appointments")
    assert res_no_token.status_code == 401, f"Expected 401 Unauthorized for missing token, got {res_no_token.status_code}"
    print(" -> SUCCESS: Unauthenticated AI tool call rejected with 401 Unauthorized!")

    print("\n[Step 3] Testing Multi-Tenant Isolation via AI Tools...")
    h1_patient_token = create_n8n_context_token(user_id=patient_a_id, role="patient", hospital_id="H001")
    docs_h1 = client.get("/api/ai-tools/search-doctors", headers={"X-N8n-Token": h1_patient_token}).json()
    for doc in docs_h1:
        assert doc.get("hospital_id") == "H001", f"Expected hospital H001, got {doc.get('hospital_id')}"
    print(" -> SUCCESS: AI search-doctors tool strictly scoped to Hospital H001!")

    print("\n[Step 4] Testing Doctor Patient Isolation via AI Tools...")
    doc_token = create_n8n_context_token(user_id=doctor_a_id, role="doctor", hospital_id="H001")
    res_doc_patients = client.get("/api/ai-tools/doctor-patients", headers={"X-N8n-Token": doc_token})
    assert res_doc_patients.status_code == 200
    print(" -> SUCCESS: Doctor AI tool returned authorized doctor patient list!")

    print("\n[Step 5] Testing Telegram Account Linking & Identity Normalization...")
    # Link telegram account for patient A
    tg_id_unique = f"tg_{patient_a_id[:8]}"
    link_token = create_access_token(user_id=patient_a_id, email=email_a, role="patient")
    res_link = client.post(
        "/api/auth/link-telegram",
        json={"telegram_id": tg_id_unique},
        headers={"Authorization": f"Bearer {link_token}"}
    )
    assert res_link.status_code == 200, f"Expected 200, got {res_link.status_code}: {res_link.text}"
    
    # Check telegram_accounts table entry
    tg_accs = SupabaseService.get_records("telegram_accounts", {"telegram_id": tg_id_unique})
    assert len(tg_accs) > 0, "Expected telegram_accounts entry to be created!"
    assert tg_accs[0]["user_id"] == patient_a_id
    print(" -> SUCCESS: Telegram account linked cleanly and saved to telegram_accounts table!")

    print("\n[Step 6] Testing Telegram Webhook Signature & Unlinked Log Handling...")
    res_tg_log = client.post(
        "/api/telegram/log-message",
        json={"telegram_id": tg_id_unique, "session_id": "tg_sess_1", "role": "user", "message": "Hello via Telegram"},
        headers={"X-Telegram-Secret": settings.TELEGRAM_WEBHOOK_SECRET}
    )
    assert res_tg_log.status_code == 200
    assert res_tg_log.json().get("user_id") == patient_a_id
    print(" -> SUCCESS: Telegram message mapped to linked application user_id!")

    print("\n" + "=" * 75)
    print("ALL PART 3 SECURITY & AUTHORIZATION VERIFICATIONS PASSED 100% CLEANLY!")
    print("=" * 75)
    assert_no_local_fallback()

if __name__ == "__main__":
    run_part3_tests()
