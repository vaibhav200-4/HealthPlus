import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.database.supabase_client import SupabaseService
from app.services.patient_service import PatientService
from app.agent.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("hospital_app.summary")

def _parse_ts(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        s = str(ts_str).replace("Z", "+00:00")
        if "." in s:
            parts = s.split(".")
            dot_part = parts[1]
            tz_split = dot_part.split("+") if "+" in dot_part else dot_part.split("-")
            frac = tz_split[0]
            tz = dot_part[len(frac):]
            if len(frac) not in (3, 6):
                frac = frac.ljust(6, "0")[:6]
                s = f"{parts[0]}.{frac}{tz}"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{ts_str}': {e}")
        return None

class SummaryService:
    @staticmethod
    def generate_patient_summary(patient_id_or_ref: str) -> Dict[str, Any]:
        """
        Generates or fetches cached clinical patient summary for doctors.
        Uses MAX(created_at) caching across patient_intake_notes, medical_records,
        appointments, and chat_messages.
        """
        # Resolve patient record & candidate IDs
        patient = PatientService.resolve_patient(patient_id_or_ref)
        patient_id = patient.get("id")
        profile_id = patient.get("profile_id")

        candidate_ids = set(filter(None, [patient_id, profile_id, patient_id_or_ref]))

        # 1. Fetch source data across candidate IDs
        intake_notes = []
        seen_intake = set()
        for cid in candidate_ids:
            for item in SupabaseService.get_records("patient_intake_notes", {"patient_id": cid}):
                if item.get("id") and item["id"] not in seen_intake:
                    seen_intake.add(item["id"])
                    intake_notes.append(item)

        medical_records = []
        seen_records = set()
        for cid in candidate_ids:
            for item in SupabaseService.get_records("medical_records", {"patient_id": cid}):
                if item.get("id") and item["id"] not in seen_records:
                    seen_records.add(item["id"])
                    medical_records.append(item)

        appointments = []
        seen_apps = set()
        for cid in candidate_ids:
            for item in SupabaseService.get_records("appointments", {"user_id": cid}):
                if item.get("id") and item["id"] not in seen_apps:
                    seen_apps.add(item["id"])
                    appointments.append(item)

        all_chat_messages = []
        seen_chats = set()
        for cid in candidate_ids:
            chats = SupabaseService.get_records("chat_messages", {"user_id": cid})
            for c in chats:
                if c.get("id") and c["id"] not in seen_chats:
                    seen_chats.add(c["id"])
                    all_chat_messages.append(c)

        # Sort chat messages by created_at desc and take recent window (30 messages)
        all_chat_messages.sort(
            key=lambda x: x.get("created_at") or "",
            reverse=True
        )
        recent_30_chats = all_chat_messages[:30]

        # Calculate max created_at timestamp across ALL UNFILTERED sources
        max_source_ts = None
        for item in intake_notes + medical_records + appointments + recent_30_chats:
            ts_str = item.get("created_at") or item.get("generated_at")
            dt = _parse_ts(ts_str)
            if dt:
                if max_source_ts is None or dt > max_source_ts:
                    max_source_ts = dt

        # 2. Cache check in patient_summaries table
        cached_summaries = []
        seen_sum = set()
        for cid in candidate_ids:
            sums = SupabaseService.get_records("patient_summaries", {"patient_id": cid})
            for s in sums:
                if s.get("id") and s["id"] not in seen_sum:
                    seen_sum.add(s["id"])
                    cached_summaries.append(s)

        cached_summaries.sort(
            key=lambda x: x.get("generated_at") or "",
            reverse=True
        )
        if cached_summaries:
            latest_summary = cached_summaries[0]
            gen_ts_str = latest_summary.get("generated_at")
            gen_dt = _parse_ts(gen_ts_str)
            if gen_dt and max_source_ts:
                if gen_dt >= max_source_ts:
                    logger.info(f"Returning cached summary for patient {patient_id}")
                    return {
                        "summary": latest_summary.get("summary_text"),
                        "cached": True,
                        "generated_at": gen_ts_str
                    }
            elif not max_source_ts and latest_summary:
                return {
                    "summary": latest_summary.get("summary_text"),
                    "cached": True,
                    "generated_at": gen_ts_str
                }

        # 3. Filter chat messages for LLM prompt (exclude purely logistical/conversational noise)
        def is_purely_logistical(msg: str) -> bool:
            if not msg:
                return True
            cleaned = msg.strip().lower()

            # 1. Standalone pure greetings & simple acknowledgments
            pure_greetings = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "bye", "goodbye", "sure"}
            if cleaned in pure_greetings:
                return True

            # 2. Clinical symptom / health complaint indicators
            symptom_keywords = {
                "pain", "fever", "cough", "tightness", "headache", "swelling", "bleed", "bleeding",
                "vomit", "nausea", "dizzy", "dizziness", "rash", "infection", "fracture", "injury",
                "hurt", "hurts", "sick", "chest", "stomach", "symptom", "symptoms", "breath",
                "breathing", "cramps", "ache", "aches", "sore", "diarrhea", "fatigue", "chills"
            }
            has_symptom = any(kw in cleaned for kw in symptom_keywords)

            # 3. Booking / Scheduling / Administrative intent phrases
            booking_phrases = [
                "book appointment", "book an appointment", "schedule appointment", "schedule an appointment",
                "cancel appointment", "reschedule", "appointment for", "appointment on", "appointment at",
                "want an appointment", "need an appointment", "available slot", "time slot", "doctor list",
                "which doctor", "payment", "qr code", "upi", "pay now", "view appointment", "my appointment"
            ]
            has_booking_intent = any(bp in cleaned for bp in booking_phrases)

            if has_booking_intent and not has_symptom:
                return True

            return False

        filtered_chats = [
            {"role": c.get("role"), "message": c.get("message"), "created_at": c.get("created_at")}
            for c in recent_30_chats
            if not is_purely_logistical(c.get("message", ""))
        ]
        filtered_chats.reverse()  # Restore chronological order for prompt

        # 4. Cache miss: Synthesize new summary via LLM
        prompt_content = (
            f"Patient Profile: {patient}\n"
            f"Intake Notes ({len(intake_notes)}): {intake_notes}\n"
            f"Medical Records ({len(medical_records)}): {medical_records}\n"
            f"Appointments ({len(appointments)}): {appointments}\n"
            f"Patient Chat Conversations (Patient-Reported, {len(filtered_chats)} messages): {filtered_chats}\n\n"
            "Synthesize a clear, structured clinical summary for attending doctors. Follow these MANDATORY clinical rules:\n"
            "1. UNVERIFIED PATIENT-REPORTED FRAMING: Any information from patient chat conversations MUST be explicitly labeled as 'Patient-reported' or 'Patient stated' (e.g. under Chief Complaint & Symptoms: 'Patient reported mild tightness in chest'). NEVER upgrade unverified chat statements into confirmed medical diagnoses, lab findings, or prescribed medications.\n"
            "2. DISTINCT SOURCES: Keep documented medical records/lab findings (verified clinical records) clearly distinct from patient chat statements (patient-reported symptoms).\n"
            "3. NO INVENTED DATA: Do not invent symptoms, diagnoses, or treatments. If any field or section has no source data available, state 'Not available.'\n\n"
            "Include the following sections:\n"
            "- Patient Overview\n"
            "- Chief Complaint & Symptoms (Combine intake notes + patient-reported chat statements, clearly labeled)\n"
            "- Relevant Medical History\n"
            "- Key Medical Findings (From medical records only)\n"
            "- Recent Activity & Appointments\n"
            "- Important Information / Actionable Next Steps"
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
            summary_text = summary_text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
        except Exception as e:
            logger.error(f"Error calling LLM for patient summary: {e}")
            summary_text = (
                f"Summary synthesized from {len(intake_notes)} intake note(s), "
                f"{len(medical_records)} record(s), {len(appointments)} appointment(s), "
                f"and {len(filtered_chats)} patient-reported chat message(s)."
            )

        now_str = datetime.now(timezone.utc).isoformat()
        summary_record = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "summary_text": summary_text,
            "generated_at": now_str,
            "source_intake_count": len(intake_notes),
            "source_record_count": len(medical_records),
            "source_appointment_count": len(appointments),
            "source_chat_count": len(filtered_chats)
        }

        SupabaseService.insert_record("patient_summaries", summary_record)
        return {
            "summary": summary_text,
            "cached": False,
            "generated_at": now_str
        }
