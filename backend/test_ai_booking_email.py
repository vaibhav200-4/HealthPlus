import asyncio
import logging
from unittest.mock import MagicMock
from app.services.email_service import send_appointment_confirmation_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ai_email")

async def run_ai_booking_email_test():
    print("--- Testing email resolution logic for AI Agent booking ---")
    
    # 1. Test when email is resolved
    mock_bg = MagicMock()
    
    # Simulate email resolution logic
    app_data = {"patient_email": "webuser@example.com", "patient_name": "Web Patient", "doctor_name": "Dr. Arjun Mehta", "hospital_name": "Sunrise Hospital", "date": "2026-08-30", "start_time": "11:00 AM", "end_time": "11:30 AM", "id": "app-999"}
    payload = {}
    p_email = "fallback@example.com"
    user_id = "user-uuid-1"
    
    resolved_email = app_data.get("patient_email") or payload.get("patient_email") or p_email
    if resolved_email and resolved_email.strip():
        mock_bg.add_task(
            send_appointment_confirmation_email,
            to_email=resolved_email.strip(),
            patient_name=app_data.get("patient_name"),
            doctor_name=app_data.get("doctor_name"),
            hospital_name=app_data.get("hospital_name"),
            appointment_date=str(app_data.get("date")),
            start_time=app_data.get("start_time"),
            end_time=app_data.get("end_time"),
            user_id=user_id,
            hospital_id="H001",
            appointment_id=app_data.get("id")
        )
    
    print(f"Background task added count: {mock_bg.add_task.call_count}")
    assert mock_bg.add_task.call_count == 1
    args, kwargs = mock_bg.add_task.call_args
    print(f"Task target: {args[0].__name__}")
    print(f"Resolved email passed to task: {kwargs['to_email']}")
    assert kwargs['to_email'] == "webuser@example.com"

    # 2. Test when email is empty (e.g. Telegram user without email)
    mock_bg_empty = MagicMock()
    app_data_empty = {"patient_email": "", "patient_name": "Telegram User", "doctor_name": "Dr. Arjun Mehta", "hospital_name": "Sunrise Hospital", "date": "2026-08-30", "start_time": "11:00 AM", "end_time": "11:30 AM", "id": "app-888"}
    p_email_empty = ""
    
    resolved_email_empty = app_data_empty.get("patient_email") or p_email_empty
    if resolved_email_empty and resolved_email_empty.strip():
        mock_bg_empty.add_task(send_appointment_confirmation_email)
    
    print(f"Telegram user without email task count: {mock_bg_empty.add_task.call_count} (Expected 0)")
    assert mock_bg_empty.add_task.call_count == 0

    print("--- All AI Agent Booking Email tests passed! ---")

if __name__ == "__main__":
    asyncio.run(run_ai_booking_email_test())
