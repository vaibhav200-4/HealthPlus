# Voice agent patches

Grounded in the files you pasted and your Supabase schema export.
NOT seen: `backend/app/database/supabase_client.py` and `backend/app/services/booking_service.py`.
`create_appointment` below still calls `BookingService.create_appointment` with the same keyword
arguments your current code uses; only `end_time` changes. Check that file accepts it.

---

## A. `ai_voice_agent/processor/hospital_db.py`

### A1. `normalize_time`: last line

Unparseable input must not silently become 9 AM. Replace the final line:

```python
    return "09:00:00"
```
with:
```python
    return None
```

### A2. `get_doctor_by_name`: final `return`

Append `hospital_id` (index 6). Existing callers only use indexes 0 to 5, so nothing breaks.

```python
            hospital_id = d.get("hospital_id")
            return (doc_id, name, spec, fee, sched, h_name, hospital_id)
```

### A3. Add these helpers (above `check_slot_available`) and replace `check_slot_available` and `create_appointment`

```python
_ACTIVE_STATUSES = ("confirmed", "pending", "booked", "checked_in", "in_progress")
_DAY_PREFIXES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_ANON_USER_ID = "00000000-0000-0000-0000-000000000001"


def _time_to_minutes(value):
    """'09:30', '09:30:00', '9 AM', '2:15 PM' -> minutes since midnight, or None."""
    if not value:
        return None
    m = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?(?::\d{2})?\s*([ap]m)?\s*$", str(value).strip().lower())
    if not m:
        return None
    hour, minute, meridiem = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if meridiem == "pm" and hour < 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def _minutes_to_hms(total: int) -> str:
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}:00"


def _day_matches(day_of_week, weekday_idx: int) -> bool:
    # Assumes day names ("Monday", "Mon"). If diagnostics #10 shows numbers, adjust here.
    if not day_of_week:
        return False
    return str(day_of_week).strip().lower()[:3] == _DAY_PREFIXES[weekday_idx]


def _availability_window(avail_str):
    """'Monday to Saturday, 10:00 AM - 2:00 PM' -> (600, 840). None if no time range is found."""
    text = str(avail_str or "").lower().replace(".", "")
    m = re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*(?:-|–|to)\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", text)
    if not m:
        return None
    s, e = _time_to_minutes(m.group(1)), _time_to_minutes(m.group(2))
    return (s, e) if (s is not None and e is not None and s < e) else None


def _safe_records(table, filters=None):
    """Uncached, exception-safe read (availability must never use the 30 s cache)."""
    try:
        return SupabaseService.get_records(table, filters) or []
    except Exception as e:
        logger.warning(f"[DB] read failed for {table} {filters}: {e}")
        return []


def check_slot_available(doctor_name, appointment_date, appointment_time):
    norm_date = normalize_date(appointment_date)
    norm_time = normalize_time(appointment_time)
    if not norm_date or not norm_time:
        return False  # unparseable date/time: make the caller ask again

    doc = get_doctor_by_name(doctor_name)
    if doc:
        ok, _ = is_doctor_available_on_date(doc, norm_date)
        if not ok:
            return False

    req_min = _time_to_minutes(norm_time)
    doc_id = str(doc[0]) if doc else None
    hospital_id = doc[6] if (doc and len(doc) > 6) else None

    if doc_id:
        # Doctor leave / hospital holiday / blocked slot
        if _safe_records("doctor_leaves", {"doctor_id": doc_id, "leave_date": norm_date}):
            return False
        if hospital_id and _safe_records("hospital_holidays", {"hospital_id": hospital_id, "holiday_date": norm_date}):
            return False
        for b in _safe_records("blocked_slots", {"doctor_id": doc_id, "slot_date": norm_date}):
            if _time_to_minutes(b.get("start_time")) == req_min:
                return False

        # Weekly schedule (enforced only when the doctor has schedule rows)
        weekday = datetime.strptime(norm_date, "%Y-%m-%d").weekday()
        rows = [r for r in _safe_records("schedules", {"doctor_id": doc_id}) if r.get("is_active") is not False]
        if rows:
            todays = [r for r in rows if _day_matches(r.get("day_of_week"), weekday)]
            if not todays:
                return False
            in_window = False
            for r in todays:
                s, e = _time_to_minutes(r.get("start_time")), _time_to_minutes(r.get("end_time"))
                if s is not None and e is not None and s <= req_min < e:
                    in_window = True
                    break
            if not in_window:
                return False
        else:
            # schedules table has no rows for this doctor: enforce the hours in doctors.availability text
            window = _availability_window(doc[4] if len(doc) > 4 else "")
            if window and not (window[0] <= req_min < window[1]):
                return False

        # Existing bookings, filtered in the query (no 1000-row truncation)
        for a in _safe_records("appointments", {"doctor_id": doc_id, "date": norm_date}):
            if a.get("status") in _ACTIVE_STATUSES and _time_to_minutes(a.get("start_time")) == req_min:
                return False
    else:
        for a in _safe_records("appointments", {"date": norm_date}):
            if a.get("status") in _ACTIVE_STATUSES and _time_to_minutes(a.get("start_time")) == req_min:
                if doctor_name and doctor_name.lower() in (a.get("doctor_name") or "").lower():
                    return False
    return True


def create_appointment(patient_name, phone, address, doctor_name, appointment_date, appointment_time, user_id=None):
    norm_date = normalize_date(appointment_date)
    norm_time = normalize_time(appointment_time)
    doc = get_doctor_by_name(doctor_name)
    if not (norm_date and norm_time and doc):
        print(f"[DB ERROR] Refusing to book: date={norm_date!r} time={norm_time!r} doctor_found={bool(doc)}")
        return None

    doc_id, doc_real_name, hospital_name = str(doc[0]), doc[1], doc[5]
    hospital_id = doc[6] if len(doc) > 6 else None

    slot_minutes = 30
    for row in _safe_records("schedules", {"doctor_id": doc_id}):
        if row.get("slot_duration_minutes"):
            slot_minutes = int(row["slot_duration_minutes"])
            break
    end_time = _minutes_to_hms(_time_to_minutes(norm_time) + slot_minutes)

    voice_user_id = user_id or _ANON_USER_ID
    notes = f"Booked via Voice AI Assistant. Address: {address or 'N/A'}"

    try:
        success, msg, app_data = BookingService.create_appointment(
            user_id=voice_user_id,
            doctor_id=doc_id,
            doctor_name=doc_real_name,
            hospital_name=hospital_name,
            date=norm_date,
            start_time=norm_time,
            end_time=end_time,
            patient_name=patient_name,
            patient_phone=phone or "",
            patient_email="",
            notes=notes,
        )
        if success and app_data and app_data.get("id"):
            return app_data["id"]
        if not success:
            print(f"[DB ERROR] BookingService reported failure: {msg}")
            return None
    except Exception as e:
        print(f"[DB WARN] BookingService call failed, trying direct insert: {e}")

    # Direct fallback: ONLY columns that exist on public.appointments
    inserted = SupabaseService.insert_record("appointments", {
        "user_id": voice_user_id,
        "doctor_id": doc_id,
        "doctor_name": doc_real_name,
        "hospital_id": hospital_id,
        "hospital_name": hospital_name,
        "date": norm_date,
        "start_time": norm_time,
        "end_time": end_time,
        "patient_name": patient_name,
        "patient_phone": phone or "",
        "patient_email": "",
        "notes": notes,
        "status": "confirmed",
        "idempotency_key": f"voice:{voice_user_id}:{doc_id}:{norm_date}:{norm_time}",
    })
    if inserted and inserted.get("id"):
        return inserted.get("id")
    return None
```

