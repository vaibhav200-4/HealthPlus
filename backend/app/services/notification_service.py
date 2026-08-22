import uuid
import logging
from typing import Dict, Any, Optional
from app.database.supabase_client import SupabaseService

logger = logging.getLogger("hospital_app.notifications")

class NotificationService:
    @staticmethod
    def create_notification(
        user_id: str,
        hospital_id: str,
        type: str,
        channel: str = "web",
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Guaranteed notification creation service.
        Called strictly AFTER underlying database transactions commit.
        """
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "hospital_id": hospital_id,
            "type": type,
            "channel": channel,
            "payload": payload or {},
            "status": "pending"
        }
        res = SupabaseService.insert_record("notifications", record)
        logger.info(f"Notification created [{type}] for user {user_id}")
        return res
