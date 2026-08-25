import sys
import io
import uuid
import logging
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import create_access_token, create_n8n_context_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_medical_records")

client = TestClient(app)

def run_tests():
    logger.info("Starting Medical Records Verification Test Suite (Consolidated Pass)...")

    unique_suffix = uuid.uuid4().hex[:6]
    doc_profile_id = str(uuid.uuid4())
    doc_id = f"D_TEST_{unique_suffix}"
    doc_email = f"drtest_{unique_suffix}@hospital.com"

    patient_profile_id = str(uuid.uuid4())
    patient_db_id = str(uuid.uuid4())
    patient_email = f"testpatient_{unique_suffix}@hospital.com"
    patient_code = f"PT-{unique_suffix.upper()}"

    # Insert Doctor Profile & Doctor Record
    SupabaseService.insert_record("profiles", {
        "id": doc_profile_id,
        "name": f"Dr. Test Specialist {unique_suffix}",
        "email": doc_email,
        "role": "doctor"
    })
    SupabaseService.insert_record("doctors", {
        "id": doc_id,
        "profile_id": doc_profile_id,
        "name": f"Dr. Test Specialist {unique_suffix}",
        "hospital_id": "H001",
        "specialization": "Cardiology"
    })

    # Insert Patient Profile & Patient Record
    SupabaseService.insert_record("profiles", {
        "id": patient_profile_id,
        "name": "Test Patient Alpha",
        "email": patient_email,
        "phone": "+91 9999988888",
        "role": "patient"
    })
    SupabaseService.insert_record("patients", {
        "id": patient_db_id,
        "profile_id": patient_profile_id,
        "hospital_id": "H001",
        "patient_code": patient_code,
        "gender": "Female",
        "blood_group": "A+"
    })

    # Insert Test Appointment
    app_id = str(uuid.uuid4())
    SupabaseService.insert_record("appointments", {
        "id": app_id,
        "user_id": patient_profile_id,
        "doctor_id": doc_id,
        "hospital_id": "H001",
        "doctor_name": f"Dr. Test Specialist {unique_suffix}",
        "hospital_name": "City Hospital",
        "date": "2026-08-25",
        "start_time": "10:00 AM",
        "end_time": "10:30 AM",
        "status": "completed",
        "patient_name": "Test Patient Alpha",
        "patient_phone": "+91 9999988888",
        "patient_email": patient_email
    })

    headers_doc = {"Authorization": f"Bearer {create_access_token(doc_profile_id, doc_email, 'doctor')}"}
    headers_pat = {"Authorization": f"Bearer {create_access_token(patient_profile_id, patient_email, 'patient')}"}
    headers_telegram_secret = {"X-Telegram-Secret": "telegram-secret-key-0192837465"}

    # TEST 1: POST /api/medical-records/upload using patients.id with X-Telegram-Secret
    logger.info("Test 1: Uploading medical record using patients.id & X-Telegram-Secret...")
    mock_pdf_content = b"%PDF-1.4 Mock PDF Content For Medical Record"
    files = {"file": ("test_lab_report.pdf", io.BytesIO(mock_pdf_content), "application/pdf")}
    data = {
        "patient_identifier": patient_db_id,
        "uploaded_by": "doctor",
        "title": "Cardiology ECG Report",
        "record_type": "lab_report",
        "description": "Routine ECG test results showing normal sinus rhythm."
    }
    resp1 = client.post("/api/medical-records/upload", files=files, data=data, headers=headers_telegram_secret)
    assert resp1.status_code == 200, f"Upload failed: {resp1.text}"
    record1 = resp1.json()
    assert record1["patient_id"] == patient_db_id
    assert record1["uploaded_by"] == "doctor"
    assert record1["file_type"] == "pdf"
    logger.info("✓ Test 1 Passed: Upload using patients.id succeeded.")

    # TEST 2: POST /api/medical-records/upload using profiles.id (Telegram / Patient web compatibility)
    logger.info("Test 2: Uploading medical record using profiles.id...")
    mock_img_content = b"\x89PNG\r\n\x1a\nMock PNG Image Content"
    files2 = {"file": ("xray_scan.png", io.BytesIO(mock_img_content), "image/png")}
    data2 = {
        "patient_identifier": patient_profile_id,
        "uploaded_by": "patient",
        "title": "Patient Uploaded Chest X-Ray",
        "record_type": "xray",
        "description": "Uploaded via web profile."
    }
    resp2 = client.post("/api/medical-records/upload", files=files2, data=data2, headers=headers_pat)
    assert resp2.status_code == 200, f"Upload failed: {resp2.text}"
    record2 = resp2.json()
    assert record2["patient_id"] == patient_db_id
    assert record2["uploaded_by"] == "patient"
    assert record2["file_type"] == "png"
    logger.info("✓ Test 2 Passed: Upload using profiles.id resolved correctly to patients.id.")

    # TEST 3: Validation Error on Invalid File Extension
    logger.info("Test 3: Testing file extension validation (.exe)...")
    bad_files = {"file": ("malicious.exe", io.BytesIO(b"binary content"), "application/octet-stream")}
    data_bad = {
        "patient_identifier": patient_db_id,
        "title": "Bad File"
    }
    resp_bad = client.post("/api/medical-records/upload", files=bad_files, data=data_bad, headers=headers_telegram_secret)
    assert resp_bad.status_code == 400
    assert "Invalid file extension" in resp_bad.json()["detail"]
    logger.info("✓ Test 3 Passed: Invalid file extension rejected with 400.")

    # TEST 4: GET /api/medical-records/patient/{patient_id}
    logger.info("Test 4: Fetching patient medical records...")
    resp_list = client.get(f"/api/medical-records/patient/{patient_db_id}", headers=headers_doc)
    assert resp_list.status_code == 200
    records_list = resp_list.json()
    assert len(records_list) >= 2
    logger.info(f"✓ Test 4 Passed: Retrived {len(records_list)} medical records for patient.")

    # TEST 5: TASK 2 Verification — Server-side record_type default to 'other' when omitted
    logger.info("Test 5: Verifying record_type defaults to 'other' when omitted or invalid...")
    photo_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01 Mock JPEG Photo Content"
    files_no_type = {"file": ("file_0", io.BytesIO(photo_bytes), "image/jpeg")}
    data_no_type = {
        "patient_identifier": patient_profile_id,
        "title": "Unspecified Photo Document"
    }
    resp_no_type = client.post("/api/medical-records/upload", files=files_no_type, data=data_no_type, headers=headers_telegram_secret)
    assert resp_no_type.status_code == 200
    rec_no_type = resp_no_type.json()
    assert rec_no_type["record_type"] == "other", f"Expected record_type 'other', got '{rec_no_type['record_type']}'"
    logger.info("✓ Test 5 Passed: Server-side record_type correctly defaulted to 'other'.")

    # TEST 6: TASK 5 Verification A — Request with missing X-Telegram-Secret (and no user JWT) MUST return 401
    logger.info("Test 6: Verifying request with missing secret returns 401 Unauthorized...")
    files_unauth = {"file": ("test.pdf", io.BytesIO(mock_pdf_content), "application/pdf")}
    data_unauth = {"patient_identifier": patient_db_id, "title": "Unauth Test"}
    resp_unauth = client.post("/api/medical-records/upload", files=files_unauth, data=data_unauth)
    assert resp_unauth.status_code == 401, f"Expected 401, got {resp_unauth.status_code}"
    logger.info("✓ Test 6 Passed: Request with missing secret correctly returned 401.")

    # TEST 7: TASK 5 Verification B — Request with n8n_token Bearer alone MUST return 401
    logger.info("Test 7: Verifying request with n8n_token Bearer header alone returns 401 Unauthorized...")
    n8n_token = create_n8n_context_token(patient_profile_id, "patient", "H001")
    headers_n8n_bearer = {"Authorization": f"Bearer {n8n_token}"}
    files_bearer = {"file": ("test.pdf", io.BytesIO(mock_pdf_content), "application/pdf")}
    data_bearer = {"patient_identifier": patient_db_id, "title": "n8n Bearer Test"}
    resp_bearer = client.post("/api/medical-records/upload", files=files_bearer, data=data_bearer, headers=headers_n8n_bearer)
    assert resp_bearer.status_code == 401, f"Expected 401 for n8n Bearer token, got {resp_bearer.status_code}"
    logger.info("✓ Test 7 Passed: n8n_token Bearer header alone correctly returned 401.")

    # TEST 8: Invalid X-Telegram-Secret header MUST return 401
    logger.info("Test 8: Verifying request with invalid X-Telegram-Secret returns 401...")
    headers_wrong_secret = {"X-Telegram-Secret": "wrong-secret-key"}
    resp_wrong = client.post("/api/medical-records/upload", files=files_unauth, data=data_unauth, headers=headers_wrong_secret)
    assert resp_wrong.status_code == 401
    logger.info("✓ Test 8 Passed: Invalid X-Telegram-Secret returned 401.")

    logger.info("=" * 60)
    logger.info("ALL CONSOLIDATED VERIFICATION TESTS PASSED SUCCESSFULLY!")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_tests()
