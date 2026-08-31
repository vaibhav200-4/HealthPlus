import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import resend
from app.config import settings
from app.database.supabase_client import SupabaseService

logger = logging.getLogger("hospital_app.email")

# Initialize resend API key at module load if available
if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY


async def send_appointment_confirmation_email(
    to_email: str,
    patient_name: str,
    doctor_name: str,
    hospital_name: str,
    appointment_date: str,
    start_time: str,
    end_time: str,
    user_id: Optional[str] = None,
    hospital_id: Optional[str] = None,
    appointment_id: Optional[str] = None
) -> bool:
    """
    Fire-and-forget email notification service for web appointment bookings using Resend.
    - Runs in a background task after web appointment creation.
    - Synchronous resend.Emails.send call is wrapped in asyncio.to_thread so it never blocks the event loop.
    - Catches all exceptions and logs error (NEVER raises).
    - Logs audit record in Supabase 'notifications' table.
    """
    if not to_email or not to_email.strip():
        logger.warning("Empty recipient email provided. Skipping email send.")
        return False

    api_key = settings.RESEND_API_KEY or resend.api_key
    if not api_key:
        logger.warning(f"RESEND_API_KEY is not set. Email to {to_email} skipped.")
        _record_notification_audit(
            user_id=user_id,
            hospital_id=hospital_id,
            to_email=to_email,
            appointment_id=appointment_id,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            status="failed"
        )
        return False

    resend.api_key = api_key

    subject = f"Appointment Confirmation - {hospital_name}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Appointment Confirmation</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b;">
      <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="text-align: center; margin-bottom: 24px;">
          <h2 style="color: #0d9488; margin: 0; font-size: 24px; font-weight: 800;">HealthPulse</h2>
          <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #0d9488; font-weight: bold;">Smart Healthcare Platform</span>
        </div>
        
        <h3 style="color: #0f172a; font-size: 18px; margin-top: 0;">Appointment Confirmed</h3>
        <p style="font-size: 14px; color: #475569; line-height: 1.6;">
          Dear <strong>{patient_name}</strong>,
        </p>
        <p style="font-size: 14px; color: #475569; line-height: 1.6;">
          Your appointment has been successfully scheduled. Below are your consultation details:
        </p>
        
        <div style="background-color: #f1f5f9; border-radius: 12px; padding: 20px; margin: 20px 0;">
          <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr>
              <td style="padding: 6px 0; color: #64748b; font-weight: 600; width: 35%;">Doctor:</td>
              <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{doctor_name}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Hospital:</td>
              <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{hospital_name}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Date:</td>
              <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{appointment_date}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Time Slot:</td>
              <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{start_time} &ndash; {end_time}</td>
            </tr>
          </table>
        </div>

        <p style="font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 0;">
          If you need to manage or reschedule your appointment, please log into your account on HealthPulse.
        </p>
        <p style="font-size: 13px; color: #64748b; margin-top: 16px;">
          Best regards,<br>
          <strong>{hospital_name} Team</strong>
        </p>
      </div>
    </body>
    </html>
    """

    params: Dict[str, Any] = {
        "from": settings.EMAIL_FROM or "onboarding@resend.dev",
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }

    try:
        # Wrap synchronous resend.Emails.send call in asyncio.to_thread so it never blocks the event loop
        res = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Successfully sent appointment confirmation email to {to_email} via Resend. Result: {res}")
        
        _record_notification_audit(
            user_id=user_id,
            hospital_id=hospital_id,
            to_email=to_email,
            appointment_id=appointment_id,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            status="sent"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send appointment confirmation email to {to_email}: {e}")
        _record_notification_audit(
            user_id=user_id,
            hospital_id=hospital_id,
            to_email=to_email,
            appointment_id=appointment_id,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            status="failed"
        )
        return False


def _record_notification_audit(
    user_id: Optional[str],
    hospital_id: Optional[str],
    to_email: str,
    appointment_id: Optional[str],
    doctor_name: str,
    appointment_date: str,
    status: str
):
    """Helper to record notification audit row in Supabase notifications table. Swallows exceptions."""
    try:
        now_str = datetime.now(timezone.utc).isoformat()
        notification_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id or "system",
            "hospital_id": hospital_id or "H001",
            "type": "appointment_confirmed",
            "channel": "email",
            "payload": {
                "appointment_id": appointment_id,
                "to": to_email,
                "doctor_name": doctor_name,
                "date": appointment_date
            },
            "status": status,
            "created_at": now_str,
            "sent_at": now_str if status == "sent" else None
        }
        SupabaseService.insert_record("notifications", notification_record)
    except Exception as err:
        logger.warning(f"Failed to record notification audit row for {to_email}: {err}")
