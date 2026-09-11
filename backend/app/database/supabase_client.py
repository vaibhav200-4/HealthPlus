import json
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.config import settings

logger = logging.getLogger("hospital_app.supabase")

class DatabaseError(Exception):
    """Raised when a database query or mutation fails while connected to Supabase."""
    pass

# In-memory store ONLY used when Supabase connection is NOT configured (standalone local mode)
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
    "patient_intake_notes": [],
    "episodes": []
}

_LOCAL_DB_FILE = Path(__file__).resolve().parents[2] / "local_db.json"

_supabase_client = None


def _load_local_store() -> None:
    global _LOCAL_STORE
    if not _LOCAL_DB_FILE.exists():
        return

    try:
        with _LOCAL_DB_FILE.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)
        if isinstance(raw_data, dict):
            for table, records in _LOCAL_STORE.items():
                loaded_records = raw_data.get(table, [])
                if isinstance(loaded_records, list):
                    records[:] = loaded_records
            for table, records in raw_data.items():
                if table not in _LOCAL_STORE:
                    _LOCAL_STORE[table] = records if isinstance(records, list) else []
    except Exception as e:
        logger.warning(f"Failed to load local DB file '{_LOCAL_DB_FILE}': {e}")


def _persist_local_store() -> None:
    try:
        with _LOCAL_DB_FILE.open("w", encoding="utf-8") as f:
            json.dump(_LOCAL_STORE, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to persist local DB file '{_LOCAL_DB_FILE}': {e}")


_load_local_store()

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
            logger.error(f"Failed to initialize Supabase client: {e}.")
            raise DatabaseError(f"Supabase initialization error: {e}") from e
    
    logger.info("Using local database fallback mode (Supabase not configured).")
    return None

class SupabaseService:
    @staticmethod
    def is_supabase_active() -> bool:
        return get_supabase_client() is not None

    @staticmethod
    def get_records(table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        client = get_supabase_client()
        if client:
            try:
                query = client.table(table).select("*")
                if filters:
                    for k, v in filters.items():
                        query = query.eq(k, v)
                res = query.execute()
                return res.data if res.data is not None else []
            except Exception as e:
                logger.error(f"Error fetching from Supabase table '{table}': {e}")
                raise DatabaseError(f"Fetch from table '{table}' failed: {e}") from e

        # Local standalone mode when Supabase is not configured
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

        client = get_supabase_client()
        if client:
            try:
                res = client.table(table).insert(data).execute()
                if res.data and len(res.data) > 0:
                    inserted = res.data[0]
                    # Also keep local store in sync for active client
                    records = _LOCAL_STORE.setdefault(table, [])
                    if not any(str(r.get("id")) == str(inserted.get("id")) for r in records):
                        records.append(inserted)
                    return inserted
                logger.error(f"Supabase insert returned empty data for table {table}")
                return None
            except Exception as e:
                logger.error(f"Error inserting into Supabase table {table}: {e}")
                raise DatabaseError(f"Insert into table '{table}' failed: {e}") from e
        
        # Only use local store if client is explicitly not configured (offline local dev mode)
        logger.info(f"Insert operation into table '{table}' executing in offline _LOCAL_STORE mode.")
        records = _LOCAL_STORE.setdefault(table, [])
        if not any(str(r.get("id")) == str(data["id"]) for r in records):
            records.append(data)
        _persist_local_store()
        return data

    @staticmethod
    def update_record(table: str, record_id: Any, updates: Dict[str, Any], id_field: str = "id") -> Optional[Dict[str, Any]]:
        client = get_supabase_client()
        if client:
            try:
                res = client.table(table).update(updates).eq(id_field, str(record_id)).execute()
                if res.data:
                    return res.data[0]
                return None
            except Exception as e:
                logger.error(f"Error updating Supabase table '{table}': {e}")
                raise DatabaseError(f"Update on table '{table}' failed: {e}") from e

        # Local standalone mode when Supabase is not configured
        updated_item = None
        records = _LOCAL_STORE.setdefault(table, [])
        for item in records:
            if str(item.get(id_field)) == str(record_id):
                item.update(updates)
                updated_item = item
                break
        _persist_local_store()
        return updated_item

    @staticmethod
    def delete_record(table: str, record_id: Any, id_field: str = "id") -> bool:
        client = get_supabase_client()
        if client:
            try:
                client.table(table).delete().eq(id_field, str(record_id)).execute()
                return True
            except Exception as e:
                logger.error(f"Error deleting from Supabase table '{table}': {e}")
                raise DatabaseError(f"Delete from table '{table}' failed: {e}") from e

        # Local standalone mode when Supabase is not configured
        records = _LOCAL_STORE.get(table, [])
        _LOCAL_STORE[table] = [r for r in records if str(r.get(id_field)) != str(record_id)]
        _persist_local_store()
        return True

