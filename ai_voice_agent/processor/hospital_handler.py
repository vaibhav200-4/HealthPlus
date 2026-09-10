"""
hospital_handler.py  –  Aradhya Mishra Hospital Assistant

Architecture:
  - One HospitalHandler instance per session (per call). State is NOT shared.
  - LLM extracts intent + entities (structured JSON).
  - This handler merges entities, resolves DB facts, validates, and produces
    a deterministic response. No hallucinations.
"""

import re
import difflib

from processor.hospital_db import (
    get_hospitals,
    get_doctors,
    get_doctors_by_hospital,
    get_doctors_by_specialization,
    get_doctor_by_name,
    get_all_specializations,
    check_slot_available,
    create_appointment,
    get_appointment_for_cancellation,
    cancel_appointment,
    get_patient_appointments,
    verify_appointment_booked,
    verify_appointment_cancelled,
    get_hospital_address,
    search_facilities_by_city,
    geocode_location,
    clean_location_string,
)
from processor.llm import normalize_phone

# ---------------------------------------------------------------------------
# Dynamic Hospital name normalizer – queries database dynamically
# ---------------------------------------------------------------------------
GENERIC_HOSPITAL_TOKENS = {
    "hospital", "hospitals", "clinic", "clinics", "medical", "centre", "center",
    "care", "advanced", "multispeciality", "speciality", "specialty", "health",
    "healthcare", "nursing", "home", "institute", "institution", "department",
    "unit", "facility", "doctor", "doctors", "doc", "availability", "check", "appointment",
    "which", "what", "where", "available", "avail", "show", "list", "find", "are", "all", "the", "in", "at", "to", "for"
}

CONFIRMATION_WORDS = {
    "yes", "yeah", "sure", "ok", "okay", "yep", "book", "confirm", "haan", "haa", "ha",
    "true", "yes please", "yes i want to book", "book appointment", "no", "nope", "nahi", "nahin"
}

HOSPITAL_ALIASES = {
    # Sunrise Multispeciality Hospital
    "sunrise": "Sunrise Multispeciality Hospital",
    "sun rise": "Sunrise Multispeciality Hospital",
    "sunrise multi": "Sunrise Multispeciality Hospital",
    "sunrise multispeciality": "Sunrise Multispeciality Hospital",
    "sunrise hospital": "Sunrise Multispeciality Hospital",

    # Green Valley Medical Centre
    "green valley": "Green Valley Medical Centre",
    "greenvalley": "Green Valley Medical Centre",
    "green valley medical": "Green Valley Medical Centre",
    "green valley centre": "Green Valley Medical Centre",
    "green valley center": "Green Valley Medical Centre",

    # Central City Hospital
    "central city": "Central City Hospital",
    "central hospital": "Central City Hospital",
    "central city hospital": "Central City Hospital",

    # Harmony Care Hospital
    "harmony": "Harmony Care Hospital",
    "harmony care": "Harmony Care Hospital",
    "harmony hospital": "Harmony Care Hospital",

    # Lifeline Advanced Hospital
    "lifeline": "Lifeline Advanced Hospital",
    "life line": "Lifeline Advanced Hospital",
    "lifeline advanced": "Lifeline Advanced Hospital",
    "lifeline hospital": "Lifeline Advanced Hospital",

    # Vijay Nagar Medical Clinic
    "vijay nagar": "Vijay Nagar Medical Clinic",
    "vijay": "Vijay Nagar Medical Clinic",
    "vjaya nagar": "Vijay Nagar Medical Clinic",
    "bjay nagar": "Vijay Nagar Medical Clinic",
    "vijay nagar clinic": "Vijay Nagar Medical Clinic",
    "vijay nagar medical": "Vijay Nagar Medical Clinic",

    # Old Palasia Medical Clinic
    "old palasia": "Old Palasia Medical Clinic",
    "palasia": "Old Palasia Medical Clinic",
    "palashia": "Old Palasia Medical Clinic",
    "old palashia": "Old Palasia Medical Clinic",
    "old palasia clinic": "Old Palasia Medical Clinic",
    # Rajwada Medical Clinic
    "rajwada": "Rajwada Medical Clinic",
    "rajbada": "Rajwada Medical Clinic",
    "raj wada": "Rajwada Medical Clinic",
    "rajwada clinic": "Rajwada Medical Clinic",
    "rajwada medical": "Rajwada Medical Clinic",

    # Bhawarkuan Medical Clinic
    "bhawarkuan": "Bhawarkuan Medical Clinic",
    "bhanwarkuan": "Bhawarkuan Medical Clinic",
    "bhanwar kuan": "Bhawarkuan Medical Clinic",
    "bhanwar goa": "Bhawarkuan Medical Clinic",
    "bower goa": "Bhawarkuan Medical Clinic",
    "bower kuan": "Bhawarkuan Medical Clinic",
    "bhanwar": "Bhawarkuan Medical Clinic",
    "bower": "Bhawarkuan Medical Clinic",
    "bhawarkua": "Bhawarkuan Medical Clinic",
    "bhawarkwa": "Bhawarkuan Medical Clinic",
    "bhawar": "Bhawarkuan Medical Clinic",
    "pawar goa": "Bhawarkuan Medical Clinic",
    "pawar kua": "Bhawarkuan Medical Clinic",
    "pawarkua": "Bhawarkuan Medical Clinic",
    "bavar goa": "Bhawarkuan Medical Clinic",
    "bavar goa medical clinic": "Bhawarkuan Medical Clinic",
    "bavar": "Bhawarkuan Medical Clinic",
    "bhavar goa": "Bhawarkuan Medical Clinic",
    "bhavar goa medical clinic": "Bhawarkuan Medical Clinic",
    "bhavar": "Bhawarkuan Medical Clinic",
    "bawar goa": "Bhawarkuan Medical Clinic",
    "bawar goa medical clinic": "Bhawarkuan Medical Clinic",
    "bhawar goa": "Bhawarkuan Medical Clinic",
    "bhawar goa medical clinic": "Bhawarkuan Medical Clinic",
    "pawar goa medical clinic": "Bhawarkuan Medical Clinic",
    "bhawarkuan clinic": "Bhawarkuan Medical Clinic",
    "bhawarkuan medical": "Bhawarkuan Medical Clinic",

    # Old Palasia Medical Clinic
    "old palasia": "Old Palasia Medical Clinic",
    "palasia": "Old Palasia Medical Clinic",
    "palashia": "Old Palasia Medical Clinic",
    "old palashia": "Old Palasia Medical Clinic",
    "old palacia": "Old Palasia Medical Clinic",
    "palacia": "Old Palasia Medical Clinic",
    "palacia clinic": "Old Palasia Medical Clinic",
    "palacia medical clinic": "Old Palasia Medical Clinic",
    "old palasia clinic": "Old Palasia Medical Clinic",
    "old palasia medical clinic": "Old Palasia Medical Clinic",

    # Sudama Nagar Medical Clinic
    "sudama nagar": "Sudama Nagar Medical Clinic",
    "sudama": "Sudama Nagar Medical Clinic",
    "sudamangar": "Sudama Nagar Medical Clinic",
    "sudama clinic": "Sudama Nagar Medical Clinic",
    "sudama nagar medical": "Sudama Nagar Medical Clinic",
}

