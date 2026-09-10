import os
import re
import json
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Word-to-digit phone number normalizer (no external API)
# ---------------------------------------------------------------------------
_WORD_DIGIT = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9",
}
_MULTIPLIER = {"double": 2, "triple": 3, "quadruple": 4}

def normalize_phone(raw: str) -> str:
    """Convert spoken phone strings to a digit string. Returns '' if nothing found."""
    if not raw:
        return ""
    # First strip all non-alphanumeric except spaces
    text = re.sub(r"[^a-zA-Z0-9 ]", " ", str(raw).lower())
    # STT can join words such as "twodouble eight" into one token.
    digit_words = "zero|oh|o|one|two|three|four|five|six|seven|eight|nine"
    text = re.sub(rf"({digit_words})(?=double|triple|quadruple)", r"\1 ", text)
    text = re.sub(rf"(double|triple|quadruple)(?={digit_words})", r"\1 ", text)
    tokens = text.split()
    digits = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _MULTIPLIER and i + 1 < len(tokens):
            nxt = tokens[i + 1]
            d = _WORD_DIGIT.get(nxt) or (nxt if nxt.isdigit() else None)
            if d:
                digits.append(d * _MULTIPLIER[tok])
                i += 2
                continue
        if tok in _WORD_DIGIT:
            digits.append(_WORD_DIGIT[tok])
        elif tok.isdigit():
            digits.append(tok)
        i += 1
    result = "".join(digits)
    # Also try extracting raw digit-only sequences from original string
    if not result:
        result = re.sub(r"\D", "", str(raw))
    return result


class GroqLLM:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from .env")
        self.client = AsyncGroq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    @classmethod
    async def verify_llm_health(cls) -> bool:
        """Startup health check that makes a real LLM call and fails loudly if it doesn't succeed."""
        try:
            instance = cls()
            test_res = await instance.extract_intent("Test startup connection", {})
            if test_res and test_res.get("intent"):
                print("[LLM HEALTH CHECK] Groq LLM startup health check PASSED!")
                return True
            raise RuntimeError("LLM health check returned invalid response format.")
        except Exception as e:
            print(f"[LLM HEALTH CHECK FAILED CRITICAL] Groq LLM startup check failed: {e}")
            raise RuntimeError(f"Groq LLM health check failed on startup: {e}") from e

    async def extract_intent(self, text: str, state: dict) -> dict:
        """
        Single fast Groq call.  Returns a dict with intent + entities.
        We pass only the fields that are NOT yet resolved in state, to keep
        the prompt tiny.
        """
        # Build a minimal state summary (only unresolved fields)
        pending = {k: v for k, v in state.items() if v is None}
        pending_str = ", ".join(pending.keys()) if pending else "none"

        from processor.hospital_db import get_all_specializations
        specs = get_all_specializations()
        spec_list_str = ", ".join(specs) if specs else "Cardiology, Gastroenterology, Orthopaedics, Gynaecology, General Medicine, Dermatology"

        system_prompt = (
            "You are Aradhya Mishra , a hospital appointment assistant.\n"
            "Help ONLY with: hospitals, doctors, specialties, fees, schedules, "
            "availability, appointments (booking/cancellation/check).\n"
            "For any unrelated question reply with intent=unrelated.\n\n"
            "Return ONLY valid JSON with these keys. Do not include any additional text or formatting outside the JSON:\n"
            "{\n"
            '  "intent": "<see list below>",\n'
            '  "doctor_name": "<doctor if explicitly mentioned, else null>",\n'
            '  "hospital_name": "<hospital if explicitly mentioned, else null>",\n'
            '  "specialization": "<specialty if mentioned, else null>",\n'
            '  "location_query": "<city, area, or \\\'near me\\\' if asking for nearby/location search, else null>",\n'
            '  "appointment_date": "<date string or null>",\n'
            '  "appointment_time": "<time string or null>",\n'
            '  "patient_name": "<patient full name if providing personal details, else null>",\n'
            '  "phone": "<phone digits only, convert spoken words to digits, else null>",\n'
            '  "address": "<address if provided, else null>",\n'
            '  "confirmation": "<yes|no|null>"\n'
            "}\n\n"
            "Intent values: greeting, book_appointment, list_hospitals, list_doctors, nearby_search, "
            "doctor_information, specialization_information, fee_information, schedule_information, "
            "hospital_information, check_availability, check_appointment, cancel_appointment, "
            "cancel_booking_process, patient_navigation, unrelated.\n\n"
            "RULES:\n"
            "- If the user asks to find hospitals, clinics, or doctors in/near a specific location or city (e.g. 'hospitals near me', 'doctors in Mumbai', 'clinics near Vijay Nagar', 'find cardiologists in Delhi'), set intent=nearby_search and set location_query to the city or area (e.g. 'Mumbai', 'Delhi', 'Vijay Nagar', 'near me').\n"
            f"- If the user describes a health concern (e.g. 'heart problem', 'stomach hurts') and asks which doctor/department to see, set intent=patient_navigation and set specialization to ONE of: {spec_list_str}.\n"
            "- Handle STT phonetic mishearings or typos for medical specialties: e.g., 'cardio movies', 'cardio logistics', 'bookend cardiologist', 'cardio' -> specialization='Cardiology'; 'derma' -> specialization='Dermatology'; 'ortho' -> specialization='Orthopaedics'. Map them to the closest standard specialization.\n"
            "- If the user asks whether a doctor is available on a date and time (e.g., 'Is Dr. X available tomorrow at 10 AM?', 'Will Dr. X be free?'), set intent=check_availability.\n"
            "- NEVER diagnose a disease, prescribe medicine, recommend treatment, or invent medical information.\n"
            "- If the user says 'I want to book an appointment', intent is EXACTLY book_appointment. Do NOT hallucinate a hospital or doctor.\n"
            "- If the user says 'Book Dr. X tomorrow at 11 AM', set intent=book_appointment, "
            "doctor_name=Dr. X, appointment_date=tomorrow, appointment_time=11 AM.\n"
            "- NEVER put a patient name into doctor_name. Patient names go in patient_name.\n"
            "- If user says 'My name is Ashish', patient_name=Ashish, doctor_name=null. Pay close attention to phrases like 'My name is X' or 'My full name is X'. Extract the most likely human name.\n"
            "- NEVER extract an address, location, or city as a patient's name.\n"
            "- For phone: convert 'one two three' -> '123', 'double four' -> '44', 'oh' -> '0'.\n"
            "- Separate date and time always. '27 August 11 AM' -> appointment_date='27 August', appointment_time='11 AM'.\n"
            "- If the user provides an address, location, or area, set address to it. If we are booking, keep intent=book_appointment.\n"
            f"- Fields still needed from user: {pending_str}.\n"
        )

        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_tokens=1024,
            )
            raw = completion.choices[0].message.content
            result = json.loads(raw)

            # Normalize phone right here so handler always gets clean digits
            if result.get("phone"):
                result["phone"] = normalize_phone(str(result["phone"]))

            return result
        except Exception as e:
            print(f"[LLM INTENT ERROR] {e}")
            return {"intent": "unrelated"}