---

## B. `ai_voice_agent/processor/hospital_handler.py`

### B1. `_normalize_hospital`: alias loop (short replies like "ha" matched "bhawarkuan")

Replace:
```python
    for alias, h_name in HOSPITAL_ALIASES.items():
        if alias in lower_raw or lower_raw in alias:
            return h_name
```
with:
```python
    for alias, h_name in HOSPITAL_ALIASES.items():
        if alias in lower_raw or (len(lower_raw) >= 4 and lower_raw in alias):
            return h_name
```

### B2. `_resolve_user_profile`: your `profiles` column is `name`, and `patients` has no name/phone

```python
    def _resolve_user_profile(self):
        """Auto-populate patient_name and phone from public.profiles for a logged-in user."""
        if not self.user_id or self.user_id == "00000000-0000-0000-0000-000000000001":
            return
        try:
            from app.database.supabase_client import SupabaseService
            profiles = SupabaseService.get_records("profiles", {"id": self.user_id})
            if profiles:
                p = profiles[0]
                if not self.patient_name and p.get("name"):
                    self.patient_name = p.get("name")
                if not self.phone and p.get("phone"):
                    digits = normalize_phone(p.get("phone"))
                    if len(digits) >= 10:
                        self.phone = digits[-10:]  # last 10 digits: strips a +91 prefix
        except Exception as e:
            print(f"[PROFILE RESOLVE ERROR] {e}")
```

