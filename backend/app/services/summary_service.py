import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

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

def _is_purely_logistical(msg: str) -> bool:
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


class SummaryService:
    @staticmethod
    def generate_patient_summary(patient_id_or_ref: str) -> Dict[str, Any]:
        """
        Generates or fetches cached CROSS-EPISODE clinical patient summary for doctors.
        Provides a historical overview across all past and present episodes,
        patient intake notes, medical records, appointments, and chat messages.
        For current active episode-scoped summaries, use generate_episode_summary.
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
            ts_str = item.get("ocr_processed_at") or item.get("created_at") or item.get("generated_at")
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

        filtered_chats = [
            {"role": c.get("role"), "message": c.get("message"), "created_at": c.get("created_at")}
            for c in recent_30_chats
            if not _is_purely_logistical(c.get("message", ""))
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

        try:
            llm = get_llm()
            messages = [
                SystemMessage(content="You are an expert clinical medical summarizer. Synthesize doctor-facing patient summaries."),
                HumanMessage(content=prompt_content)
            ]
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

    @staticmethod
    def generate_episode_summary(episode_id: str, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Episode-scoped clinical summary combining OCR'd documents, patient-reported
        chat history, intake notes, and appointments — all bounded to this episode's
        time window. Cached against episodes.summary_generated_at vs the max source
        timestamp; pass force_regenerate=True to bypass the cache.
        """
        episode = SupabaseService.get_record_by_id("episodes", episode_id)
        if not episode:
            logger.error(f"Cannot generate episode summary: episode {episode_id} not found.")
            return {
                "episode_id": episode_id,
                "summary": "Episode not found",
                "cached": False,
                "generated_at": None,
                "source_record_count": 0
            }

        patient_id = episode.get("patient_id")
        condition = episode.get("condition", "General Health Care")
        status = episode.get("status", "active")
        started_at_str = episode.get("started_at")
        resolved_at_str = episode.get("resolved_at")

        start_dt = _parse_ts(started_at_str)
        end_dt = _parse_ts(resolved_at_str) if resolved_at_str else datetime.now(timezone.utc).replace(tzinfo=None)

        # Candidate patient IDs for fetching user-linked data
        patient_rec = PatientService.resolve_patient(patient_id) if patient_id else {}
        candidate_ids = set(filter(None, [patient_id, patient_rec.get("id"), patient_rec.get("profile_id")]))

        # 1. Episode-scoped OCR Medical Records (where episode_id == episode_id and ocr_status == 'completed')
        records = SupabaseService.get_records("medical_records", {"episode_id": episode_id})
        completed_records = [r for r in records if r.get("ocr_status") == "completed"]
        completed_records.sort(key=lambda x: x.get("ocr_processed_at") or x.get("created_at") or "")

        # 2. Episode-scoped Patient Chat Messages (bounded by started_at and resolved_at/now)
        all_chats = []
        seen_chats = set()
        for cid in candidate_ids:
            c_list = SupabaseService.get_records("chat_messages", {"user_id": cid})
            for c in c_list:
                if c.get("id") and c["id"] not in seen_chats:
                    seen_chats.add(c["id"])
                    c_dt = _parse_ts(c.get("created_at"))
                    if c_dt:
                        # Time window check
                        if start_dt and c_dt < start_dt:
                            continue
                        if end_dt and c_dt > end_dt:
                            continue
                        all_chats.append(c)

        # Filter out logistical messages and sort chronologically
        clinical_chats = [
            c for c in all_chats
            if not _is_purely_logistical(c.get("message", ""))
        ]
        clinical_chats.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        recent_episode_chats = clinical_chats[:30]
        recent_episode_chats.reverse()  # Restore chronological order for prompt

        # 3. Episode-scoped Patient Intake Notes (time-window filter as approximate boundary)
        intake_notes = []
        seen_intake = set()
        for cid in candidate_ids:
            notes = SupabaseService.get_records("patient_intake_notes", {"patient_id": cid})
            for n in notes:
                if n.get("id") and n["id"] not in seen_intake:
                    seen_intake.add(n["id"])
                    n_dt = _parse_ts(n.get("created_at"))
                    if n_dt:
                        if start_dt and n_dt < start_dt:
                            continue
                        if end_dt and n_dt > end_dt:
                            continue
                        intake_notes.append(n)

        # 4. Episode-scoped Appointments (time-window filter as approximate boundary)
        appointments = []
        seen_appts = set()
        for cid in candidate_ids:
            appts = SupabaseService.get_records("appointments", {"user_id": cid})
            for a in appts:
                if a.get("id") and a["id"] not in seen_appts:
                    seen_appts.add(a["id"])
                    a_dt = _parse_ts(a.get("created_at") or a.get("date"))
                    if a_dt:
                        if start_dt and a_dt < start_dt:
                            continue
                        if end_dt and a_dt > end_dt:
                            continue
                        appointments.append(a)

        # 5. Compute max_source_ts across all episode sources
        max_source_ts = None
        for r in completed_records:
            ts_str = r.get("ocr_processed_at") or r.get("created_at")
            dt = _parse_ts(ts_str)
            if dt and (max_source_ts is None or dt > max_source_ts):
                max_source_ts = dt

        for c in recent_episode_chats:
            dt = _parse_ts(c.get("created_at"))
            if dt and (max_source_ts is None or dt > max_source_ts):
                max_source_ts = dt

        for n in intake_notes:
            dt = _parse_ts(n.get("created_at"))
            if dt and (max_source_ts is None or dt > max_source_ts):
                max_source_ts = dt

        for a in appointments:
            dt = _parse_ts(a.get("created_at") or a.get("date"))
            if dt and (max_source_ts is None or dt > max_source_ts):
                max_source_ts = dt

        # 6. Lazy Cache Check: Compare episodes.summary_generated_at vs max_source_ts
        existing_summary = episode.get("summary")
        summary_gen_at = episode.get("summary_generated_at")
        gen_dt = _parse_ts(summary_gen_at)

        if not force_regenerate and existing_summary and gen_dt:
            if max_source_ts is None or gen_dt >= max_source_ts:
                logger.info(f"Returning cached summary for episode {episode_id}")
                return {
                    "episode_id": episode_id,
                    "summary": existing_summary,
                    "cached": True,
                    "generated_at": summary_gen_at,
                    "source_record_count": len(completed_records)
                }

        # 7. LLM Prompt Construction
        doc_texts = []
        source_record_ids = []
        for r in completed_records:
            source_record_ids.append(r["id"])
            text = r.get("extracted_text") or f"Document Title: {r.get('title')} ({r.get('record_type')})"
            doc_texts.append(f"--- Document ({r.get('title')} - {r.get('record_type')}) ---\n{text}")

        combined_docs = "\n\n".join(doc_texts) if doc_texts else "Not available."

        chat_texts = []
        for c in recent_episode_chats:
            role = "Patient" if c.get("role") in ["user", "patient"] else "Assistant/System"
            chat_texts.append(f"[{c.get('created_at') or 'Recent'}] {role}: {c.get('message')}")
        combined_chats = "\n".join(chat_texts) if chat_texts else "Not available."

        intake_texts = []
        for n in intake_notes:
            intake_texts.append(f"[{n.get('created_at') or 'N/A'}]: {n.get('symptoms') or n.get('notes') or n}")
        combined_intake = "\n".join(intake_texts) if intake_texts else "Not available."

        appt_texts = []
        for a in appointments:
            appt_texts.append(f"[{a.get('date') or a.get('created_at')}]: Hospital: {a.get('hospital_name', 'N/A')}, Status: {a.get('status', 'N/A')}, Notes: {a.get('notes', 'N/A')}")
        combined_appts = "\n".join(appt_texts) if appt_texts else "Not available."

        prompt_content = (
            f"Episode Condition: {condition}\n"
            f"Episode Status: {status}\n"
            f"Started At: {started_at_str or 'N/A'}\n"
            f"Resolved At: {resolved_at_str or 'Active (Ongoing)'}\n\n"
            f"--- 1. Verified OCR Medical Documents ({len(completed_records)} records) ---\n"
            f"{combined_docs}\n\n"
            f"--- 2. Patient-Reported Chat History ({len(recent_episode_chats)} messages) ---\n"
            f"{combined_chats}\n\n"
            f"--- 3. Intake Notes ({len(intake_notes)} notes) ---\n"
            f"{combined_intake}\n\n"
            f"--- 4. Episode Appointments ({len(appointments)} appointments) ---\n"
            f"{combined_appts}\n\n"
            "Synthesize a concise, structured clinical summary for attending doctors specifically for THIS episode of care. "
            "Follow these MANDATORY clinical guidelines:\n"
            "1. UNVERIFIED PATIENT-REPORTED FRAMING: Any information from patient chat conversations MUST be explicitly labeled as 'Patient-reported' or 'Patient stated' (e.g. under Chief Complaint & Symptoms: 'Patient reported mild tightness in chest'). NEVER upgrade patient chat statements into confirmed medical diagnoses, lab findings, or prescribed treatments.\n"
            "2. DISTINCT SOURCES: Keep documented medical records/lab findings (verified clinical records) clearly distinct from patient chat statements (patient-reported symptoms).\n"
            "3. NO INVENTED DATA: Do not invent symptoms, diagnoses, or treatments. If any section has no source data available, state 'Not available.'\n\n"
            "Include the following exact sections:\n"
            "- Episode Overview (Condition, Status, Started At, Resolved At)\n"
            "- Chief Complaint & Symptoms (Combine intake notes + patient-reported chat statements, clearly labeled as Patient-reported)\n"
            "- Key Medical Findings (From verified OCR medical records only)\n"
            "- Relevant Activity (Episode-scoped appointments)\n"
            "- Actionable Next Steps"
        )

        try:
            llm = get_llm()
            messages = [
                SystemMessage(content="You are an expert clinical summarizer. Synthesize episode-scoped doctor summaries."),
                HumanMessage(content=prompt_content)
            ]
            res = llm.invoke(messages)
            summary_text = getattr(res, "content", str(res))
            if isinstance(summary_text, list):
                summary_text = "\n".join([p.get("text", "") if isinstance(p, dict) else str(p) for p in summary_text])
            summary_text = summary_text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
        except Exception as e:
            logger.error(f"LLM call failed for episode summary {episode_id}: {e}")
            summary_text = (
                f"Episode summary for {condition} ({status}):\n"
                f"- Records: {len(completed_records)} OCR document(s)\n"
                f"- Patient Chat: {len(recent_episode_chats)} message(s) (Patient-reported)\n"
                f"- Intake Notes: {len(intake_notes)}\n"
                f"- Appointments: {len(appointments)}"
            )

        now_str = datetime.now(timezone.utc).isoformat()
        updates = {
            "summary": summary_text,
            "summary_generated_at": now_str,
            "summary_source_record_ids": source_record_ids,
            "updated_at": now_str
        }

        SupabaseService.update_record("episodes", episode_id, updates)
        logger.info(f"Generated unified episode-scoped summary for episode {episode_id}")
        return {
            "episode_id": episode_id,
            "summary": summary_text,
            "cached": False,
            "generated_at": now_str,
            "source_record_count": len(completed_records)
        }


