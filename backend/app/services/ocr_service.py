import os
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from mistralai.client import Mistral
except ImportError:
    Mistral = None

from app.database.supabase_client import SupabaseService, get_supabase_client
from app.config import settings

logger = logging.getLogger("hospital_app.ocr")

MISTRAL_MODEL = "mistral-ocr-latest"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2


def _clean_text(text: str) -> str:
    """Lightweight cleanup — collapse excess blank lines/whitespace."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _run_mistral_ocr(file_path: Path) -> str:
    """
    Uploads a file to Mistral, runs OCR, returns combined cleaned text
    across all pages. Raises on failure after retries.
    """
    if Mistral is None:
        raise RuntimeError("mistralai package is not installed. Please install mistralai.")

    api_key = settings.MISTRAL_API_KEY
    if not api_key or "your-mistral" in api_key:
        raise ValueError("MISTRAL_API_KEY is not configured.")

    client = Mistral(api_key=api_key)

    uploaded = client.files.upload(
        file={"file_name": file_path.name, "content": file_path.read_bytes()},
        purpose="ocr",
    )
    signed = client.files.get_signed_url(file_id=uploaded.id, expiry=1)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.ocr.process(
                model=MISTRAL_MODEL,
                document={"type": "document_url", "document_url": signed.url},
                include_image_base64=False,
            )
            break
        except Exception as exc:
            last_error = exc
            wait = attempt * RETRY_BACKOFF_SECONDS
            logger.warning(f"OCR attempt {attempt}/{MAX_RETRIES} failed: {exc}")
            time.sleep(wait)
    else:
        raise last_error

    response_dict = response.model_dump()
    page_texts = []
    for page in response_dict.get("pages", []):
        text = _clean_text((page.get("markdown") or "").strip())
        if text:
            page_texts.append(text)

    return "\n\n".join(page_texts)


class OCRService:
    @staticmethod
    def process_record_ocr(record_id: str) -> bool:
        """
        Runs OCR on an uploaded medical record. Sets ocr_status to 'completed'
        ONLY when real extracted text is obtained — every other path sets
        'failed' explicitly. Never silently marks a failure as completed.
        """
        record = SupabaseService.get_record_by_id("medical_records", record_id)
        if not record:
            logger.error(f"OCR failed: medical record {record_id} not found.")
            return False

        file_url = record.get("file_url")
        file_type = (record.get("file_type") or "").lower()

        if not file_url:
            logger.warning(f"Medical record {record_id} has no file_url.")
            SupabaseService.update_record("medical_records", record_id, {
                "ocr_status": "failed",
                "ocr_processed_at": datetime.now(timezone.utc).isoformat(),
            })
            return False

        local_path: Optional[Path] = None
        temp_download = False

        try:
            if os.path.exists(file_url):
                local_path = Path(file_url)
            else:
                client = get_supabase_client()
                if client:
                    try:
                        res = client.storage.from_("medical-records").download(file_url)
                        if res:
                            os.makedirs("data/ocr_temp", exist_ok=True)
                            temp_path = Path(f"data/ocr_temp/{record_id}.{file_type or 'pdf'}")
                            with open(temp_path, "wb") as f:
                                f.write(res)
                            local_path = temp_path
                            temp_download = True
                    except Exception as storage_err:
                        logger.warning(f"Could not download from Supabase storage: {storage_err}")

            if not local_path or not local_path.exists():
                logger.error(f"No file available for OCR on record {record_id} ({file_url}).")
                SupabaseService.update_record("medical_records", record_id, {
                    "ocr_status": "failed",
                    "ocr_processed_at": datetime.now(timezone.utc).isoformat(),
                })
                return False

            try:
                extracted_text = _run_mistral_ocr(local_path)
            except Exception as mistral_err:
                logger.error(f"Mistral OCR extraction failed for record {record_id}: {mistral_err}")
                SupabaseService.update_record("medical_records", record_id, {
                    "ocr_status": "failed",
                    "ocr_processed_at": datetime.now(timezone.utc).isoformat(),
                })
                return False

            if not extracted_text.strip():
                logger.error(f"OCR returned no text for record {record_id}.")
                SupabaseService.update_record("medical_records", record_id, {
                    "ocr_status": "failed",
                    "ocr_processed_at": datetime.now(timezone.utc).isoformat(),
                })
                return False

            SupabaseService.update_record("medical_records", record_id, {
                "extracted_text": extracted_text,
                "ocr_status": "completed",
                "ocr_processed_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"OCR successfully completed for medical record {record_id}")
            return True

        finally:
            if temp_download and local_path and local_path.exists():
                try:
                    os.remove(local_path)
                except Exception:
                    pass