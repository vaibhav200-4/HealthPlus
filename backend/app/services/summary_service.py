import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.database.supabase_client import SupabaseService
from app.services.patient_service import PatientService
from app.agent.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("hospital_app.summary")

class SummaryService:
    @staticmethod
    def generate_patient_summary(patient_id_or_ref: str) -> Dict[str, Any]:
        """
        Generates or fetches cached clinical patient summary for doctors.
        Uses MAX(created_at) caching across patient_intake_notes, medical_records, and appointments.
        """
        # Resolve patient record
        patient = PatientService.resolve_patient(patient_id_or_ref)
        patient_id = patient.get("id")

        # 1. Fetch source data
        intake_notes = SupabaseService.get_records("patient_intake_notes", {"patient_id": patient_id})
        medical_records = SupabaseService.get_records("medical_records", {"patient_id": patient_id})
        appointments = SupabaseService.get_records("appointments", {"user_id": patient_id})

        # Calculate max created_at timestamp across sources
        max_source_ts = None
        for item in intake_notes + medical_records + appointments:
            ts_str = item.get("created_at") or item.get("generated_at")
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if max_source_ts is None or dt > max_source_ts:
                        max_source_ts = dt
                except Exception:
                    pass

        # 2. Cache check in patient_summaries table
        cached_summaries = SupabaseService.get_records("patient_summaries", {"patient_id": patient_id})
        if cached_summaries:
            latest_summary = cached_summaries[0]
            gen_ts_str = latest_summary.get("generated_at")
            if gen_ts_str and max_source_ts:
                try:
                    gen_dt = datetime.fromisoformat(gen_ts_str.replace("Z", "+00:00"))
                    if gen_dt >= max_source_ts:
                        logger.info(f"Returning cached summary for patient {patient_id}")
                        return {
                            "summary": latest_summary.get("summary_text"),
                            "cached": True,
                            "generated_at": gen_ts_str
                        }
                except Exception:
                    pass
            elif not max_source_ts and latest_summary:
                return {
                    "summary": latest_summary.get("summary_text"),
                    "cached": True,
                    "generated_at": gen_ts_str
                }

        # 3. Cache miss: Synthesize new summary via LLM
        prompt_content = (
            f"Patient Profile: {patient}\n"
            f"Intake Notes ({len(intake_notes)}): {intake_notes}\n"
            f"Medical Records ({len(medical_records)}): {medical_records}\n"
            f"Appointments ({len(appointments)}): {appointments}\n\n"
            "Synthesize a clear, structured clinical summary for attending doctors. Include:\n"
            "- Chief Complaint & Symptom History\n"
            "- Key Medical Record Findings\n"
            "- Upcoming/Recent Appointments & Status\n"
            "- Clinical Recommendations / Actionable Next Steps"
        )

        llm = get_llm()
        messages = [
            SystemMessage(content="You are an expert clinical medical summarizer. Synthesize doctor-facing patient summaries."),
            HumanMessage(content=prompt_content)
        ]
        
        try:
            res = llm.invoke(messages)
            summary_text = getattr(res, "content", str(res))
            if isinstance(summary_text, list):
                summary_text = "\n".join([p.get("text", "") if isinstance(p, dict) else str(p) for p in summary_text])
        except Exception as e:
            logger.error(f"Error calling LLM for patient summary: {e}")
            summary_text = f"Summary synthesized from {len(intake_notes)} intake note(s), {len(medical_records)} record(s), and {len(appointments)} appointment(s)."

        now_str = datetime.now().isoformat()
        summary_record = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "summary_text": summary_text,
            "generated_at": now_str,
            "source_intake_count": len(intake_notes),
            "source_record_count": len(medical_records),
            "source_appointment_count": len(appointments)
        }

        SupabaseService.insert_record("patient_summaries", summary_record)
        return {
            "summary": summary_text,
            "cached": False,
            "generated_at": now_str
        }
