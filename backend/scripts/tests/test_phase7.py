import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import create_access_token
from app.agent.tools import save_intake_note
import asyncio

def test_phase7():
    print("--- Phase 7 Acceptance Test ---")
    settings.LLM_PROVIDER = "nvidia"
    client = TestClient(app)

    # 1. Ensure test profile & patient exist
    profs = SupabaseService.get_records("profiles")
    if profs:
        test_user_id = profs[0]["id"]
        test_email = profs[0].get("email", "patient@test.com")
        test_role = profs[0].get("role", "patient")
    else:
        test_user_id = str(uuid.uuid4())
        test_email = "patient_p7@test.com"
        test_role = "patient"
        SupabaseService.insert_record("profiles", {
            "id": test_user_id,
            "email": test_email,
            "name": "Phase7 Patient",
            "role": test_role
        })

    token = create_access_token(test_user_id, test_email, test_role)
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure an intake note exists for patient
    asyncio.run(save_intake_note.ainvoke({
        "patient_id": test_user_id,
        "content": "Patient reports mild chest tightness after exercise.",
        "structured_data": {"symptom": "chest tightness", "trigger": "exercise"}
    }))

    # First call to summary endpoint -> should generate summary (cached: False)
    print("Calling GET /api/medical-records/patient/{patient_id}/summary (Call 1)...")
    res1 = client.get(f"/api/medical-records/patient/{test_user_id}/summary", headers=headers)
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}: {res1.text}"
    body1 = res1.json()
    assert body1.get("summary"), "Summary text was empty!"
    print(f"Call 1 response: cached={body1.get('cached')}, generated_at={body1.get('generated_at')}")

    # Second call to summary endpoint -> should return cached summary (cached: True)
    print("Calling GET /api/medical-records/patient/{patient_id}/summary (Call 2)...")
    res2 = client.get(f"/api/medical-records/patient/{test_user_id}/summary", headers=headers)
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.text}"
    body2 = res2.json()
    assert body2.get("cached") is True, f"Expected cached=True on second call, got {body2.get('cached')}"
    assert body1["summary"] == body2["summary"], "Cached summary text did not match initial summary!"
    print(f"Call 2 response verified: cached={body2.get('cached')}")

    print("Phase 7 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase7()
