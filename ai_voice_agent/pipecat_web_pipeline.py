# ai_voice_agent/pipecat_web_pipeline.py
import os
import sys
import uuid
import time
import json
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv

# Add processor path
agent_dir = os.path.abspath(os.path.dirname(__file__))
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from processor.hospital_handler import HospitalHandler
from processor.llm import GroqLLM
from processor.manager import TurnManager

logger = logging.getLogger("hospital_app.pipecat_web")

load_dotenv(override=True)


class WebPipecatProcessor:
    """
    Processor optimized for FastAPI WebSocket Web Clients.
    Combines TurnManager echo cancellation and HospitalHandler state routing.
    """
    def __init__(self, websocket, session_id: str, user_id: str, turn_manager: TurnManager, llm: Optional[GroqLLM] = None):
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id
        self.turn_manager = turn_manager
        self.llm = llm or GroqLLM()
        self.handler = HospitalHandler()
        self.handler.user_id = user_id
        self.greeted = False
        self._generation_task = None
        self.last_assistant_text = ""

    async def send_initial_greeting(self):
        """Sends the initial Aradhya voice assistant greeting frame."""
        if not self.greeted:
            self.greeted = True
            greeting = self.handler.generate_greeting()
            self.last_assistant_text = greeting
            if self.turn_manager:
                self.turn_manager.register_bot_reply(greeting)
            
            await self.websocket.send_json({
                "type": "bot_text",
                "text": greeting,
                "voice_id": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
                "session_id": self.session_id,
                "engine": "browser-stt-groq-tts-browser"
            })

    async def process_user_text(self, user_text: str):
        """Processes user input text through TurnManager echo filters and GroqLLM."""
        user_text = user_text.strip()
        if not user_text:
            return

        # ── TurnManager Echo Filter ──────────────────────────────────────────────
        last_bot = getattr(self, "last_assistant_text", "")
        if last_bot and len(user_text.split()) > 2:
            from processor.manager import _token_overlap_ratio, _ECHO_OVERLAP_THRESHOLD
            overlap = _token_overlap_ratio(user_text, last_bot)
            if overlap >= _ECHO_OVERLAP_THRESHOLD:
                logger.info(f"[ECHO CANCEL] Dropped echo overlap ({overlap:.2f}): {user_text!r}")
                return

        request_start = time.perf_counter()
        logger.info(f"[PIPECAT USER] session={self.session_id}: {user_text!r}")

        if self._generation_task and not self._generation_task.done():
            self._generation_task.cancel()

        self._generation_task = asyncio.create_task(
            self._generate_response(user_text, request_start)
        )

    async def _generate_response(self, user_text: str, request_start: float):
        try:
            # 1. Fast Rule-Based Intent Matching
            intent_data = None
            if self.handler.current_intent == "nearby_search":
                intent_data = {"intent": "nearby_search", "location": user_text, "location_query": user_text}
            else:
                try:
                    from app.api.voice import _rule_based_intent, _extract_voice_entities
                except Exception:
                    from processor.hospital_handler import _rule_based_intent, _extract_voice_entities

                rule_intent = await asyncio.to_thread(_rule_based_intent, user_text)
                if rule_intent.get("intent") != "unknown":
                    intent_data = rule_intent
                else:
                    try:
                        intent_data = await asyncio.wait_for(
                            self.llm.extract_intent(user_text, self.handler.state),
                            timeout=1.2
                        )
                        if not intent_data or intent_data.get("intent") in ("unrelated", "unknown", None, ""):
                            intent_data = rule_intent
                    except Exception as llm_err:
                        logger.warning(f"GroqLLM intent extraction fallback: {llm_err}")
                        intent_data = rule_intent

                local_entities = await asyncio.to_thread(_extract_voice_entities, user_text)
                for k, v in local_entities.items():
                    if v and not intent_data.get(k):
                        intent_data[k] = v

                # Handle phone normalization for spoken numbers (e.g., "9922886633 Double" or "9922886633")
                if (self.handler.current_intent in ("book_appointment", "cancel_appointment", "check_appointment")
                        and self.handler.patient_name and not self.handler.phone):
                    from processor.llm import normalize_phone
                    phone_digits = normalize_phone(user_text)
                    if len(phone_digits) >= 10:
                        intent_data["phone"] = phone_digits

            # 2. Dialogue Manager Processing
            assistant_text = await asyncio.to_thread(
                self.handler.process_intent,
                intent_data,
                user_text
            )

            should_end = False
            if "[END_CALL]" in assistant_text:
                assistant_text = assistant_text.replace("[END_CALL]", "").strip()
                should_end = True

            self.last_assistant_text = assistant_text
            if self.turn_manager:
                self.turn_manager.register_bot_reply(assistant_text)

            ttft = time.perf_counter() - request_start
            logger.info(f"[PIPECAT PERF] TTFT: {ttft:.3f}s | Reply: {assistant_text!r}")

            # Send bot_text frame over WebSocket
            await self.websocket.send_json({
                "type": "bot_text",
                "text": assistant_text,
                "voice_id": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
                "session_id": self.session_id,
                "end_call": should_end,
                "engine": "browser-stt-groq-tts-browser"
            })

        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.error(f"[PIPECAT PROCESSOR ERROR] {exc}", exc_info=True)


async def create_pipecat_web_session(websocket, session_id: str, user_id: str):
    """
    Creates and manages a Pipecat web session with Turn Management.
    """
    conv_uuid = uuid.uuid4()
    user_uuid = uuid.uuid4()
    
    turn_manager = TurnManager(
        conversation_id=conv_uuid,
        user_id=user_uuid,
        timeout=0.2
    )

    processor = WebPipecatProcessor(
        websocket=websocket,
        session_id=session_id,
        user_id=user_id,
        turn_manager=turn_manager
    )

    await processor.send_initial_greeting()
    return processor