### B3. `_get_user_first_name`: delete the dead `patients` lookup

Delete this block (the `patients` table has no `name` column):
```python
                patients = _cached_get_records("patients", {"profile_id": self.user_id})
                if patients and len(patients) > 0 and patients[0].get("name"):
                    self.user_name = str(patients[0].get("name")).strip().split()[0].capitalize()
                    return self.user_name
```

### B4. `_merge_entities`: phone slicing

Spoken numbers are 10 digits, but anything with a country code is truncated to the wrong number. Replace
`self.phone = digits[:10]` with `self.phone = digits[-10:]` (both places it appears in `_merge_entities` and the
fallback block in `process_intent`).

### B5. `_handle_confirmation`: hardcoded fee

Replace the returned f-string's `fee rupees 800` with a computed value. Before the `return`:
```python
                fee = int(float(self.doctor_row[3])) if (self.doctor_row and self.doctor_row[3]) else 0
```
and in the string use `fee rupees {fee}` and `{_fmt_doc(self.doctor_row) if self.doctor_row else self.doctor_name}`.

---

## C. `backend/app/api/voice.py`: SECURITY FIX (user_id was trusted from the query string)

Replace the whole WebSocket signature and the resolution block:

```python
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
    # ... rest of the function unchanged
```

Also confirm `from pipecat_web_pipeline import create_pipecat_web_session` matches the real filename.

---

## D. Web pipeline file (the one defining `WebPipecatProcessor`): unblock the event loop

In `_generate_response`, replace:
```python
                rule_intent = _rule_based_intent(user_text)
```
with:
```python
                rule_intent = await asyncio.to_thread(_rule_based_intent, user_text)
```
and replace:
```python
                local_entities = _extract_voice_entities(user_text)
```
with:
```python
                local_entities = await asyncio.to_thread(_extract_voice_entities, user_text)
```

---

## E. Delete / clean up

- Delete the Neon `setup_db()` script (it drops `appointments`).
- Remove the `NEON_DATABASE_URL` check from `ai_voice_agent/bot.py`.

---

## F. `hospital_db.py`: remove the hardcoded `MASTER_DOCTORS` (verified redundant)

Your live DB already contains all 34 doctors (D001-D010, D101-D124) and all 10 hospitals (H001-H005, H_SEED_1-5).
Delete the whole `MASTER_DOCTORS = [ ... ]` list and replace `_get_all_doctors_merged` with:

```python
def _get_all_doctors_merged():
    """All doctors live in public.doctors (D001-D010, D101-D124 verified). No hardcoded fallback."""
    return [d for d in (_cached_get_records("doctors") or []) if d.get("name") and not _is_test_doctor(d)]
```

Tradeoff: if Supabase is unreachable the agent now finds no doctors instead of answering from the hardcoded list.
Names D101+ are stored without "Dr." ("Amit Shah"); the code already adds the prefix when speaking, so leave them.

---

## G. `hospital_handler.py`: specialization spelling and aliases

The DB stores **Orthopedics** and **Gynecology**, and has **no Gastroenterology doctors**. Replace the whole
`SPECIALIZATION_ALIASES` dict with the one below and change the alias loop in `_normalize_specialization`.

