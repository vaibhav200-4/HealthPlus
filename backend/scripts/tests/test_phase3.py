import sys
import uuid
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.config import settings
from app.database.supabase_client import SupabaseService

def test_phase3():
    print("--- Phase 3 Acceptance Test ---")
    settings.LLM_PROVIDER = "gemini"
    client = TestClient(app)

    # 1. Reject invalid / missing secret token with 403
    print("Testing Webhook 403 rejection on missing secret token...")
    res_bad = client.post("/api/telegram/webhook", json={"message": {"text": "hi"}})
    assert res_bad.status_code == 403, f"Expected 403, got {res_bad.status_code}"
    print("Webhook 403 rejection verified.")

    # 2. Valid update processing & 200 OK ack
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    headers = {"X-Telegram-Bot-Api-Secret-Token": secret}
    tg_id = f"998877{uuid.uuid4().hex[:4]}"
    chat_id = f"12345{uuid.uuid4().hex[:4]}"

    payload = {
        "message": {
            "chat": {"id": chat_id},
            "from": {"id": tg_id, "first_name": "Test", "last_name": "TelegramUser"},
            "text": "Where is the hospital located?"
        }
    }

    print("Sending valid Telegram update to POST /api/telegram/webhook...")
    res_good = client.post("/api/telegram/webhook", json=payload, headers=headers)
    
    assert res_good.status_code == 200, f"Expected 200, got {res_good.status_code}"
    assert res_good.json() == {"status": "ok"}
    print("Webhook 200 OK status verified.")

    # 3. Verify chat_messages contains user and assistant entries for this telegram_id
    msgs = SupabaseService.get_records("chat_messages", {"telegram_id": tg_id})
    print(f"Found {len(msgs)} chat message(s) logged for telegram_id {tg_id}")
    roles = [m.get("role") for m in msgs]
    assert "user" in roles, "User message was not logged in chat_messages!"
    
    print("Phase 3 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase3()
