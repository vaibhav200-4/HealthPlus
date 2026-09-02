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

def test_phase2():
    print("--- Phase 2 Acceptance Test ---")
    settings.LLM_PROVIDER = "gemini"
    
    # Obtain or create a test profile
    profs = SupabaseService.get_records("profiles")
    if profs:
        test_user_id = profs[0]["id"]
        test_email = profs[0].get("email", "test@hospital.com")
        test_role = profs[0].get("role", "patient")
    else:
        test_user_id = str(uuid.uuid4())
        test_email = "test_phase2@hospital.com"
        test_role = "patient"
        SupabaseService.insert_record("profiles", {
            "id": test_user_id,
            "email": test_email,
            "name": "Phase2 Test User",
            "role": test_role
        })

    token = create_access_token(test_user_id, test_email, test_role)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = f"sess_p2_{uuid.uuid4().hex[:6]}"

    client = TestClient(app)

    # 1. Test with USE_AGENT = True
    settings.USE_AGENT = True
    print("Testing POST /api/chat/send with USE_AGENT=True...")
    res_agent = client.post(
        "/api/chat/send",
        json={"message": "where is the hospital", "session_id": session_id},
        headers=headers
    )
    assert res_agent.status_code == 200, f"Expected 200, got {res_agent.status_code}: {res_agent.text}"
    body_agent = res_agent.json()
    assert body_agent["message"], "Agent response message was empty!"
    assert body_agent["session_id"] == session_id
    print(f"Agent response received: '{body_agent['message'][:80]}...'")

    # 2. Test with USE_AGENT = False (kill switch fallback to n8n)
    settings.USE_AGENT = False
    print("Testing POST /api/chat/send with USE_AGENT=False (kill switch fallback)...")
    res_n8n = client.post(
        "/api/chat/send",
        json={"message": "where is the hospital", "session_id": session_id},
        headers=headers
    )
    assert res_n8n.status_code == 200, f"Expected 200, got {res_n8n.status_code}: {res_n8n.text}"
    body_n8n = res_n8n.json()
    print(f"n8n fallback response received: '{body_n8n['message'][:80]}...'")

    # Restore settings.USE_AGENT
    settings.USE_AGENT = True
    print("Phase 2 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase2()
