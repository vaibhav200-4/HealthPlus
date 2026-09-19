import json
import uuid
import logging
import httpx
from typing import Dict, List, Any, Optional, Callable
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

_supabase_client = None

# Errors that mean "the pooled connection was already dead when we tried to use it" —
# safe to retry once with a fresh client, since no request actually reached the server.
_RETRYABLE_ERRORS = (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError)


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


def _reset_client():
    """Discard the current client so the next get_supabase_client() call builds
    a brand-new one with a fresh underlying httpx connection pool."""
    global _supabase_client
    _supabase_client = None


def _run_with_retry(build_query: Callable[[Any], Any], table: str, action: str):
    """
    Runs a Supabase query. If it fails because a pooled HTTP connection was already
    dead (e.g. 'Server disconnected'), discards the client and retries exactly once
    with a fresh one. Any other exception (real query errors, auth errors, etc.)
    is raised immediately without retrying.

    build_query: a function that takes a supabase client and returns the executed result.
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        return build_query(client)
    except _RETRYABLE_ERRORS as e:
        logger.warning(
            f"[SUPABASE RETRY] '{action}' on '{table}' hit a dead pooled connection "
            f"({type(e).__name__}: {e}). Retrying once with a fresh client..."
        )
        _reset_client()
        fresh_client = get_supabase_client()
        if fresh_client is None:
            raise
        return build_query(fresh_client)


class SupabaseService:
    @staticmethod
    def is_supabase_active() -> bool:
        return get_supabase_client() is not None

    @staticmethod
    def get_records(table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        client = get_supabase_client()
        if client:
            def _query(c):
                query = c.table(table).select("*")
                if filters:
                    for k, v in filters.items():
                        query = query.eq(k, v)
                res = query.execute()
                return res.data if res.data is not None else []

            try:
                return _run_with_retry(_query, table, "get_records")
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
            def _query(c):
                res = c.table(table).insert(data).execute()
                if res.data:
                    return res.data[0]
                return data

            try:
                return _run_with_retry(_query, table, "insert_record")
            except Exception as e:
                logger.error(f"Error inserting into Supabase table '{table}': {e}")
                raise DatabaseError(f"Insert into table '{table}' failed: {e}") from e

        # Local standalone mode when Supabase is not configured
        records = _LOCAL_STORE.setdefault(table, [])
        if not any(str(r.get("id")) == str(data["id"]) for r in records):
            records.append(data)
        return data

    @staticmethod
    def update_record(table: str, record_id: Any, updates: Dict[str, Any], id_field: str = "id") -> Optional[Dict[str, Any]]:
        client = get_supabase_client()
        if client:
            def _query(c):
                res = c.table(table).update(updates).eq(id_field, str(record_id)).execute()
                if res.data:
                    return res.data[0]
                return None

            try:
                return _run_with_retry(_query, table, "update_record")
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
        return updated_item

    @staticmethod
    def delete_record(table: str, record_id: Any, id_field: str = "id") -> bool:
        client = get_supabase_client()
        if client:
            def _query(c):
                c.table(table).delete().eq(id_field, str(record_id)).execute()
                return True

            try:
                return _run_with_retry(_query, table, "delete_record")
            except Exception as e:
                logger.error(f"Error deleting from Supabase table '{table}': {e}")
                raise DatabaseError(f"Delete from table '{table}' failed: {e}") from e

        # Local standalone mode when Supabase is not configured
        records = _LOCAL_STORE.get(table, [])
        _LOCAL_STORE[table] = [r for r in records if str(r.get(id_field)) != str(record_id)]
        return True