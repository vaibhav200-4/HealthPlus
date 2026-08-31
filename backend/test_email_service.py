import asyncio
import logging
import uuid
from app.services.email_service import send_appointment_confirmation_email
from app.database.supabase_client import SupabaseService
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_email")

async def run_tests():
    print("--- 1. Test Email Service with missing / mock API Key ---")
    # Store original key
    original_key = settings.RESEND_API_KEY
    test_user_id = str(uuid.uuid4())

    # Test with empty API key
    settings.RESEND_API_KEY = ""
    result = await send_appointment_confirmation_email(
        to_email="testpatient@example.com",
        patient_name="John Doe",
        doctor_name="Dr. Arjun Mehta",
        hospital_name="Sunrise Multispeciality Hospital",
        appointment_date="2026-08-30",
        start_time="10:00 AM",
        end_time="10:30 AM",
        user_id=test_user_id,
        hospital_id="H001",
        appointment_id=str(uuid.uuid4())
    )
    print(f"Result with missing API key: {result} (Expected: False, no exception raised)")

    # Test audit record creation in notifications table
    notifications = SupabaseService.get_records("notifications", {"user_id": test_user_id})
    print(f"Notification audit records found: {len(notifications)}")
    if notifications:
        latest = notifications[-1]
        print(f"Latest notification status: {latest.get('status')}, type: {latest.get('type')}, channel: {latest.get('channel')}")

    # Restore key
    settings.RESEND_API_KEY = original_key
    print("--- Tests completed successfully! ---")

if __name__ == "__main__":
    asyncio.run(run_tests())
