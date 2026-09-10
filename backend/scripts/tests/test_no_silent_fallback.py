import sys
import os
import pytest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database.supabase_client import SupabaseService, DatabaseError, get_supabase_client

def test_no_silent_fallback_on_db_failure():
    print("==========================================")
    print("TEST: Database Error & Fallback Lockdown")
    print("==========================================")

    client = get_supabase_client()
    if not client:
        print("[SKIP] Supabase client not configured in test environment. Skipping active DB error test.")
        return

    print("\n[Step 1] Attempting invalid query against active Supabase database...")
    try:
        # Query nonexistent column to force a DB error
        SupabaseService.get_records("episodes", {"nonexistent_column_abc": "value_123"})
        assert False, "Expected DatabaseError was NOT raised! Silent fallback is still active."
    except DatabaseError as exc:
        print(f"[OK] DatabaseError correctly caught and raised: {exc}")

    print("\n[Step 2] Testing invalid insert against active Supabase database...")
    try:
        # Insert invalid data structure into table to force write error
        SupabaseService.insert_record("episodes", {"invalid_col_123": "val"})
        assert False, "Expected DatabaseError on failed insert was NOT raised! Silent fallback is still active."
    except DatabaseError as exc:
        print(f"[OK] DatabaseError correctly caught on failed write: {exc}")

    print("\n==========================================")
    print("NO SILENT FALLBACK TEST PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_no_silent_fallback_on_db_failure()
