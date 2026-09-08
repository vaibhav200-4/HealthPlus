import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger("hospital_app.voice")

router = APIRouter(prefix="/api/voice", tags=["Voice Agent"])

@router.get("/config", response_model=Dict[str, Any])
def get_voice_config():
    """Return voice agent service status and telephony number."""
    return {
        "groq_configured": bool(settings.GROQ_API_KEY),
        "sarvam_configured": bool(settings.SARVAM_API_KEY),
        "cartesia_configured": bool(settings.CARTESIA_API_KEY),
        "telephony_virtual_number": settings.TELEPHONY_VIRTUAL_NUMBER,
        "telephony_port": settings.TELEPHONY_WS_PORT,
        "active": bool(settings.GROQ_API_KEY and settings.SARVAM_API_KEY and settings.CARTESIA_API_KEY)
    }

@router.get("/telephony-info", response_model=Dict[str, Any])
def get_telephony_info():
    """Get active telephone number for voice agent phone calls."""
    return {
        "phone_number": settings.TELEPHONY_VIRTUAL_NUMBER,
        "display_number": settings.TELEPHONY_VIRTUAL_NUMBER,
        "status": "online",
        "supported_languages": ["English", "Hindi"],
        "description": "Call our 24/7 AI Voice Assistant directly from any phone to inquire about doctors, schedules, or book appointments."
    }

@router.post("/session", response_model=Dict[str, Any])
def create_voice_session():
    """Create a browser voice interaction session."""
    session_id = str(uuid.uuid4())
    return {
        "success": True,
        "session_id": session_id,
        "ws_url": f"/api/voice/ws/{session_id}",
        "telephony_number": settings.TELEPHONY_VIRTUAL_NUMBER
    }

def _rule_based_intent(text: str) -> dict:
    t = text.lower().strip()

    from processor.hospital_handler import _normalize_hospital
    resolved_h = _normalize_hospital(text)
    if resolved_h:
        # If user explicitly specifies a hospital name (e.g. "Sunrise Multi Speciality Hospital"), it is hospital selection!
        return {"intent": "book_appointment", "hospital_name": resolved_h}

    # 1. Hospital inquiry check MUST only trigger for explicit listing questions/requests, NOT plain hospital names
    if any(k in t for k in ["list hospital", "list hospitals", "which hospital", "which hospitals", "available hospital", "available hospitals", "show hospital", "show hospitals", "what hospital", "what hospitals", "all hospitals", "hospitals available"]):
        if not any(k in t for k in ["book", "appointment", "doctor", "dr.", "dr ", "cardiolog", "dermatolog", "ortho", "gynaec", "gynec", "gastro", "pediatr", "neurol", "psychiat", "pulmon"]):
            return {"intent": "list_hospitals"}

    # 2. Check for doctor listing intent FIRST if user asks about doctors in general or available doctors
    if any(k in t for k in ["which doctor", "which doctors", "what doctor", "what doctors", "available doctor", "available doctors", "doctors are available", "doctors available", "list doctor", "list doctors", "show doctor", "show doctors", "all doctors"]):
        return {"intent": "list_doctors"}

    # 3. General availability query for a specific doctor/slot
    if any(k in t for k in ["availab", "free slot", "free time", "slot"]):
        if not any(k in t for k in ["hospital", "hospitals"]):
            return {"intent": "check_availability"}

    # 3. Booking intent
    if any(k in t for k in ["book", "appointment", "schedule"]):
        return {"intent": "book_appointment"}

    # 4. Specialty / Navigation intent
    if any(k in t for k in ["cardio", "derma", "ortho", "gynaec", "gynec", "gastro", "pediatr", "neurol", "psychiat", "pulmon", "medicine", "physician", "doctor"]):
        return {"intent": "patient_navigation"}

    # 5. List doctors
    if any(k in t for k in ["which doctor", "available doctor", "list doctor", "doctors", "find doctor"]):
        return {"intent": "list_doctors"}

    # 6. Cancellation / Check
    if any(k in t for k in ["cancel"]):
        return {"intent": "cancel_appointment"}
    if any(k in t for k in ["check appointment", "my appointment", "status"]):
        return {"intent": "check_appointment"}

    # 7. Greetings
    if any(k in t for k in ["hi", "hello", "hey", "namaste", "good morning", "good afternoon", "good evening"]):
        return {"intent": "greeting"}

    return {"intent": "unknown"}