def _normalize_hospital(raw: str) -> str | None:
    if not raw:
        return None
    lower_raw = str(raw).lower().strip()
    lower_raw = re.sub(r'[\.,!\?]+$', '', lower_raw).strip()

    if not lower_raw or lower_raw in ("hospital", "hospitals", "clinic", "clinics", "medical", "none", "null"):
        return None

    # 0. Check explicit aliases first
    for alias, h_name in HOSPITAL_ALIASES.items():
        if alias in lower_raw or lower_raw in alias:
            return h_name
    
    # 0.5. Check fuzzy match against alias keys (SequenceMatcher ratio >= 0.70)
    best_alias_h = None
    best_alias_score = 0.0
    for alias, h_name in HOSPITAL_ALIASES.items():
        score = difflib.SequenceMatcher(None, lower_raw, alias).ratio()
        if score > best_alias_score:
            best_alias_score = score
            best_alias_h = h_name

    if best_alias_score >= 0.70:
        return best_alias_h

    # Strip common generic words to find meaningful tokens
    raw_tokens = [w for w in re.findall(r'\b[a-z0-9]+\b', lower_raw) if w not in GENERIC_HOSPITAL_TOKENS]
    if not raw_tokens:
        return None

    hospitals = get_hospitals()
    if not hospitals:
        return None

    raw_meaningful = " ".join(raw_tokens)

    # 1. Exact or substring match on meaningful hospital name tokens
    for h_name, _ in hospitals:
        h_tokens = [w for w in re.findall(r'\b[a-z0-9]+\b', h_name.lower()) if w not in GENERIC_HOSPITAL_TOKENS]
        h_meaningful = " ".join(h_tokens)
        if h_meaningful and (raw_meaningful == h_meaningful or h_meaningful in raw_meaningful or raw_meaningful in h_meaningful):
            return h_name

    # 2. Fuzzy token similarity match
    best_h_name = None
    best_score = 0.0
    for h_name, _ in hospitals:
        h_tokens = [w for w in re.findall(r'\b[a-z0-9]+\b', h_name.lower()) if w not in GENERIC_HOSPITAL_TOKENS]
        for r_tok in raw_tokens:
            if len(r_tok) < 3:
                continue
            for h_tok in h_tokens:
                score = difflib.SequenceMatcher(None, r_tok, h_tok).ratio()
                if score > best_score:
                    best_score = score
                    best_h_name = h_name

    if best_score >= 0.70:
        return best_h_name

    return None
SPECIALIZATION_ALIASES = {
    "cardio": "Cardiology",
    "cardiologist": "Cardiology",
    "cardiology": "Cardiology",
    "cardiac": "Cardiology",
    "heart": "Cardiology",
    "cardio movies": "Cardiology",
    "cardio logistics": "Cardiology",
    "bookend cardiologist": "Cardiology",
    "ortho": "Orthopaedics",
    "orthopedics": "Orthopaedics",
    "orthopaedic": "Orthopaedics",
    "orthopaedics": "Orthopaedics",
    "orthopedist": "Orthopaedics",
    "bone": "Orthopaedics",
    "derma": "Dermatology",
    "dermatologist": "Dermatology",
    "dermatology": "Dermatology",
    "skin": "Dermatology",
    "gynaec": "Gynaecology",
    "gynaecology": "Gynaecology",
    "gynecology": "Gynaecology",
    "gynaecologist": "Gynaecology",
    "gynecologist": "Gynaecology",
    "women": "Gynaecology",
    "gastro": "Gastroenterology",
    "gastroenterology": "Gastroenterology",
    "gastroenterologist": "Gastroenterology",
    "stomach": "Gastroenterology",
    "general medicine": "General Medicine",
    "general physician": "General Medicine",
    "physician": "General Medicine",
}

