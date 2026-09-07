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
        ai_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_voice_agent"))
        if ai_agent_dir not in sys.path:
            sys.path.insert(0, ai_agent_dir)
            
        from processor.hospital_handler import HospitalHandler
        from processor.llm import GroqLLM
        
        handler = HospitalHandler()
        llm = GroqLLM() if settings.GROQ_API_KEY else None

        # Send initial greeting
        initial_msg = (
            "Hello! I am Aradhya Mishra, your HealthPlus hospital assistant. "
            "I can help you with doctor availability, hospital details, and appointment bookings. How can I help you today?"
        )
        await websocket.send_json({
            "type": "bot_text",
            "text": initial_msg,
            "session_id": session_id
        })

        while True:
            data = await websocket.receive_json()
            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            logger.info(f"[WS Voice {session_id}] User text: {user_text}")

            if llm:
                intent_data = await llm.extract_intent(user_text, handler.state)
            else:
                intent_data = {"intent": "greeting"}

            response_text = handler.process_intent(intent_data, user_text)
            
            should_end = "[END_CALL]" in response_text
            clean_response = response_text.replace("[END_CALL]", "").strip()

            await websocket.send_json({
                "type": "bot_text",
                "text": clean_response,
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
