# backend/app/api/voice.py
import re
import uuid
import sys
import os
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger("hospital_app.voice")

# Ensure ai_voice_agent directory is on sys.path for module resolution
ai_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_voice_agent"))
if ai_agent_dir not in sys.path:
    sys.path.insert(0, ai_agent_dir)

router = APIRouter(prefix="/api/voice", tags=["Voice Agent"])

@router.get("/config", response_model=Dict[str, Any])
def get_voice_config():
    """Browser voice status. Speech-to-text and text-to-speech run in the browser."""
    groq_ok = bool(getattr(settings, "GROQ_API_KEY", None))
    return {"mode": "browser", "groq_configured": groq_ok, "active": groq_ok}


@router.post("/session", response_model=Dict[str, Any])
def create_voice_session(request: Request = None):
    """Create a browser voice session.

    If an Authorization: Bearer <token> header is provided, the real user_id is resolved so
    voice-booked appointments appear under the logged-in user's account.
    """
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000001"  # anonymous fallback

    if request:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                from app.auth.auth_handler import decode_access_token
                payload = decode_access_token(token)
                if payload and payload.get("user_id"):
                    user_id = payload["user_id"]
            except Exception as e:
                logger.warning(f"Could not decode token in create_voice_session: {e}")

    return {
        "success": True,
        "session_id": session_id,
        "ws_url": f"/api/voice/ws/{session_id}",
        "user_id": user_id,
    }

def _rule_based_intent(text: str) -> dict:
    t = text.lower().strip()

    # PRIORITY -1: Explicit Cancellation intent MUST override any doctor/hospital name match
    if any(k in t for k in ["cancel", "cancellation", "delete appointment", "delete booking", "remove appointment"]):
        return {"intent": "cancel_appointment"}

    # PRIORITY 0: Check if the text resolves to a known hospital in our DB *first*.
    try:
        from processor.hospital_handler import _normalize_hospital
        resolved_h = _normalize_hospital(text)
        if resolved_h:
            return {"intent": "book_appointment", "hospital_name": resolved_h}
    except Exception as _e:
        logger.warning(f"Hospital normalization failed: {_e}")

    # 0. Dynamic location-based nearby search rule.
    # Only fires when the matched location is NOT a known DB hospital (checked above).
    location_triggers = ["near me", "nearby", "near by", "around me", "close to me"]
    is_location = any(lt in t for lt in location_triggers)
    city_match = re.search(r'\b(?:in|at|around|near)\s+([a-zA-Z\s]{3,20})\b', t)
    if not is_location and city_match:
        c_name = city_match.group(1).strip().lower()
        if c_name not in ("the hospital", "the clinic", "the morning", "the evening", "my area", "our hospital"):
            is_location = True

    if is_location and any(k in t for k in ["hospital", "hospitals", "doctor", "doctors", "clinic", "clinics", "specialist", "specialists"]):
        loc_val = "near_me"
        if city_match:
            loc_val = city_match.group(1).strip()
        return {"intent": "nearby_search", "location_query": loc_val}

    # 0.5 Check for user asking about their own appointments / bookings (my_appointments)
    my_app_patterns = [
        r"\bmy (?:appointments|bookings|previous appointments|upcoming appointments|past appointments)\b",
        r"\b(?:what|check|view|show|list) (?:my )?(?:appointments|bookings)\b",
        r"\b(?:do i have|any) (?:upcoming|past|previous)?\s*(?:appointments|bookings)\b",
        r"\bmy (?:previous|upcoming|past) (?:bookings|appointments)\b",
        r"\bshow my (?:bookings|appointments)\b"
    ]
    if any(re.search(pat, t) for pat in my_app_patterns):
        return {"intent": "my_appointments"}

    # 1. Hospital inquiry check MUST trigger for explicit listing questions/requests
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

    # 4. Booking intent
    if any(k in t for k in ["book", "appointment", "schedule"]):
        return {"intent": "book_appointment"}

    # 5. Specialty / Navigation intent
    if any(k in t for k in ["cardio", "derma", "ortho", "gynaec", "gynec", "gastro", "pediatr", "neurol", "psychiat", "pulmon", "medicine", "physician", "doctor"]):
        return {"intent": "patient_navigation"}

    # 6. List doctors
    if any(k in t for k in ["which doctor", "available doctor", "list doctor", "doctors", "find doctor"]):
        return {"intent": "list_doctors"}

    # 7. Cancellation / Check
    if any(k in t for k in ["cancel"]):
        return {"intent": "cancel_appointment"}
    if any(k in t for k in ["check appointment", "my appointment", "status"]):
        return {"intent": "check_appointment"}

    # 8. Greetings
    greeting_words = [r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bnamaste\b", r"\bgood morning\b", r"\bgood afternoon\b", r"\bgood evening\b"]
    greeting_phrases = ["who are you", "what can you do", "tell me about yourself", "about you"]
    
    if any(re.search(pat, t) for pat in greeting_words) or any(k in t for k in greeting_phrases):
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

ANON_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.websocket("/ws/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str, token: str = ""):
    # user_id comes ONLY from a verified token. A client-supplied user_id is never trusted.
    user_id = ANON_USER_ID
    if token:
        try:
            from app.auth.auth_handler import decode_access_token
            payload = decode_access_token(token)
            if payload and payload.get("user_id"):
                user_id = payload["user_id"]
        except Exception as _e:
            logger.warning(f"Could not resolve user_id from token: {_e}")

    await websocket.accept()
    logger.info(f"Voice WebSocket connected: session={session_id} authenticated={user_id != ANON_USER_ID}")
    
    try:
        import sys
        import os
        import asyncio
        ai_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_voice_agent"))
        if ai_agent_dir not in sys.path:
            sys.path.insert(0, ai_agent_dir)
            
        from pipecat_web_pipeline import create_pipecat_web_session

        # Create Pipecat Web Session with Silero VAD and TurnManager
        processor = await create_pipecat_web_session(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id
        )

        while True:
            data = await websocket.receive_json()
            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            logger.info(f"[WS Pipecat {session_id}] User text: {user_text}")
            await processor.process_user_text(user_text)

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket client disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in voice WebSocket session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": "Voice processing error"})
        except Exception:
            pass
