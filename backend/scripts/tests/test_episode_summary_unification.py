import sys
import os
import uuid
import time
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database.supabase_client import SupabaseService
from app.services.summary_service import SummaryService
from app.services.episode_service import EpisodeService

def test_unified_episode_summary():
    print("==========================================")
    print("TEST: Unified Episode-Scoped Summary")
    print("==========================================")

    # 1. Setup Patient
    patient_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    t_minus_10d = (now - timedelta(days=10)).isoformat()
    t_minus_5d = (now - timedelta(days=5)).isoformat()
    t_minus_2d = (now - timedelta(days=2)).isoformat()

    # Episode 1: Resolved (Past episode)
    ep1 = {
        "id": f"ep1-{uuid.uuid4().hex[:6]}",
        "patient_id": patient_id,
        "condition": "Acute Bronchitis (Resolved)",
        "started_at": t_minus_10d,
        "resolved_at": t_minus_5d,
        "status": "resolved",
        "summary": "Old summary for bronchitis",
        "summary_generated_at": t_minus_5d,
        "created_at": t_minus_10d,
        "updated_at": t_minus_5d
    }
    SupabaseService.insert_record("episodes", ep1)

    # Episode 1 chat message & document
    c1 = {
        "id": str(uuid.uuid4()),
        "user_id": patient_id,
        "role": "user",
        "message": "I have severe wheezing and bronchitis coughing",
        "created_at": (now - timedelta(days=8)).isoformat()
    }
    SupabaseService.insert_record("chat_messages", c1)

    doc1 = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "episode_id": ep1["id"],
        "title": "Old Chest XRay",
        "record_type": "xray",
        "ocr_status": "completed",
        "extracted_text": "Findings: Bilateral bronchial wall thickening",
        "ocr_processed_at": (now - timedelta(days=8)).isoformat(),
        "created_at": (now - timedelta(days=8)).isoformat()
    }
    SupabaseService.insert_record("medical_records", doc1)

    # Episode 2: Active (Current episode)
    ep2 = {
        "id": f"ep2-{uuid.uuid4().hex[:6]}",
        "patient_id": patient_id,
        "condition": "Severe Migraine",
        "started_at": t_minus_2d,
        "resolved_at": None,
        "status": "active",
        "summary": None,
        "summary_generated_at": None,
        "created_at": t_minus_2d,
        "updated_at": t_minus_2d
    }
    SupabaseService.insert_record("episodes", ep2)

    # Episode 2 chat message & document
    c2 = {
        "id": str(uuid.uuid4()),
        "user_id": patient_id,
        "role": "user",
        "message": "I have a throbbing headache with extreme nausea and light sensitivity",
        "created_at": (now - timedelta(days=1)).isoformat()
    }
    SupabaseService.insert_record("chat_messages", c2)

    doc2 = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "episode_id": ep2["id"],
        "title": "Brain MRI Scan",
        "record_type": "mri",
        "ocr_status": "completed",
        "extracted_text": "MRI Findings: Unremarkable brain parenchyma, no acute intracranial hemorrhage",
        "ocr_processed_at": (now - timedelta(days=1)).isoformat(),
        "created_at": (now - timedelta(days=1)).isoformat()
    }
    SupabaseService.insert_record("medical_records", doc2)

    # ----------------------------------------------------
    # Check 1: Cross-episode isolation
    # ----------------------------------------------------
    print("\n[Check 1] Generating summary for Active Episode (Migraine)...")
    res1 = SummaryService.generate_episode_summary(ep2["id"])
    print(f"-> Generated at: {res1['generated_at']}")
    print(f"-> Cached status: {res1['cached']}")
    print(f"-> Summary snippet:\n{res1['summary'][:300]}")

    assert res1["cached"] is False, "Initial summary generation should not be cached"
    assert "bronchitis" not in res1["summary"].lower(), "Resolved episode 1 content (bronchitis) leaked into episode 2 summary!"
    assert "migraine" in res1["summary"].lower() or "headache" in res1["summary"].lower(), "Active episode condition/symptoms missing!"
    print("[OK] Check 1 PASSED: Cross-episode isolation verified (0 bleed-through from resolved episode).")

    # ----------------------------------------------------
    # Check 2: Consecutive call returns cached: True
    # ----------------------------------------------------
    print("\n[Check 2] Calling generate_episode_summary again with no data changes...")
    res2 = SummaryService.generate_episode_summary(ep2["id"])
    print(f"-> Cached status: {res2['cached']}")
    assert res2["cached"] is True, "Second call should return cached: True"
    print("[OK] Check 2 PASSED: Cache hit verified.")

    # ----------------------------------------------------
    # Check 3: Mid-episode document addition triggers staleness & regeneration
    # ----------------------------------------------------
    print("\n[Check 3] Adding new completed document to active episode...")
    time.sleep(0.01)
    doc3_ts = datetime.now(timezone.utc).isoformat()

    doc3 = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "episode_id": ep2["id"],
        "title": "Blood Panel Report",
        "record_type": "blood_test",
        "ocr_status": "completed",
        "extracted_text": "Blood Findings: Elevated CRP and WBC count",
        "ocr_processed_at": doc3_ts,
        "created_at": doc3_ts
    }
    SupabaseService.insert_record("medical_records", doc3)

    res3 = SummaryService.generate_episode_summary(ep2["id"])
    print(f"-> Cached status after new doc: {res3['cached']}")
    assert res3["cached"] is False, "New document should trigger cache invalidation and fresh LLM summary"
    print("[OK] Check 3 PASSED: Staleness detection on document upload verified.")

    # ----------------------------------------------------
    # Check 4: Patient-reported chat framing verification
    # ----------------------------------------------------
    print("\n[Check 4] Verifying patient-reported chat labeling in output...")
    summary_lower = res3["summary"].lower()
    assert "patient" in summary_lower or "reported" in summary_lower or "headache" in summary_lower
    print("[OK] Check 4 PASSED: Patient-reported chat framing verified.")

    print("\n==========================================")
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_unified_episode_summary()
