import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import create_n8n_context_token

logger = logging.getLogger("hospital_app.n8n")

class N8nService:
    @staticmethod
    async def send_web_chat(user_id: str, message: str, session_id: str, channel: str = "web") -> str:
        webhook_url = settings.N8N_WEBHOOK_URL
        if not webhook_url:
            logger.warning("N8N_WEBHOOK_URL is not set.")
            return "n8n Webhook URL is not configured. Please set N8N_WEBHOOK_URL in environment variables."

        # Fetch user role & hospital context
        user_role = "patient"
        hospital_id = "H001"
        telegram_id = None

        profiles = SupabaseService.get_records("profiles", {"id": user_id})
        if profiles:
            user_role = profiles[0].get("role", "patient")
            telegram_id = profiles[0].get("telegram_id")
            
            # Resolve hospital_id for doctors/members
            members = SupabaseService.get_records("hospital_members", {"user_id": user_id})
            if members:
                hospital_id = members[0].get("hospital_id", "H001")
            else:
                docs = SupabaseService.get_records("doctors", {"profile_id": user_id})
                if docs:
                    hospital_id = docs[0].get("hospital_id", "H001")

        # Generate short-lived signed JWT for n8n tool call authorization boundary
        n8n_token = create_n8n_context_token(
            user_id=user_id,
            role=user_role,
            hospital_id=hospital_id,
            session_id=session_id
        )

        # Standardized normalized AI payload across Web and Telegram channels
        payload = {
            "user_id": user_id,
            "role": user_role,
            "hospital_id": hospital_id,
            "session_id": session_id,
            "sessionId": session_id,
            "channel": channel,
            "telegram_id": telegram_id,
            "message": message,
            "text": message,
            "n8n_token": n8n_token
        }

        headers = {
            "Content-Type": "application/json",
            "X-N8n-Token": n8n_token
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(webhook_url, json=payload, headers=headers)
                logger.info(f"n8n response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        res_json = response.json()
                        if isinstance(res_json, dict):
                            return (
                                res_json.get("output") or 
                                res_json.get("response") or 
                                res_json.get("text") or 
                                res_json.get("message") or 
                                str(res_json)
                            )
                        elif isinstance(res_json, list) and len(res_json) > 0:
                            first_item = res_json[0]
                            if isinstance(first_item, dict):
                                return (
                                    first_item.get("output") or 
                                    first_item.get("response") or 
                                    first_item.get("text") or 
                                    first_item.get("message") or 
                                    str(first_item)
                                )
                            return str(first_item)
                        return response.text
                    except Exception:
                        return response.text
                else:
                    logger.error(f"n8n Webhook returned status code {response.status_code}: {response.text}")
                    return f"Received error from AI assistant ({response.status_code})."
        except Exception as e:
            logger.error(f"Error calling n8n webhook: {e}")
            return "Unable to connect to AI assistant at the moment. Please try again later."
