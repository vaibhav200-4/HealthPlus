import httpx
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger("hospital_app.n8n")

class N8nService:
    @staticmethod
    async def send_web_chat(user_id: str, message: str, session_id: str) -> str:
        webhook_url = settings.N8N_WEBHOOK_URL
        if not webhook_url:
            logger.warning("N8N_WEBHOOK_URL is not set.")
            return "n8n Webhook URL is not configured. Please set N8N_WEBHOOK_URL in environment variables."

        payload = {
            "user_id": user_id,
            "message": message,
            "text": message,
            "session_id": session_id,
            "sessionId": session_id
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(webhook_url, json=payload)
                logger.info(f"n8n response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        res_json = response.json()
                        # Extract response text based on common n8n return patterns
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