def _normalize_specialization(raw: str) -> str | None:
    if not raw or str(raw).lower() in ("none", "null", ""):
        return None
    lower_raw = str(raw).lower().strip()

    # 1. Alias lookup
    for alias, std_spec in SPECIALIZATION_ALIASES.items():
        if alias in lower_raw or lower_raw in alias:
            return std_spec

    # 2. Substring match against DB specializations
    valid_specs = get_all_specializations() or [
        "Cardiology", "Gastroenterology", "Orthopaedics",
        "Gynaecology", "General Medicine", "Dermatology"
    ]
    for s in valid_specs:
        if s.lower() in lower_raw or lower_raw in s.lower():
            return s

    # 3. Fuzzy word matching with difflib
    raw_words = lower_raw.split()
    for word in raw_words:
        matches = difflib.get_close_matches(word, [s.lower() for s in valid_specs], n=1, cutoff=0.7)
        if matches:
            matched_lower = matches[0]
            for s in valid_specs:
                if s.lower() == matched_lower:
                    return s

    return None


# Doctor name resolver – safe (only when appropriate)
# ---------------------------------------------------------------------------
def _resolve_doctor(name_hint: str, hospital_filter: str | None = None) -> tuple | None:
    if not name_hint:
        return None

    clean = re.sub(r'^(dr\.?|doctor)\s+', '', name_hint.strip(), flags=re.I).strip()

    # 1. Direct DB lookup (ILIKE)
    doc = get_doctor_by_name(clean) or get_doctor_by_name(name_hint.strip())
    if doc:
        if hospital_filter and hospital_filter.lower() not in doc[5].lower():
            return None
        return doc

    # 2. Fuzzy match
    if hospital_filter:
        candidates = get_doctors_by_hospital(hospital_filter)
        cand_names = [r[0] for r in candidates]
    else:
        all_docs = get_doctors()
        cand_names = [r[0] for r in all_docs]

    if not cand_names:
        return None

    # Map cleaned candidate names to original DB names
    cand_map = {}
    for c in cand_names:
        c_clean = re.sub(r'^(dr\.?|doctor)\s+', '', c.strip(), flags=re.I).strip().lower()
        # Keep track of the original name so we can look it up in DB
        cand_map[c_clean] = c

    matches = difflib.get_close_matches(clean.lower(), cand_map.keys(), n=1, cutoff=0.75)
    if matches:
        resolved_original = cand_map[matches[0]]
        return get_doctor_by_name(resolved_original)

    return None


def _fmt_doc(doc_row) -> str:
    name = doc_row[1]
    return name if str(name).startswith("Dr") else f"Dr. {name}"