```python
SPECIALIZATION_ALIASES = {
    "cardio": "Cardiology", "cardiologist": "Cardiology", "cardiology": "Cardiology",
    "cardiac": "Cardiology", "heart": "Cardiology",
    "cardio movies": "Cardiology", "cardio logistics": "Cardiology", "bookend cardiologist": "Cardiology",
    "ortho": "Orthopedics", "orthopedics": "Orthopedics", "orthopaedic": "Orthopedics",
    "orthopaedics": "Orthopedics", "orthopedist": "Orthopedics", "orthopaedist": "Orthopedics",
    "bone": "Orthopedics",
    "derma": "Dermatology", "dermatologist": "Dermatology", "dermatology": "Dermatology", "skin": "Dermatology",
    "gynec": "Gynecology", "gynaec": "Gynecology", "gynecology": "Gynecology", "gynaecology": "Gynecology",
    "gynecologist": "Gynecology", "gynaecologist": "Gynecology", "women": "Gynecology",
    "neuro": "Neurology", "neurologist": "Neurology", "neurology": "Neurology",
    "pediatric": "Pediatrics", "paediatric": "Pediatrics", "pediatrician": "Pediatrics",
    "paediatrician": "Pediatrics", "child specialist": "Pediatrics", "child doctor": "Pediatrics",
    "psych": "Psychiatry", "psychiatrist": "Psychiatry", "psychiatry": "Psychiatry",
    "pulmo": "Pulmonology", "pulmonologist": "Pulmonology", "pulmonology": "Pulmonology",
    "lung": "Pulmonology", "lungs": "Pulmonology",
    "endocrin": "Endocrinology", "endocrinologist": "Endocrinology", "endocrinology": "Endocrinology",
    "diabetes": "Endocrinology", "thyroid": "Endocrinology",
    "surgeon": "General Surgery", "surgery": "General Surgery", "general surgery": "General Surgery",
    "general medicine": "General Medicine", "general physician": "General Medicine", "physician": "General Medicine",
}
```

In `_normalize_specialization`, replace the alias loop with (short replies such as "he" no longer match "heart"):

```python
    for alias, std_spec in SPECIALIZATION_ALIASES.items():
        if alias in lower_raw or (len(lower_raw) >= 4 and lower_raw in alias):
            return std_spec
```

Also change the hardcoded fallback lists `["Cardiology", "Gastroenterology", "Orthopaedics", "Gynaecology", ...]`
(in `_normalize_specialization`, `_handle_patient_navigation`, and `llm.py`) to the DB spelling:
`["Cardiology", "Dermatology", "General Medicine", "Gynecology", "Neurology", "Orthopedics", "Pediatrics"]`.

---

## H. `hospital_handler.py`: hospital aliases

Delete the alias blocks for **Care First Hospital**, **City Heart Institute** and **Apex Healthcare Clinic**
(they do not exist in your DB). Add the three hospitals that have no aliases:

```python
    # Central City Hospital
    "central city": "Central City Hospital",
    "central city hospital": "Central City Hospital",

    # Harmony Care Hospital
    "harmony": "Harmony Care Hospital",
    "harmony care": "Harmony Care Hospital",
    "harmony hospital": "Harmony Care Hospital",

    # Lifeline Advanced Hospital
    "lifeline": "Lifeline Advanced Hospital",
    "life line": "Lifeline Advanced Hospital",
    "lifeline advanced": "Lifeline Advanced Hospital",
    "life line advanced": "Lifeline Advanced Hospital",
```

---

## I. Anonymous users: `appointments.user_id` has a FOREIGN KEY to `profiles(id)`

The anonymous sentinel id `00000000-0000-0000-0000-000000000001` only works if a profile with that id exists.
Otherwise every anonymous booking fails at the database. Check first (run one query at a time):

```sql
select id, email, role from public.profiles where id = '00000000-0000-0000-0000-000000000001';
select count(*) from public.appointments where user_id = '00000000-0000-0000-0000-000000000001';
```

If no such profile exists, pick ONE:

**Option 1: allow anonymous/phone bookings.** Create the guest profile (it will appear in admin user lists):
```sql
insert into public.profiles (id, name, email, role)
values ('00000000-0000-0000-0000-000000000001', 'Voice Guest', 'voice-guest@internal.invalid', 'user')
on conflict (id) do nothing;
```

**Option 2: web users must be logged in to book.** Add at the very top of `_handle_booking` in `hospital_handler.py`:
```python
        if self.user_id == "00000000-0000-0000-0000-000000000001":
            self._reset()
            return "Please log in to your account to book by voice. I can still help with doctor and hospital information."
```

---

## J. Dead status values

`appointments.status` only allows: pending, confirmed, checked_in, in_progress, completed, cancelled, no_show.
The code also checks "booked" and "active", which can never occur. Harmless; remove them when you next touch those lists.