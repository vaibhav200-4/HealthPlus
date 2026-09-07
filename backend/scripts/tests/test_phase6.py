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

def test_phase6():
    print("--- Phase 6 Acceptance Test ---")
    settings.LLM_PROVIDER = "nvidia"
    client = TestClient(app)

    # 1. Verify GET /health endpoint returns new service description and 200 OK
    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data.get("service") == "LangGraph Agent Hospital Assistant"
    assert "n8n_webhook_configured" not in health_data
    print("GET /health updated response verified successfully.")

    # 2. Verify n8n_service.py file deletion
    n8n_service_file = backend_dir / "app" / "services" / "n8n_service.py"
    assert not n8n_service_file.exists(), f"n8n_service.py file still exists at {n8n_service_file}!"
    print("n8n_service.py file deletion verified.")

    # 3. Test POST /api/chat/send functions cleanly without n8n_service
    profs = SupabaseService.get_records("profiles")
    if profs:
        test_user_id = profs[0]["id"]
        test_email = profs[0].get("email", "patient@test.com")
        test_role = profs[0].get("role", "patient")
    else:
        test_user_id = str(uuid.uuid4())
        test_email = "patient_p6@test.com"
        test_role = "patient"

    token = create_access_token(test_user_id, test_email, test_role)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = f"sess_p6_{uuid.uuid4().hex[:6]}"

    print("Testing POST /api/chat/send after n8n retirement...")
    res_chat = client.post(
        "/api/chat/send",
        json={"message": "What services are available?", "session_id": session_id},
        headers=headers
    )
    assert res_chat.status_code == 200
    body = res_chat.json()
    assert body.get("message"), "Response message was empty!"
    print(f"Chat response verified: '{body['message'][:80]}...'")

    print("Phase 6 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase6()
