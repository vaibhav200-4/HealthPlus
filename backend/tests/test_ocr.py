"""
Tests for OCRService.process_record_ocr

Covers the exact bug we just fixed: every failure path must set
ocr_status='failed' and return False — none should fall through to
'completed' with placeholder text.

Run with:
    pip install pytest --break-system-packages   # if not already installed
    pytest backend/tests/test_ocr_service.py -v
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.ocr_service import OCRService


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_record(**overrides):
    base = {
        "id": "rec-123",
        "file_url": "data/uploads/rec-123.png",
        "file_type": "png",
        "title": "Sugar Report",
        "record_type": "lab_result",
        "description": "uploaded clinical record",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Record not found
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service.SupabaseService")
def test_record_not_found_returns_false(mock_supabase):
    mock_supabase.get_record_by_id.return_value = None

    result = OCRService.process_record_ocr("missing-id")

    assert result is False
    mock_supabase.update_record.assert_not_called()


# ---------------------------------------------------------------------------
# 2. No file_url on the record
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service.SupabaseService")
def test_missing_file_url_marks_failed(mock_supabase):
    mock_supabase.get_record_by_id.return_value = make_record(file_url=None)

    result = OCRService.process_record_ocr("rec-123")

    assert result is False
    args, kwargs = mock_supabase.update_record.call_args
    assert args[0] == "medical_records"
    assert args[1] == "rec-123"
    assert args[2]["ocr_status"] == "failed"
    assert "extracted_text" not in args[2]  # no placeholder text written


# ---------------------------------------------------------------------------
# 3. File can't be found locally or in storage
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service.get_supabase_client")
@patch("app.services.ocr_service.SupabaseService")
@patch("app.services.ocr_service.os.path.exists", return_value=False)
def test_file_not_found_anywhere_marks_failed(mock_exists, mock_supabase, mock_get_client):
    mock_supabase.get_record_by_id.return_value = make_record()
    mock_get_client.return_value = None  # storage client unavailable

    result = OCRService.process_record_ocr("rec-123")

    assert result is False
    args, kwargs = mock_supabase.update_record.call_args
    assert args[2]["ocr_status"] == "failed"
    assert "extracted_text" not in args[2]


# ---------------------------------------------------------------------------
# 4. Mistral OCR raises an exception (e.g. the import bug, network error, etc.)
#    -> must NOT be marked completed
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service._run_mistral_ocr", side_effect=RuntimeError("cannot import name 'Mistral'"))
@patch("app.services.ocr_service.SupabaseService")
@patch("app.services.ocr_service.os.path.exists", return_value=True)
def test_mistral_exception_marks_failed_not_completed(mock_exists, mock_supabase, mock_ocr_call):
    mock_supabase.get_record_by_id.return_value = make_record()

    result = OCRService.process_record_ocr("rec-123")

    assert result is False
    args, kwargs = mock_supabase.update_record.call_args
    assert args[2]["ocr_status"] == "failed"
    # This is the exact regression we're guarding against:
    assert args[2].get("ocr_status") != "completed"
    assert "extracted_text" not in args[2]


# ---------------------------------------------------------------------------
# 5. Mistral OCR "succeeds" but returns empty/whitespace text
#    -> must still be marked failed, not completed with blank content
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service._run_mistral_ocr", return_value="   \n  ")
@patch("app.services.ocr_service.SupabaseService")
@patch("app.services.ocr_service.os.path.exists", return_value=True)
def test_empty_ocr_result_marks_failed(mock_exists, mock_supabase, mock_ocr_call):
    mock_supabase.get_record_by_id.return_value = make_record()

    result = OCRService.process_record_ocr("rec-123")

    assert result is False
    args, kwargs = mock_supabase.update_record.call_args
    assert args[2]["ocr_status"] == "failed"


# ---------------------------------------------------------------------------
# 6. Successful OCR -> completed, with real extracted text (not a placeholder)
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service._run_mistral_ocr", return_value="Blood glucose: 140 mg/dL, fasting.")
@patch("app.services.ocr_service.SupabaseService")
@patch("app.services.ocr_service.os.path.exists", return_value=True)
def test_successful_ocr_marks_completed_with_real_text(mock_exists, mock_supabase, mock_ocr_call):
    mock_supabase.get_record_by_id.return_value = make_record()

    result = OCRService.process_record_ocr("rec-123")

    assert result is True
    args, kwargs = mock_supabase.update_record.call_args
    assert args[2]["ocr_status"] == "completed"
    assert args[2]["extracted_text"] == "Blood glucose: 140 mg/dL, fasting."
    # Regression guard: make sure it's not the old placeholder pattern
    assert "Document Title:" not in args[2]["extracted_text"]
    assert "Medical Document Title:" not in args[2]["extracted_text"]


# ---------------------------------------------------------------------------
# 7. Download from Supabase storage fails -> failed, not a silent placeholder
# ---------------------------------------------------------------------------

@patch("app.services.ocr_service.get_supabase_client")
@patch("app.services.ocr_service.SupabaseService")
@patch("app.services.ocr_service.os.path.exists", return_value=False)
def test_storage_download_failure_marks_failed(mock_exists, mock_supabase, mock_get_client):
    mock_supabase.get_record_by_id.return_value = make_record()
    mock_client = MagicMock()
    mock_client.storage.from_.return_value.download.side_effect = Exception("network error")
    mock_get_client.return_value = mock_client

    result = OCRService.process_record_ocr("rec-123")

    assert result is False
    args, kwargs = mock_supabase.update_record.call_args
    assert args[2]["ocr_status"] == "failed"