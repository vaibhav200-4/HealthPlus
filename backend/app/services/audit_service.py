import uuid
import logging
from typing import Dict, Any, Optional
from app.database.supabase_client import SupabaseService

logger = logging.getLogger("hospital_app.audit")

class AuditService:
    @staticmethod
    def log_action(
        user_id: Optional[str],
        hospital_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Service-layer audit logging for security compliance and immutable event tracking.
        """
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "hospital_id": hospital_id or "H001",
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_value": old_value,
            "new_value": new_value
        }
        res = SupabaseService.insert_record("audit_logs", record)
        logger.info(f"Audit log recorded: [{action}] on {resource_type}:{resource_id} by user {user_id}")
        return res
