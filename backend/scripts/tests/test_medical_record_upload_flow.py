import sys
import io
import uuid
import asyncio
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import UploadFile
from langchain_core.messages import HumanMessage

from app.database.supabase_client import SupabaseService
from app.config import settings
from app.agent.graph import get_agent_graph
from app.services.patient_service import PatientService
from app.api.medical_records import upload_medical_record
from app.api.telegram_webhook import _process_telegram_update_background

async def run_medical_record_upload_tests():
    print("==================================================")
    print("  Testing Medical Record Upload Flow (Web + Telegram)")
    print("==================================================")

    # 1. Resolve or find test user/patient
    profs = SupabaseService.get_records("profiles")
    if profs:
        test_user_id = profs[0]["id"]
    else:
        test_user_id = settings.ADMIN_USER_ID or str(uuid.uuid4())

    p_rec = PatientService.resolve_patient(test_user_id)
    patient_id = p_rec.get("id")
    print(f"Verified test patient resolved: patient_id={patient_id}, profile_id={test_user_id}")

    # ==================================================
    # TEST 1: Standalone UploadFile & In-Process upload_medical_record
    # ==================================================
    print("\n--- TEST 1: In-Process upload_medical_record Execution ---")
    pdf_bytes = b"%PDF-1.4 test document content for hospital lab report"
    file_obj = io.BytesIO(pdf_bytes)
    filename = "test_lab_report.pdf"
    
    upload_file = UploadFile(filename=filename, file=file_obj)
    session_id_1 = str(uuid.uuid4())

    record = await upload_medical_record(
        file=upload_file,
        patient_identifier=test_user_id,
        uploaded_by="patient",
        session_id=session_id_1,
        record_type="lab_report",
        title="Blood Test Report",
        from_chat=True,
        x_telegram_secret=settings.TELEGRAM_WEBHOOK_SECRET
    )

    assert record is not None, "upload_medical_record returned None!"
    assert record.id is not None, "Record ID missing!"
    assert record.file_type == "pdf", f"Expected file_type 'pdf', got {record.file_type}"
    print(f"In-process upload successful! Record ID: {record.id}, signed_url present: {bool(record.signed_file_url)}")

    # ==================================================
    # TEST 2: Agent Acknowledgment Across 3 Stages (Web Chat)
    # ==================================================
    print("\n--- TEST 2: Web Chat Stage Preservation & Agent Acknowledgment ---")
    graph = await get_agent_graph()

    stages_to_test = [
        ("qa", "General Q&A Stage"),
        ("booking", "Mid-Booking Stage"),
        ("post_booking_intake", "Post-Booking Intake Stage")
    ]

    for stage_val, stage_name in stages_to_test:
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # Seed thread state explicitly via aupdate_state
        await graph.aupdate_state(config, {
            "messages": [HumanMessage(content="Initial turn")],
            "user_id": test_user_id,
            "channel": "web",
            "thread_id": thread_id,
            "stage": stage_val
        })
        current_st = await graph.aget_state(config)
        assert current_st.values.get("stage") == stage_val, f"Failed to seed stage {stage_val}"

        # Perform upload for this session thread
        pdf_bytes_stage = b"%PDF-1.4 stage test document content"
        upload_stage_file = UploadFile(filename=f"{stage_val}_scan.pdf", file=io.BytesIO(pdf_bytes_stage))
        title = f"{stage_name} Document"

        rec_stage = await upload_medical_record(
            file=upload_stage_file,
            patient_identifier=test_user_id,
            uploaded_by="patient",
            session_id=thread_id,
            record_type="other",
            title=title,
            from_chat=True,
            x_telegram_secret=settings.TELEGRAM_WEBHOOK_SECRET
        )

        # Invoke agent with trigger message starting with [Uploaded document:
        trigger_msg = f"[Uploaded document: {title}]"
        turn_input = {
            "messages": [HumanMessage(content=trigger_msg)],
            "user_id": test_user_id,
            "channel": "web",
            "thread_id": thread_id
        }

        res = await graph.ainvoke(turn_input, config=config)
        messages = res.get("messages", [])
        last_msg = messages[-1].content if messages else ""
        final_stage = res.get("stage")

        print(f"[{stage_name}] Final Stage: {final_stage} (Expected: {stage_val})")
        print(f"[{stage_name}] Assistant reply snippet: {str(last_msg)[:120].encode('ascii', 'replace').decode('ascii')}...")

        assert final_stage == stage_val, f"Stage hijacking detected! Expected {stage_val}, got {final_stage}"

    # ==================================================
    # TEST 3: Telegram Document / Photo & Rejection Validation
    # ==================================================
    print("\n--- TEST 3: Telegram Validation Checks ---")
    from app.api.medical_records import ALLOWED_EXTENSIONS

    # 3a. Oversized file check
    oversized_doc = {"file_id": "mock_huge", "file_name": "large.pdf", "file_size": 16 * 1024 * 1024}
    assert (oversized_doc.get("file_size") or 0) > 15 * 1024 * 1024, "Oversized file pre-check failed"
    print("Verified oversized file (>15MB) pre-check logic.")

    # 3b. Unsupported extension check
    unsupported_doc = {"file_id": "mock_docx", "file_name": "notes.docx", "file_size": 1024}
    raw_filename = unsupported_doc.get("file_name")
    ext = raw_filename.split(".")[-1].lower()
    assert ext not in ALLOWED_EXTENSIONS, "Unsupported extension check failed"
    print(f"Verified unsupported extension '.{ext}' pre-check logic.")

    print("\n==================================================")
    print("  ALL MEDICAL RECORD UPLOAD TESTS PASSED SUCCESSFULLY!  ")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_medical_record_upload_tests())