# ---------------------------------------------------------------------------
# Main handler – one instance per session
# ---------------------------------------------------------------------------
class HospitalHandler:
    def __init__(self):
        self.hospital_name: str | None = None
        self.doctor_name: str | None = None
        self.doctor_row: tuple | None = None
        self.specialization: str | None = None
        self.appointment_date: str | None = None
        self.appointment_time: str | None = None
        self.patient_name: str | None = None
        self.phone: str | None = None
        self.phone_buffer = ""
        self.address: str | None = None
        
        self.current_intent: str | None = None
        self.confirmation_pending: bool = False
        self.navigation_booking_pending: bool = False
        self.awaiting_anything_else: bool = False
        
        # Dynamic nearby search state (info-only, separate from booking)
        self.location_query: str | None = None
        self.nearby_results: list = []
        self.awaiting_registered_booking: bool = False
        
        self.cancel_appointments: list = []
        self.cancel_idx: int = 0

    def process_intent(self, intent_data: dict, user_text: str = "") -> str:
        intent = intent_data.get("intent", "unrelated")
        if not isinstance(intent, str):
            intent = "unrelated"
        intent = intent.lower()

        if self.confirmation_pending:
            return self._handle_confirmation(intent_data, user_text)

        if getattr(self, "navigation_booking_pending", False):
            self.navigation_booking_pending = False
            text_lower = user_text.lower().strip()
            confirm = intent_data.get("confirmation")
            if confirm == "yes" or any(w in text_lower for w in ("yes", "yeah", "sure", "ok", "book")):
                intent = "book_appointment"
                self.current_intent = "book_appointment"
            elif confirm == "no" or any(w in text_lower for w in ("no", "nope")):
                self.awaiting_anything_else = True
                return "Alright. How else can I help you?"

        text_clean_lower = re.sub(r'[^a-z0-9\s\']', '', user_text.lower().strip())
        explicit_ending = {"no thanks", "no thank you", "that's all", "thats all", "nothing else", "that is all", "i'm done", "im done", "bye", "goodbye", "nothing"}
        if text_clean_lower in explicit_ending or (getattr(self, "awaiting_anything_else", False) and text_clean_lower in ("no", "nope", "nahi", "nahin")):
            self._reset()
            return "Thank you for using Aradhya Hospital Assistant. Have a great day! [END_CALL]"

        self.awaiting_anything_else = False

        self._merge_entities(intent_data, user_text)

        # Transition intent to book_appointment when doctor or hospital entity is present
        if (self.doctor_name or self.hospital_name):
            if not self.current_intent or self.current_intent in ("book_appointment", "nearby_search"):
                self.current_intent = "book_appointment"
                if intent in ("unknown", "unrelated", "greeting", "list_hospitals", "hospital_information"):
                    intent = "book_appointment"

        # ── Follow-up after dynamic nearby search: user wants to book at registered hospital ──
        if getattr(self, "awaiting_registered_booking", False):
            self.awaiting_registered_booking = False
            text_lower = user_text.lower().strip()
            confirm = intent_data.get("confirmation")
            is_yes = confirm == "yes" or any(w in text_lower for w in ("yes", "yeah", "sure", "ok", "book", "appointment", "want to book", "ha", "haa", "haan"))
            is_no = confirm == "no" or any(w in text_lower for w in ("no", "nope", "nahi", "nahin"))
            
            if is_yes and not is_no:
                intent = "book_appointment"
                self.current_intent = "book_appointment"
            elif is_no:
                self.awaiting_anything_else = True
                return "Alright. How else can I help you today?"

        # ── Nearby search continuation: user is providing their city/area name ──
        if self.current_intent == "nearby_search" and not self.location_query:
            # User is answering "Which city are you in?" — treat their text as location
            text_clean = clean_location_string(user_text)
            if text_clean and intent not in ("farewell", "greeting", "book_appointment",
                                              "cancel_appointment", "list_hospitals"):
                intent = "nearby_search"
                intent_data["location_query"] = text_clean
                intent_data["intent"] = "nearby_search"

        # Fallback for LLM JSON failures or complete misclassifications during data collection
        if self.current_intent in ("book_appointment", "cancel_appointment", "check_appointment"):
            if intent in ("unrelated", "unknown") and not any(intent_data.get(k) for k in ["patient_name", "phone", "address", "hospital_name", "doctor_name", "appointment_date", "appointment_time"]):
                text_clean = user_text.strip()
                if text_clean:
                    if self.current_intent == "book_appointment":
                        # Only collect patient details as fallback IF doctor/hospital & date/time are established
                        if (self.hospital_name or self.doctor_name) and self.appointment_date and self.appointment_time:
                            clean_text_val = text_clean.strip().lower().rstrip('.!?')
                            if not self.patient_name and clean_text_val not in CONFIRMATION_WORDS:
                                self.patient_name = text_clean
                                intent = self.current_intent
                            elif not self.phone:
                                digits = normalize_phone(text_clean)
                                if len(digits) >= 10:
                                    self.phone = digits[:10]
                                    intent = self.current_intent
                            elif not self.address and clean_text_val not in CONFIRMATION_WORDS:
                                self.address = text_clean
                                intent = self.current_intent
                    elif self.current_intent in ("cancel_appointment", "check_appointment"):
                        clean_text_val = text_clean.strip().lower().rstrip('.!?')
                        if not self.patient_name and clean_text_val not in CONFIRMATION_WORDS:
                            self.patient_name = text_clean
                            intent = self.current_intent
                        elif not self.phone:
                            digits = normalize_phone(text_clean)
                            if len(digits) >= 10:
                                self.phone = digits[:10]
                                intent = self.current_intent

        # Robust intent override: if we are in a booking flow and the LLM misclassified a single-entity response
        if self.current_intent in ("book_appointment", "cancel_appointment", "check_appointment"):
            if intent in ("unrelated", "unknown", "hospital_information", "doctor_information", "fee_information", "schedule_information"):
                # If they provided ANY useful booking entity in this turn, force current intent
                def _is_valid(val):
                    return bool(val and str(val).lower() not in ("none", "null", ""))

                if any(_is_valid(intent_data.get(k)) for k in ["patient_name", "phone", "address", "hospital_name", "doctor_name", "appointment_date", "appointment_time"]):
                    intent = self.current_intent

        # Logging to verify router
        print(f"[ROUTER] intent={intent}")
        print(f"[ROUTER] entities={intent_data}")
        print(f"[STATE] after={self.state}")

        # Exact ONE router based on explicit intent
        if intent == "farewell":
            self._reset()
            return "Thank you for calling, have a great day and stay healthy, goodbye!"
            
        if intent == "greeting":
            if self.current_intent:
                return self._resume_flow()
            self._reset()
            return ("Hello! I am Aradhya Mishra, your hospital assistant. "
                    "I can help you with hospital information, doctor availability, "
                    "and appointment booking. How can I help you today?")
                    
        if intent == "nearby_search":
            return self._handle_nearby_search(intent_data, user_text)

        if intent == "list_hospitals":
            return self._handle_list_hospitals()
            
        if intent == "list_doctors":
            return self._handle_list_doctors(intent_data)
            
        if intent == "patient_navigation":
            return self._handle_patient_navigation(intent_data, user_text)

        if intent == "check_specialization" or intent == "specialization_information":
            return self._handle_check_specialization(intent_data)
            
        if intent in ("check_fee", "fee_information", "check_schedule", "schedule_information", "check_hospital", "hospital_information", "doctor_information"):
            return self._handle_info_query(intent)

        if intent == "check_availability":
            return self._handle_check_availability()
            
        if intent == "book_appointment":
            self.current_intent = "book_appointment"
            return self._handle_booking()
            
        if intent == "cancel_appointment":
            self.current_intent = "cancel_appointment"
            return self._handle_cancel()
            
        if intent == "cancel_booking_process":
            self._reset()
            return "Booking process cancelled. How else can I help you?"

        if intent == "check_appointment":
            self.current_intent = "check_appointment"
            return self._handle_check_appointment()

        # Fallback for unrelated
        return ("I can help with hospital information and appointments. "
                "What would you like to know?")

    def _merge_entities(self, d: dict, user_text: str = ""):
        extracted_patient = None
        raw_p = d.get("patient_name")
        if raw_p and str(raw_p).lower() not in ("none", "null", ""):
            extracted_patient = str(raw_p).strip()

        # ── Hospital resolution ──────────────────────────────────────────────
        raw_h = d.get("hospital_name")
        candidates_h = []
        if raw_h and str(raw_h).lower() not in ("none", "null", ""):
            candidates_h.append(str(raw_h))
        if user_text:
            candidates_h.append(user_text)

        if not self.hospital_name:
            for cand_h in candidates_h:
                norm_h = _normalize_hospital(cand_h)
                if norm_h:
                    self.hospital_name = norm_h
                    break
        raw_d = d.get("doctor_name")
        explicit_doc = raw_d if (raw_d and str(raw_d).lower() not in ("none", "null", "")) else None

        candidates_to_try = []
        if explicit_doc:
            candidates_to_try.append(explicit_doc)

        if not self.doctor_name:
            if explicit_doc and explicit_doc not in candidates_to_try:
                candidates_to_try.append(explicit_doc)
            if user_text and user_text not in candidates_to_try:
                candidates_to_try.append(user_text)
            if extracted_patient and extracted_patient not in candidates_to_try:
                candidates_to_try.append(extracted_patient)
            if self.patient_name and self.patient_name not in candidates_to_try:
                candidates_to_try.append(self.patient_name)

        for candidate in candidates_to_try:
            doc = _resolve_doctor(candidate, self.hospital_name)
            if doc:
                # If changing doctors, clear the date/time since the schedule is different
                if self.doctor_name and self.doctor_name != doc[1]:
                    self.appointment_date = None
                    self.appointment_time = None
                    
                self.doctor_row = doc
                self.doctor_name = doc[1]
                if not self.hospital_name:
                    self.hospital_name = doc[5]
                self.specialization = doc[2]
                
                # If the candidate came from patient_name state, clear it (it was misclassified)
                if self.patient_name == candidate:
                    self.patient_name = None
                if extracted_patient == candidate:
                    extracted_patient = None
                break  # Stop once we have a valid doctor

        # Only store as patient_name if the value is NOT a doctor and NOT a confirmation word
        if extracted_patient:
            clean_p = extracted_patient.strip().lower().rstrip('.!?')
            if clean_p not in CONFIRMATION_WORDS and not _resolve_doctor(extracted_patient, self.hospital_name):
                self.patient_name = extracted_patient

        # Phone
        raw_ph = d.get("phone")
        if raw_ph:
            digits = re.sub(r"\D", "", str(raw_ph))
            if digits:
                # Speech recognition often delivers a phone number in several turns.
                if len(digits) >= 10:
                    self.phone = digits[:10]
                    self.phone_buffer = self.phone
                else:
                    self.phone_buffer = (self.phone_buffer + digits)[-10:]
                    if len(self.phone_buffer) == 10:
                        self.phone = self.phone_buffer

        # Address
        raw_a = d.get("address")
        if raw_a and str(raw_a).lower() not in ("none", "null", ""):
            clean_a = re.sub(r'^(my\s+address\s+is\s+|address\s+is\s+)', '', str(raw_a), flags=re.I).strip()
            self.address = clean_a
        elif self.current_intent == "book_appointment" and self.doctor_name and self.appointment_date and self.appointment_time and self.patient_name and self.phone and not self.address:
            # We are explicitly in the address collection state! Accept ANY non-empty free-text input as address!
            clean_user = re.sub(r'^(my\s+address\s+is\s+|address\s+is\s+)', '', user_text, flags=re.I).strip()
            if clean_user and not any(w in clean_user.lower() for w in ("cancel", "stop", "exit", "quit")):
                self.address = clean_user

        # Strip trailing punctuation from patient_name, address, doctor_name, hospital_name
        def _clean_punct(val: str | None) -> str | None:
            if not val:
                return None
            return re.sub(r'[\.,!\?]+$', '', str(val)).strip()

        if self.patient_name:
            self.patient_name = _clean_punct(self.patient_name)
        if self.address:
            self.address = _clean_punct(self.address)
        if self.doctor_name:
            self.doctor_name = _clean_punct(self.doctor_name)
        if self.hospital_name:
            self.hospital_name = _clean_punct(self.hospital_name)

        # Specialization
        raw_s = d.get("specialization")
        norm_spec = None
        if raw_s:
            norm_spec = _normalize_specialization(str(raw_s)) or str(raw_s).strip()
        elif user_text:
            norm_spec = _normalize_specialization(user_text)

        if norm_spec:
            # Clear old doctor lock when searching by specialization
            self.doctor_name = None
            self.doctor_row = None
            # If specialization changed or set, check if hospital was explicitly specified in this turn
            raw_h = d.get("hospital_name")
            explicit_h = _normalize_hospital(raw_h) if raw_h else _normalize_hospital(user_text)
            if not explicit_h:
                # User did not explicitly specify a hospital, clear old hospital filter to allow multi-hospital search
                self.hospital_name = None
            else:
                self.hospital_name = explicit_h
            self.specialization = norm_spec
        else:
            # Hospital (only if user explicitly mentions a hospital name)
            raw_h = d.get("hospital_name")
            if raw_h:
                resolved = _normalize_hospital(raw_h)
                if resolved:
                    self.hospital_name = resolved
            elif user_text:
                resolved = _normalize_hospital(user_text)
                if resolved:
                    self.hospital_name = resolved

        # Date/Time
        raw_date = d.get("appointment_date")
        if raw_date and str(raw_date).lower() not in ("none", "null", ""):
            # STT might output a.m. or p.m. with dots. Remove dots to normalize.
            date_clean = re.sub(r'([ap])\.m\.', r'\1m', str(raw_date), flags=re.I)
            time_in_date = re.search(
                r'\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b',
                date_clean,
                flags=re.I,
            )
            if time_in_date:
                self.appointment_time = time_in_date.group(0)
                self.appointment_date = date_clean[:time_in_date.start()].strip()
            else:
                self.appointment_date = str(raw_date).strip()

        raw_time = d.get("appointment_time")
        if raw_time and str(raw_time).lower() not in ("none", "null", ""):
            time_clean = re.sub(r'([ap])\.m\.', r'\1m', str(raw_time), flags=re.I)
            self.appointment_time = time_clean.strip()

        # CRITICAL GUARD: If doctor is set, lock hospital_name to doctor's actual database hospital!
        if self.doctor_row and len(self.doctor_row) > 5 and self.doctor_row[5]:
            self.hospital_name = self.doctor_row[5]

    def _looks_like_patient_context(self, d: dict) -> bool:
        p = d.get("patient_name")
        return bool(p and str(p).lower() not in ("none", "null", ""))


    # ── Dynamic Nearby Search Handler ───────────────────────────────────────
    def _handle_nearby_search(self, intent_data: dict, user_text: str = "") -> str:
        raw_loc = intent_data.get("location_query") or self.location_query
        spec = intent_data.get("specialization") or self.specialization

        loc = clean_location_string(raw_loc) if raw_loc else None
        cleaned_user = clean_location_string(user_text) if user_text else None

        # Filter out generic relative location tokens
        INVALID_CITY_TOKENS = {"me", "here", "nearby", "near me", "near_me", "none", "null", ""}

        # If location specified in intent_data or user_text, update state
        if loc and loc.lower() not in INVALID_CITY_TOKENS:
            self.location_query = loc
        elif cleaned_user and cleaned_user.lower() not in INVALID_CITY_TOKENS and not any(w in cleaned_user.lower() for w in ("find hospitals", "hospitals near me", "show me hospital", "hospital near me")):
            self.location_query = cleaned_user

        # If no location query yet, ask user for location
        if not self.location_query:
            self.current_intent = "nearby_search"  # Remember we're waiting for city
            return "Which city or area are you located in? I can search for nearby hospitals and clinics for you."

        # Search facilities via Overpass API
        self.current_intent = None  # Clear — we're executing, not waiting
        results = search_facilities_by_city(self.location_query, specialty=spec)
        if not results:
            loc_disp = self.location_query.title()
            self.location_query = None
            self.awaiting_registered_booking = True
            return (f"I couldn't find any medical facilities near {loc_disp}. "
                    "Would you like to see available options at our registered HealthPlus hospitals instead?")

        self.nearby_results = results
        self.awaiting_registered_booking = True  # Enable follow-up booking transition
        top_results = results[:5]

        items = []
        for i, f in enumerate(top_results, 1):
            dist_m = f.get("distance_meters", 0)
            if dist_m >= 1000:
                dist_str = f"{dist_m / 1000:.1f} km"
            else:
                dist_str = f"{int(dist_m)} meters"

            phone = f.get("phone")
            phone_str = f", phone {phone}" if phone else ""
            items.append(f"{i}. {f['name']} ({dist_str} away{phone_str})")

        spec_str = f" for {spec}" if spec else ""
        loc_disp = self.location_query.title()
        res_str = "; ".join(items)

        top_phrase = " The top five nearest are: " if len(results) > 5 else " "
        return (
            f"I found {len(results)} facilities near {loc_disp}{spec_str}.{top_phrase}{res_str}. "
            "Please note these are external facilities provided for information only. "
            "If you would like to book an appointment at one of our HealthPlus registered hospitals, just let me know!"
        )

    # ── Information handlers ─────────────────────────────────────────────────
    def _handle_list_hospitals(self) -> str:
        self.specialization = None
        self.doctor_name = None
        self.doctor_row = None
        rows = get_hospitals()
        if not rows:
            return "I'm sorry, I couldn't find any hospitals in our system right now."
        names = [r[0] for r in rows]
        return f"We have {len(names)} available hospitals: {', '.join(names)}. Which hospital would you prefer?"

    def _handle_list_doctors(self, d: dict) -> str:
        hospital = self.hospital_name
        if not hospital:
            raw_h = d.get("hospital_name")
            if raw_h:
                hospital = _normalize_hospital(raw_h)
        if hospital:
            rows = get_doctors_by_hospital(hospital)
            if not rows:
                return f"I couldn't find any doctors at {hospital}."
            doc_list = [
                f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]} ({r[1]})"
                for r in rows
            ]
            return f"At {hospital} we have: {', '.join(doc_list)}."
        
        rows = get_doctors()
        if not rows:
            return "I couldn't find any doctors in our system."
        doc_list = [
            f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]} ({r[1]})"
            for r in rows
        ]
        return f"We have the following doctors: {', '.join(doc_list)}."

    def _handle_patient_navigation(self, d: dict, user_text: str = "") -> str:
        # If user asks about other hospitals or different hospitals, clear hospital filter
        if any(w in user_text.lower() for w in ("other", "different", "else", "another")):
            self.hospital_name = None

        spec = d.get("specialization") or self.specialization
        valid_specs = get_all_specializations() or ["Cardiology", "Gastroenterology", "Orthopaedics", "Gynaecology", "General Medicine", "Dermatology"]
        
        matched_spec = None
        if spec:
            for v in valid_specs:
                if v.lower() in str(spec).lower() or str(spec).lower() in v.lower():
                    matched_spec = v
                    break

        if not matched_spec:
            specs_str = ", ".join(valid_specs[:6])
            return f"I can help you find a doctor from departments such as: {specs_str}. Which specialty do you need?"

        self.specialization = matched_spec
        rows = get_doctors_by_specialization(matched_spec, self.hospital_name)
        if not rows:
            return f"I couldn't find any {matched_spec} doctors."

        doc_list = []
        for r in rows:
            name = f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]}"
            fee = int(float(r[1])) if r[1] else 0
            schedule = r[2]
            hospital = r[3]
            if self.hospital_name:
                doc_list.append(f"{name} (fee: rupees {fee}, schedule: {schedule})")
            else:
                doc_list.append(f"{name} at {hospital} (fee: rupees {fee}, schedule: {schedule})")
        
        docs_str = ", ".join(doc_list)
        self.navigation_booking_pending = True

        if len(rows) == 1 and any(w in user_text.lower() for w in ("other", "different", "else", "another")):
            r = rows[0]
            name = f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]}"
            return f"Currently, {name} at {r[3]} is our only {matched_spec} specialist across all available hospitals (fee: rupees {int(float(r[1]))}, schedule: {r[2]}). Would you like to book an appointment with {name}?"

        return f"A {matched_spec} department may be appropriate. We have: {docs_str}. Would you like to book an appointment?"

    def _handle_check_specialization(self, d: dict) -> str:
        spec = self.specialization or d.get("specialization")
        if not spec:
            return "Which specialization are you interested in?"
        rows = get_doctors_by_specialization(spec, self.hospital_name)
        if not rows:
            return f"I couldn't find any {spec} doctors in our system."
        doc_list = [
            f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]} at {r[3]}"
            for r in rows
        ]
        return f"For {spec} we have: {', '.join(doc_list)}."

    def _handle_info_query(self, intent: str) -> str:
        if not self.doctor_row and self.doctor_name:
            self.doctor_row = get_doctor_by_name(self.doctor_name)
        doc = self.doctor_row
        if not doc:
            return "Which doctor would you like information about?"
        display = _fmt_doc(doc)
        if intent in ("check_fee", "fee_information"):
            return f"{display} charges rupees {int(float(doc[3]))}."
        if intent in ("check_schedule", "schedule_information"):
            return f"{display} is available {doc[4]}."
        if intent in ("check_hospital", "hospital_information", "doctor_information"):
            return f"{display} specializes in {doc[2]} and works at {doc[5]}."
        return ""

    def _handle_check_availability(self) -> str:
        if not self.doctor_name:
            if self.specialization:
                rows = get_doctors_by_specialization(self.specialization, self.hospital_name)
                if rows:
                    doc_list = []
                    for r in rows:
                        name = f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]}"
                        hosp = r[3]
                        if self.hospital_name:
                            doc_list.append(name)
                        else:
                            doc_list.append(f"{name} at {hosp}")
                    location = f" at {self.hospital_name}" if self.hospital_name else ""
                    return f"I found these {self.specialization} doctors{location}: {', '.join(doc_list)}. Which doctor would you like to check availability for?"
            return "Which doctor would you like to check availability for?"
        if not self.doctor_row:
            self.doctor_row = get_doctor_by_name(self.doctor_name)

        if not self.appointment_date or not self.appointment_time:
            if not self.appointment_date:
                return f"What date would you like to check for Dr. {self.doctor_name}?"
            return f"What time would you like to check for Dr. {self.doctor_name} on {self.appointment_date}?"

        doc = self.doctor_row
        display = _fmt_doc(doc) if doc else f"Dr. {self.doctor_name}"
        fee_amount = int(float(doc[3])) if (doc and len(doc) > 3 and doc[3]) else 500
        fee_str = f" The consultation fee is rupees {fee_amount}."

        available = check_slot_available(self.doctor_name, self.appointment_date, self.appointment_time)
        if available:
            self.navigation_booking_pending = True
            return f"Yes, {display} is available on {self.appointment_date} at {self.appointment_time}.{fee_str} Would you like to book an appointment?"
        else:
            return f"No, {display} is not available on {self.appointment_date} at {self.appointment_time}. What other date or time works for you?"

    # ── Booking flow ─────────────────────────────────────────────────────────
    def _handle_booking(self) -> str:
        if not self.doctor_name:
            if self.specialization:
                rows = get_doctors_by_specialization(self.specialization, self.hospital_name)
                if rows:
                    doc_list = []
                    for r in rows:
                        name = f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]}"
                        hosp = r[3]
                        if self.hospital_name:
                            doc_list.append(name)
                        else:
                            doc_list.append(f"{name} at {hosp}")
                    location = f" at {self.hospital_name}" if self.hospital_name else ""
                    return f"I found these {self.specialization} doctors{location}: {', '.join(doc_list)}. Which doctor would you like to book?"
                else:
                    location = f" at {self.hospital_name}" if self.hospital_name else ""
                    return f"I couldn't find any {self.specialization} doctors{location}. Which hospital or doctor would you prefer?"

            if self.hospital_name:
                rows = get_doctors_by_hospital(self.hospital_name)
                if rows:
                    doc_list = [f"{r[0] if str(r[0]).startswith('Dr') else 'Dr. ' + r[0]} ({r[1]})" for r in rows]
                    return f"At {self.hospital_name} we have: {', '.join(doc_list)}. Which doctor would you like to see?"
                return f"Which doctor would you like to see at {self.hospital_name}?"

            rows = get_hospitals()
            names = [r[0] for r in rows] if rows else []
            if names:
                return f"Which hospital would you prefer? Available options are: {', '.join(names)}."
            return "Which hospital would you prefer?"

        if not self.doctor_row:
            self.doctor_row = get_doctor_by_name(self.doctor_name)
        if not self.doctor_row:
            return "Could you tell me the doctor's name again?"

        doc = self.doctor_row
        display = _fmt_doc(doc)
        if not self.hospital_name:
            self.hospital_name = doc[5]

        if not self.appointment_date or not self.appointment_time:
            prompt = (
                f"{display} specializes in {doc[2]} at {self.hospital_name}. "
                f"The consultation fee is rupees {int(float(doc[3]))} and they are available {doc[4]}. "
            )
            if not self.appointment_date:
                return prompt + "What date would you like to book?"
            if not self.appointment_time:
                return prompt + f"I have the date as {self.appointment_date}. What time would you like to book?"

        # All core booking info present, check availability
        available = check_slot_available(
            self.doctor_name,
            self.appointment_date,
            self.appointment_time,
        )
        if not available:
            self.appointment_date = None
            self.appointment_time = None
            return f"I'm sorry, {display} is not available at that time. What other date or time works for you?"

        # Slot is available, collect missing patient info
        if not self.patient_name:
            return "That slot is available! Please provide your full name."

        if not self.phone:
            return f"Thanks {self.patient_name}. What is your ten digit mobile number?"
        if len(self.phone) != 10 or not self.phone.isdigit():
            self.phone = None
            return "Please provide a valid ten digit mobile number."

        if not self.address:
            return "Got it. Finally, what is your address?"

        # All fields present – show summary and ask confirmation
        self.confirmation_pending = True
        return (
            f"Please confirm your booking: "
            f"{display} at {self.hospital_name}, "
            f"on {self.appointment_date} at {self.appointment_time}, "
            f"fee rupees {int(float(doc[3]))}, "
            f"patient {self.patient_name}, "
            f"number ending {' '.join(self.phone[-4:])}. "
            "Shall I confirm this booking? Say yes or no."
        )

    def _handle_confirmation(self, intent_data: dict, user_text: str) -> str:
        confirm = intent_data.get("confirmation")
        text_lower = user_text.lower().strip()

        if confirm is None:
            if any(w in text_lower for w in ("yes", "yeah", "confirm", "ok", "haan", "ha", "bilkul", "thik", "theek", "sure", "yep", "do it")):
                confirm = "yes"
            elif any(w in text_lower for w in ("no", "nahi", "nope", "cancel", "nahin")):
                confirm = "no"

        if confirm == "yes":
            self.confirmation_pending = False
            return self._execute_booking()

        if confirm == "no":
            self.confirmation_pending = False
            self._reset()
            self.awaiting_anything_else = True
            return "No problem, I've cancelled the booking request. How else can I help you?"

        return "Sorry, I didn't catch that. Please say yes to confirm or no to cancel."

    def _execute_booking(self) -> str:
        app_id = create_appointment(
            self.patient_name,
            self.phone,
            self.address,
            self.doctor_name,
            self.appointment_date,
            self.appointment_time,
        )
        if app_id and verify_appointment_booked(app_id):
            booking_id = app_id
            self._reset()
            self.awaiting_anything_else = True
            return (f"Your appointment is confirmed! "
                    f"Your booking ID is {booking_id}. "
                    "Is there anything else I can help you with?")
        self._reset()
        return ("I'm sorry, there was a problem completing your booking. "
                "Please try again or call the hospital directly.")

    # ── Cancellation flow ────────────────────────────────────────────────────
    def _handle_cancel(self) -> str:
        if not self.patient_name:
            return "Sure, I can help with that. May I have your full name?"
        if not self.phone:
            return "And what is your ten digit mobile number?"
        if len(self.phone) != 10 or not self.phone.isdigit():
            self.phone = None
            return "Please provide a valid ten digit mobile number."

        apps = get_appointment_for_cancellation(self.patient_name, self.phone)
        if not apps:
            self._reset()
            return ("I couldn't find any active appointments booked under that name "
                    "and mobile number.")

        if len(apps) > 1:
            self.cancel_appointments = apps
            lines = []
            for i, a in enumerate(apps, 1):
                lines.append(f"{i}. {a[1]} on {a[2]} at {a[3]}")
            self._reset()
            return ("I found multiple appointments: " + "; ".join(lines) +
                    ". Please call us directly to cancel a specific one.")

        app_id = apps[0][0]
        success = cancel_appointment(app_id)
        
        # Verify the DB actually reports cancelled
        if success and verify_appointment_cancelled(app_id):
            self._reset()
            return "Your appointment has been successfully cancelled."
            
        self._reset()
        return "I'm sorry, there was a problem cancelling your appointment. Please try again."

    # ── Check appointment ─────────────────────────────────────────────────────
    def _handle_check_appointment(self) -> str:
        if not self.patient_name:
            return "Sure, I can check that. May I have your full name?"
        if not self.phone:
            return "And what is your ten digit mobile number?"
        if len(self.phone) != 10 or not self.phone.isdigit():
            self.phone = None
            return "Please provide a valid ten digit mobile number."

        apps = get_appointment_for_cancellation(self.patient_name, self.phone)
        self._reset()
        if not apps:
            return "I couldn't find any active appointments under that name and number."
        a = apps[0]
        return (f"Yes, {a[6]} has an appointment with {a[1]} "
                f"at {a[5]} on {a[2]} at {a[3]}.")

    def _resume_flow(self) -> str:
        if self.current_intent == "book_appointment":
            return "Hello! Let me continue with your booking. " + self._handle_booking()
        if self.current_intent == "cancel_appointment":
            return "Hello! Let me continue with your cancellation. " + self._handle_cancel()
        return "Hello! How can I help you?"

    def _reset(self):
        self.hospital_name = None
        self.doctor_name = None
        self.doctor_row = None
        self.specialization = None
        self.appointment_date = None
        self.appointment_time = None
        self.patient_name = None
        self.phone = None
        self.phone_buffer = ""
        self.address = None
        self.current_intent = None
        self.confirmation_pending = False
        self.navigation_booking_pending = False
        self.awaiting_anything_else = False
        self.location_query = None
        self.nearby_results = []
        self.cancel_appointments = []

    @property
    def state(self) -> dict:
        fields = {
            "hospital_name": self.hospital_name,
            "doctor_name": self.doctor_name,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "patient_name": self.patient_name,
            "phone": self.phone,
            "address": self.address,
            "location_query": self.location_query,
        }
        return fields