def _extract_voice_entities(text: str) -> dict:
    """Extract booking entities locally when the LLM is unavailable or vague."""
    import re
    from datetime import datetime, timedelta
    from processor.hospital_db import get_all_specializations, get_doctors

    lower_text = text.lower()
    entities = {}

    # Match the longest known doctor name inside a natural sentence.
    doctor_matches = []
    for doctor in get_doctors():
        name = str(doctor[0])
        clean_name = re.sub(r"^dr\.?\s*", "", name, flags=re.I).strip()
        if clean_name.lower() in lower_text:
            doctor_matches.append((len(clean_name), name))
    if doctor_matches:
        entities["doctor_name"] = max(doctor_matches)[1]

    from processor.hospital_handler import _normalize_specialization
    norm_spec = _normalize_specialization(text)
    if norm_spec:
        entities["specialization"] = norm_spec
    else:
        for specialization in get_all_specializations():
            if str(specialization).lower() in lower_text:
                entities["specialization"] = specialization
                break

    time_match = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b",
        text,
        re.I,
    )
    if time_match:
        entities["appointment_time"] = re.sub(
            r"([ap])\.m\.", r"\1m", time_match.group(0), flags=re.I
        )

    if "day after tomorrow" in lower_text:
        entities["appointment_date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    elif "tomorrow" in lower_text:
        entities["appointment_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "today" in lower_text:
        entities["appointment_date"] = datetime.now().strftime("%Y-%m-%d")
    else:
        date_match = re.search(
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)|"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}|"
            r"\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            text,
            re.I,
        )
        if date_match:
            entities["appointment_date"] = date_match.group(0)

    return entities

@router.websocket("/ws/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket pipeline endpoint for live browser audio/text communication.
    Handles user inputs and returns voice agent responses and state.
    """
    await websocket.accept()
    logger.info(f"Voice WebSocket client connected for session: {session_id}")
    
    try:
        import sys
        import os
        import asyncio
        ai_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_voice_agent"))
        if ai_agent_dir not in sys.path:
            sys.path.insert(0, ai_agent_dir)
            
        from processor.hospital_handler import HospitalHandler
        
        handler = HospitalHandler()
        llm = None
        if settings.GROQ_API_KEY and "your-groq-api-key" not in settings.GROQ_API_KEY:
            try:
                from processor.llm import GroqLLM
                llm = GroqLLM()
            except Exception as llm_err:
                logger.warning(f"Could not load GroqLLM: {llm_err}. Using rule-based fallback processor.")
                llm = None

        # Send initial greeting
        initial_msg = (
            "Hello! I am Aradhya Mishra, your HealthPlus hospital assistant. "
            "I can help you with doctor availability, hospital details, and appointment bookings. How can I help you today?"
        )
        await websocket.send_json({
            "type": "bot_text",
            "text": initial_msg,
            "voice_id": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
            "session_id": session_id
        })

        while True:
            data = await websocket.receive_json()
            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            logger.info(f"[WS Voice {session_id}] User text: {user_text}")

            intent_data = None
            if llm:
                try:
                    # Timeout after 3.5s to allow Groq LLM API responses to complete reliably
                    intent_data = await asyncio.wait_for(llm.extract_intent(user_text, handler.state), timeout=3.5)
                    # If LLM returned "unrelated" or empty intent, override with rule-based
                    if not intent_data or intent_data.get("intent") in ("unrelated", "unknown", None, ""):
                        logger.info(f"[WS Voice {session_id}] LLM returned '{intent_data}', falling back to rule-based.")
                        rule_intent = _rule_based_intent(user_text)
                        if intent_data:
                            intent_data["intent"] = rule_intent["intent"]
                        else:
                            intent_data = rule_intent
                except Exception as ex:
                    logger.exception(f"LLM intent extraction failed or timed out: {ex}. Using rule-based intent fallback.")
                    intent_data = _rule_based_intent(user_text)
            else:
                intent_data = _rule_based_intent(user_text)

            local_entities = _extract_voice_entities(user_text)
            for key, value in local_entities.items():
                if value and not intent_data.get(key):
                    intent_data[key] = value

            if handler.current_intent == "book_appointment" and handler.patient_name and not handler.phone:
                from processor.llm import normalize_phone
                phone_digits = normalize_phone(user_text)
                if phone_digits:
                    intent_data["phone"] = phone_digits

            # A direct availability question should be answered immediately,
            # while a booking request should continue through the booking flow.
            availability_words = ("available", "availability", "free slot", "free time")
            is_availability_query = (
                any(word in user_text.lower() for word in availability_words)
                and not any(word in user_text.lower() for word in ("book", "appointment", "schedule"))
                and intent_data.get("doctor_name")
                and intent_data.get("appointment_date")
                and intent_data.get("appointment_time")
            )
            if is_availability_query:
                intent_data["intent"] = "check_availability"
            
            # CRITICAL: If we are in an active booking flow and got a generic intent
            # (like "greeting" because no keyword matched), preserve the flow intent
            # and try to use the user text as the next expected entity.
            if handler.current_intent in ("book_appointment", "cancel_appointment", "check_appointment"):
                if intent_data.get("intent") in ("greeting", "unrelated", "unknown"):
                    # Check if intent_data already has useful entities from the LLM
                    has_entity = any(
                        intent_data.get(k) and str(intent_data.get(k)).lower() not in ("none", "null", "")
                        for k in ["doctor_name", "hospital_name", "appointment_date", "appointment_time", "patient_name", "phone", "address"]
                    )
                    if not has_entity:
                        # Try to intelligently extract the next needed entity from raw text
                        entity_extracted = False
                        
                        # 1. Try doctor name (if doctor not yet set)
                        if not handler.doctor_name:
                            from processor.hospital_handler import _resolve_doctor
                            doc = _resolve_doctor(user_text, handler.hospital_name)
                            if doc:
                                intent_data["doctor_name"] = doc[1]
                                entity_extracted = True
                                logger.info(f"[WS Voice {session_id}] Resolved doctor: {doc[1]}")
                        
                        # 2. Try hospital name (if hospital not yet set)
                        if not entity_extracted and not handler.hospital_name:
                            from processor.hospital_handler import _normalize_hospital
                            hosp = _normalize_hospital(user_text)
                            if hosp:
                                intent_data["hospital_name"] = hosp
                                entity_extracted = True
                                logger.info(f"[WS Voice {session_id}] Resolved hospital: {hosp}")
                        
                        # 3. Try date/time (if doctor is set but date/time not yet set)
                        if not entity_extracted and handler.doctor_name and (not handler.appointment_date or not handler.appointment_time):
                            import re
                            from datetime import datetime, timedelta
                            text_lower = user_text.lower().strip()
                            
                            # Parse time like "10 AM", "10:00 AM", "3 PM"
                            time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)(?!\w)', user_text, re.I)
                            time_str = None
                            if time_match:
                                time_str = time_match.group(0).strip()
                                time_str = re.sub(r'([ap])\.m\.', r'\1m', time_str, flags=re.I)
                            
                            # Parse date: "tomorrow", "day after tomorrow", explicit dates
                            date_str = None
                            if "tomorrow" in text_lower:
                                if "day after" in text_lower:
                                    date_str = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                                else:
                                    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                            elif "today" in text_lower:
                                date_str = datetime.now().strftime("%Y-%m-%d")
                            else:
                                # Try to parse explicit dates like "7 September", "September 7", "2026-09-07"
                                date_patterns = [
                                    r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)',
                                    r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
                                    r'(\d{4}-\d{2}-\d{2})',
                                    r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',
                                ]
                                for pat in date_patterns:
                                    dm = re.search(pat, text_lower)
                                    if dm:
                                        # Remove the time part from the text to get the date portion
                                        date_text = user_text
                                        if time_match:
                                            date_text = user_text[:time_match.start()] + user_text[time_match.end():]
                                        date_str = date_text.strip().rstrip('.,;:')
                                        if not date_str and dm:
                                            date_str = dm.group(0)
                                        break
                            
                            if date_str or time_str:
                                if date_str:
                                    intent_data["appointment_date"] = date_str
                                if time_str:
                                    intent_data["appointment_time"] = time_str
                                entity_extracted = True
                                logger.info(f"[WS Voice {session_id}] Parsed date={date_str}, time={time_str}")
                        
                        # 4. Try patient details (if doctor + date/time set)
                        if not entity_extracted and handler.doctor_name and handler.appointment_date and handler.appointment_time:
                            from processor.llm import normalize_phone
                            text_clean = user_text.strip()
                            if not handler.patient_name:
                                intent_data["patient_name"] = text_clean
                                entity_extracted = True
                            elif not handler.phone:
                                digits = normalize_phone(text_clean)
                                if digits:
                                    # Keep partial chunks; HospitalHandler combines them.
                                    intent_data["phone"] = digits
                                    entity_extracted = True
                            elif not handler.address:
                                intent_data["address"] = text_clean
                                entity_extracted = True
                    
                    # Always preserve the booking flow intent
                    intent_data["intent"] = handler.current_intent
            
            logger.info(f"[WS Voice {session_id}] Final intent: {intent_data}")

            response_text = handler.process_intent(intent_data, user_text)
            
            should_end = "[END_CALL]" in response_text
            clean_response = response_text.replace("[END_CALL]", "").strip()

            await websocket.send_json({
                "type": "bot_text",
                "text": clean_response,
                "voice_id": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
                "intent": intent_data.get("intent"),
                "end_call": should_end,
                "state": handler.state
            })

            if should_end:
                break

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in Voice WebSocket session {session_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "Voice processing error"})
        except Exception:
            pass
        finally:
            await websocket.close()
