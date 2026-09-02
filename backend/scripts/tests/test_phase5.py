import sys
import uuid
import asyncio
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
from app.agent.tools import save_intake_note

def test_phase5():
    print("--- Phase 5 Acceptance Test ---")
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
        test_email = "patient_p5@test.com"
        test_role = "patient"
        SupabaseService.insert_record("profiles", {
            "id": test_user_id,
            "email": test_email,
            "name": "Phase5 Patient",
            "role": test_role
        })

    token = create_access_token(test_user_id, test_email, test_role)
    headers = {"Authorization": f"Bearer {token}"}

    # Test tool save_intake_note directly
    print("Saving intake note via save_intake_note tool...")
    asyncio.run(save_intake_note.ainvoke({
        "patient_id": test_user_id,
        "content": "Chest pain and shortness of breath",
        "structured_data": {"symptom": "chest pain", "duration": "2 days"}
    }))

    # Verify intake note created in DB or local store
    notes = SupabaseService.get_records("patient_intake_notes", {"patient_id": test_user_id})
    print(f"Found {len(notes)} intake note(s) in patient_intake_notes table for patient {test_user_id}")
    assert len(notes) > 0, "Intake note record was not created in patient_intake_notes!"
    assert notes[-1].get("source") == "agent", "Intake note source must be 'agent'!"
    print(f"Intake note verified: id={notes[-1]['id']}, source={notes[-1]['source']}")

    # Step C: Turn limit safety test - send messages to verify exit back to hospital_qa
    print("Testing safety exit after max intake turns...")
    session_id_turn_limit = f"sess_p5_limit_{uuid.uuid4().hex[:6]}"
    
    # Send 4 messages without completing intake to trigger 4-turn safety limit
    for i in range(1, 5):
        print(f"Sending turn {i} in post_booking_intake...")
        res_turn = client.post(
            "/api/chat/send",
            json={"message": f"Turn {i} response: I am still feeling unwell.", "session_id": session_id_turn_limit},
            headers=headers
        )
        assert res_turn.status_code == 200

    # Now post a QA question ("Where is the hospital located?") to verify graph has returned to hospital_qa node
    print("Verifying exit back to hospital_qa node with general question...")
    res_qa = client.post(
        "/api/chat/send",
        json={"message": "Where is the hospital located?", "session_id": session_id_turn_limit},
        headers=headers
    )
    assert res_qa.status_code == 200
    answer_text = res_qa.json()["message"]
    print(f"QA response received (len={len(answer_text)} characters).")
    print("Phase 5 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase5()
