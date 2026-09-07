import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from app.config import settings

logger = logging.getLogger("hospital_app.supabase")

# In-memory fallback store for local development if Supabase URL is placeholder
_LOCAL_STORE: Dict[str, List[Dict[str, Any]]] = {
    "profiles": [],
    "hospitals": [],
    "hospital_members": [],
    "departments": [],
    "doctors": [],
    "schedules": [],
    "appointments": [],
    "patients": [],
    "sessions": [],
    "prescriptions": [],
    "prescription_items": [],
    "medical_records": [],
    "doctor_reviews": [],
    "chat_messages": [],
    "chat_sessions": [],
    "telegram_accounts": [],
    "notifications": [],
    "audit_logs": [],
    "patient_summaries": [],
    "patient_intake_notes": []
}

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    if (
        settings.SUPABASE_URL 
        and "your-supabase-project" not in settings.SUPABASE_URL 
        and settings.SUPABASE_ANON_KEY 
        and "your-supabase-anon-key" not in settings.SUPABASE_ANON_KEY
    ):
        try:
            from supabase import create_client
            key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
            _supabase_client = create_client(settings.SUPABASE_URL, key)
            logger.info("Successfully connected to Supabase.")
            return _supabase_client
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to local store.")
    
    logger.info("Using local database fallback mode.")
    return None

class SupabaseService:
    @staticmethod
    def is_supabase_active() -> bool:
        return get_supabase_client() is not None

    @staticmethod
    def get_records(table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        client = get_supabase_client()
        remote_data = None
        if client:
            try:
                query = client.table(table).select("*")
                if filters:
                    for k, v in filters.items():
                        query = query.eq(k, v)
                res = query.execute()
                remote_data = res.data
            except Exception as e:
                logger.error(f"Error fetching from Supabase table {table}: {e}")

        if remote_data is not None and len(remote_data) > 0:
            local_items = {str(item.get("id")): item for item in _LOCAL_STORE.get(table, []) if item.get("id")}
            merged = []
            for item in remote_data:
                item_id = str(item.get("id"))
                if item_id in local_items:
                    merged_item = dict(item)
                    for k, v in local_items[item_id].items():
                        if k not in merged_item or merged_item[k] is None or v is not None:
                            merged_item[k] = v
                    merged.append(merged_item)
                else:
                    merged.append(item)
            return merged

        # Local fallback if remote empty or errored
        records = _LOCAL_STORE.get(table, [])
        if filters:
            filtered = []
            for item in records:
                match = True
                for k, v in filters.items():
                    if item.get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(item)
            return filtered
        return list(records)

    @staticmethod
    def get_record_by_id(table: str, record_id: Any, id_field: str = "id") -> Optional[Dict[str, Any]]:
        records = SupabaseService.get_records(table, {id_field: str(record_id)})
        return records[0] if records else None

    @staticmethod
    def insert_record(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        
        # Always maintain in local store
        records = _LOCAL_STORE.setdefault(table, [])
        # Avoid duplicate insert in local store
        if not any(str(r.get("id")) == str(data["id"]) for r in records):
            records.append(data)

        client = get_supabase_client()
        if client:
            try:
                res = client.table(table).insert(data).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Error inserting into Supabase table {table}: {e}")
                logger.critical(f"CRITICAL: Insert operation into table '{table}' fell back to _LOCAL_STORE!")
        else:
            logger.critical(f"CRITICAL: Insert operation into table '{table}' executing in _LOCAL_STORE fallback mode!")
        
        return data

    @staticmethod
    def update_record(table: str, record_id: Any, updates: Dict[str, Any], id_field: str = "id") -> Optional[Dict[str, Any]]:
        updated_item = None
        records = _LOCAL_STORE.setdefault(table, [])
        for item in records:
            if str(item.get(id_field)) == str(record_id):
                item.update(updates)
                updated_item = item
                break

        client = get_supabase_client()
        if client:
            try:
                res = client.table(table).update(updates).eq(id_field, str(record_id)).execute()
                if res.data:
                    remote_res = res.data[0]
                    if updated_item:
                        updated_item.update(remote_res)
                    return remote_res
            except Exception as e:
                logger.error(f"Error updating Supabase table {table}: {e}")
                logger.critical(f"CRITICAL: Update operation on table '{table}' fell back to _LOCAL_STORE!")

        if not updated_item:
            # If not in local store, fetch remote record, apply updates, and store locally
            try:
                if client:
                    res = client.table(table).select("*").eq(id_field, str(record_id)).execute()
                    if res.data:
                        rec = dict(res.data[0])
                        rec.update(updates)
                        records.append(rec)
                        updated_item = rec
            except Exception:
                pass

        return updated_item

    @staticmethod
    def delete_record(table: str, record_id: Any, id_field: str = "id") -> bool:
        client = get_supabase_client()
        if client:
            try:
                client.table(table).delete().eq(id_field, str(record_id)).execute()
                return True
            except Exception as e:
                logger.error(f"Error deleting from Supabase table {table}: {e}")
                logger.critical(f"CRITICAL: Delete operation on table '{table}' fell back to _LOCAL_STORE!")
        else:
            logger.critical(f"CRITICAL: Delete operation on table '{table}' executing in _LOCAL_STORE fallback mode!")
        
        # Local fallback
        records = _LOCAL_STORE.get(table, [])
        _LOCAL_STORE[table] = [r for r in records if str(r.get(id_field)) != str(record_id)]
        return True
