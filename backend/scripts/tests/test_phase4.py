import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import create_access_token

def test_phase4():
    print("--- Phase 4 Acceptance Test ---")
    settings.LLM_PROVIDER = "gemini"
    client = TestClient(app)

    # 1. Ensure test profile & doctor exist
    profs = SupabaseService.get_records("profiles")
    if profs:
        test_user_id = profs[0]["id"]
        test_email = profs[0].get("email", "patient@test.com")
        test_role = profs[0].get("role", "patient")
    else:
        test_user_id = str(uuid.uuid4())
        test_email = "patient_p4@test.com"
        test_role = "patient"
        SupabaseService.insert_record("profiles", {
            "id": test_user_id,
            "email": test_email,
            "name": "Phase4 Patient",
            "role": test_role
        })

    token = create_access_token(test_user_id, test_email, test_role)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = f"sess_p4_{uuid.uuid4().hex[:6]}"

    # Fetch or seed a doctor for cardiologist testing
    docs = SupabaseService.get_records("doctors")
    if not docs:
        doc_id = str(uuid.uuid4())
        SupabaseService.insert_record("doctors", {
            "id": doc_id,
            "name": "Dr. Sarah Jenkins",
            "specialty": "Cardiology",
            "hospital_id": "H001",
            "department_id": "D001"
        })
    else:
        doc_id = docs[0]["id"]

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Step A: "I want to see a cardiologist"
    print("Sending message 1: 'I want to see a cardiologist'...")
    res1 = client.post(
        "/api/chat/send",
        json={"message": "I want to see a cardiologist", "session_id": session_id},
        headers=headers
    )
    assert res1.status_code == 200

    # Step B: Direct booking request with doctor, date, and slot
    print(f"Sending booking request for doctor {doc_id} on {tomorrow} at 10:00 AM...")
    booking_msg = f"Please book an appointment with doctor ID {doc_id} on date {tomorrow} from 10:00 AM to 10:30 AM. user_id is {test_user_id}."
    res2 = client.post(
        "/api/chat/send",
        json={"message": booking_msg, "session_id": session_id},
        headers=headers
    )
    assert res2.status_code == 200

    # Verify appointment in DB
    apps = SupabaseService.get_records("appointments", {"user_id": test_user_id, "doctor_id": doc_id, "date": tomorrow})
    assert len(apps) > 0, "Appointment record was not created in appointments table!"
    app_rec = apps[0]
    assert app_rec.get("idempotency_key"), "Idempotency key is missing on booked appointment!"
    idempotency_key = app_rec["idempotency_key"]
    print(f"Appointment created successfully: id={app_rec['id']}, idempotency_key={idempotency_key}")

    # Step C: Re-send identical booking request with same session_id -> verify no duplicate created
    print("Re-posting identical booking sequence to test idempotency...")
    res3 = client.post(
        "/api/chat/send",
        json={"message": booking_msg, "session_id": session_id},
        headers=headers
    )
    assert res3.status_code == 200

    apps_after = SupabaseService.get_records("appointments", {"user_id": test_user_id, "doctor_id": doc_id, "date": tomorrow})
    assert len(apps_after) == len(apps), "Duplicate appointment was created despite idempotency key!"
    print("Idempotency verified: no duplicate appointment created.")
    print("Phase 4 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase4()
