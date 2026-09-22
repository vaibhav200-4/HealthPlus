# ai_voice_agent/processor/hospital_db.py
import os
import sys
import re
import time
import math
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("hospital_app.hospital_db")

# Add backend directory to sys.path for importing SupabaseService & BookingService
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.supabase_client import SupabaseService
from app.services.booking_service import BookingService

def get_connection():
    """Compatibility function returning Supabase connection status check."""
    return SupabaseService.is_supabase_active()

def normalize_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).lower().strip()
    date_str = date_str.replace(" of ", " ")
    
    # Try YYYY-MM-DD directly
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    today = datetime.now()
    if "today" in date_str or "आज" in date_str:
        return today.strftime("%Y-%m-%d")
    if "tomorrow" in date_str or "कल" in date_str:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        if day in date_str:
            days_ahead = i - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12
    }
    
    found_month = None
    for m in months:
        if m in date_str:
            found_month = months[m]
            break
            
    day_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', date_str)
    
    if found_month and day_match:
        day = int(day_match.group(1))
        year = today.year
        year_match = re.search(r'\b(20\d{2})\b', date_str)
        if year_match:
            year = int(year_match.group(1))
        try:
            return datetime(year, found_month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None

def is_past_date(date_str: str) -> bool:
    """Returns True if normalized YYYY-MM-DD date is strictly in the past relative to today."""
    if not date_str:
        return False
    norm = normalize_date(date_str)
    if not norm:
        return False
    try:
        dt = datetime.strptime(norm, "%Y-%m-%d").date()
        today = datetime.now().date()
        return dt < today
    except Exception:
        return False

def normalize_time(time_str):
    if not time_str:
        return None
    time_str = str(time_str).upper().strip()
    
    # Strip dots from a.m. / p.m.
    time_str = re.sub(r'([AP])\.M\.', r'\1M', time_str)
    
    # Add space before AM/PM if missing (e.g. 1PM -> 1 PM)
    time_str = re.sub(r'(\d)(AM|PM)', r'\1 \2', time_str)
    
    # STT often confuses 12 PM for 12 AM. Nobody books a doctor at midnight.
    if "12 AM" in time_str:
        time_str = time_str.replace("12 AM", "12 PM")
        
    try:
        t = datetime.strptime(time_str, "%I %p")
        return t.strftime("%I:%M %p")
    except Exception:
        try:
            t = datetime.strptime(time_str, "%I:%M %p")
            return t.strftime("%I:%M %p")
        except Exception:
            pass

    # Try 24-hour HH:MM or HH:MM:SS format
    try:
        parts = time_str.split(":")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            h = int(parts[0])
            m = parts[1]
            period = "AM"
            if h == 0:
                h_12 = 12
            elif h == 12:
                h_12 = 12
                period = "PM"
            elif h > 12:
                h_12 = h - 12
                period = "PM"
            else:
                h_12 = h
            return f"{h_12:02d}:{m} {period}"
    except Exception:
        pass

    # Fallback for bare numbers like "4" or "4:30"
    match = re.match(r"^(\d{1,2})(?::(\d{2}))?$", time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = "AM"
        if 1 <= hour <= 7:
            hour += 12
        if hour == 0:
            h_12 = 12
        elif hour == 12:
            h_12 = 12
            period = "PM"
        elif hour > 12:
            h_12 = hour - 12
            period = "PM"
        else:
            h_12 = hour
        return f"{h_12:02d}:{minute:02d} {period}"
        
    return None

def warmup():
    try:
        active = SupabaseService.is_supabase_active()
        print(f"[DB] HealthPlus Supabase Warmup successful. Active: {active}")
    except Exception as e:
        print(f"[DB ERROR] Warmup failed: {e}")

def _is_test_hospital(hospital: dict) -> bool:
    """Return True if the hospital record is a test entry."""
    name = (hospital.get("hospital_name") or hospital.get("name") or "").strip().lower()
    h_id = str(hospital.get("id") or "").lower()
    return "test" in name or "h_test" in name or "h_test" in h_id


def _is_test_doctor(doctor: dict) -> bool:
    """Return True if the doctor record is a test/dummy entry that should be hidden."""
    name = (doctor.get("name") or "").strip()
    flags = [
        "[test]",
        "test specialist",
        "dr. bob",
        "dr bob",
    ]
    name_lower = name.lower()
    for flag in flags:
        if flag in name_lower:
            return True
    if re.search(r'\b[0-9a-f]{6}\b', name_lower):
        return True
    return False


_DB_CACHE = {}

def _cached_get_records(table_name, filters=None, ttl=30):
    import json
    cache_key = (table_name, json.dumps(filters or {}, sort_keys=True))
    now = time.time()
    if cache_key in _DB_CACHE:
        val, cached_time = _DB_CACHE[cache_key]
        if now - cached_time < ttl:
            return val
            
    records = SupabaseService.get_records(table_name, filters)
    _DB_CACHE[cache_key] = (records, now)
    return records

def _get_hospital_map():
    hospitals = _cached_get_records("hospitals")
    return {h.get("id"): h.get("hospital_name") for h in hospitals if h.get("id") and not _is_test_hospital(h)}

def get_all_context_string():
    try:
        hospitals = _cached_get_records("hospitals")
        doctors = _cached_get_records("doctors")
        
        context = "AVAILABLE HOSPITALS:\n"
        for h in hospitals:
            if _is_test_hospital(h):
                continue
            h_name = h.get("hospital_name") or h.get("name", "Hospital")
            city = h.get("city") or h.get("area") or "Indore"
            context += f"- {h_name} (Location: {city})\n"
        
        context += "\nAVAILABLE DOCTORS:\n"
        h_map = _get_hospital_map()
        for d in doctors:
            if _is_test_doctor(d):
                continue
            h_name = h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
            name = d.get("name")
            spec = d.get("specialization")
            fee = d.get("consultation_fee") or 500
            sched = d.get("availability") or "Mon-Sat 10:00 AM - 05:00 PM"
            context += f"- Dr. {name} (Specialist: {spec}, Fee: {fee}, Schedule: {sched}, Hospital: {h_name})\n"
        return context
    except Exception as e:
        print(f"[DB ERROR] Could not fetch context for LLM: {e}")
        return ""

def get_hospitals():
    hospitals = _cached_get_records("hospitals")
    result = []
    for h in hospitals:
        if _is_test_hospital(h):
            continue
        name = h.get("hospital_name") or h.get("name")
        address = ", ".join(filter(None, [h.get("street"), h.get("area"), h.get("city")])) or "Indore"
        if name:
            result.append((name, address))
    return result

def _get_all_doctors_merged():
    """All doctors live in public.doctors (D001-D010, D101-D124 verified). No hardcoded fallback."""
    return [d for d in (_cached_get_records("doctors") or []) if d.get("name") and not _is_test_doctor(d)]

def get_doctors():
    doctors = _get_all_doctors_merged()
    result = []
    for d in doctors:
        name = d.get("name")
        spec = d.get("specialization")
        fee = d.get("consultation_fee") or 500
        sched = d.get("availability") or "Mon-Sat 09:00 AM - 05:00 PM"
        if name and spec:
            result.append((name, spec, fee, sched))
    return result

def get_doctors_by_specialization(specialization, hospital_name=None):
    if not specialization:
        return []
    doctors = _get_all_doctors_merged()
    h_map = _get_hospital_map()
    result = []
    
    search_raw = str(specialization).lower().strip()

    for d in doctors:
        doc_spec = str(d.get("specialization") or "").lower().strip()
        if not doc_spec:
            continue
            
        matches = (search_raw in doc_spec or doc_spec in search_raw)
        if not matches:
            if ("gynec" in search_raw or "gynaec" in search_raw) and ("gynec" in doc_spec or "gynaec" in doc_spec):
                matches = True
            elif ("ortho" in search_raw) and ("ortho" in doc_spec):
                matches = True

        if matches:
            h_name = d.get("hospital_name") or h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
            if hospital_name and hospital_name.lower() not in h_name.lower():
                continue
            name = d.get("name")
            fee = d.get("consultation_fee") or 500
            sched = d.get("availability") or "Mon-Sat 09:00 AM - 05:00 PM"
            result.append((name, fee, sched, h_name))
    return result

def get_all_specializations():
    doctors = _get_all_doctors_merged()
    specs = set()
    for d in doctors:
        s = d.get("specialization")
        if s:
            specs.add(s)
    return list(specs)

def get_doctor_by_name(doctor_name):
    if not doctor_name:
        return None
    doctors = _get_all_doctors_merged()
    h_map = _get_hospital_map()
    clean_search = re.sub(r'^(dr\.?|doctor)\s+', '', doctor_name.strip(), flags=re.I).lower()
    if not clean_search:
        return None

    def _build_doc_tuple(d):
        doc_id = d.get("id")
        name = d.get("name")
        spec = d.get("specialization") or "General Medicine"
        fee = d.get("consultation_fee") or 500
        sched = d.get("availability") or "Mon-Sat 09:00 AM - 05:00 PM"
        h_name = d.get("hospital_name") or h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
        hospital_id = d.get("hospital_id")
        return (doc_id, name, spec, fee, sched, h_name, hospital_id)

    # Pass 1: Exact match on clean doctor name
    for d in doctors:
        d_name = d.get("name") or ""
        clean_d = re.sub(r'^(dr\.?|doctor)\s+', '', d_name.strip(), flags=re.I).lower()
        if clean_search == clean_d:
            return _build_doc_tuple(d)

    # Pass 2: Substring match
    for d in doctors:
        d_name = d.get("name") or ""
        clean_d = re.sub(r'^(dr\.?|doctor)\s+', '', d_name.strip(), flags=re.I).lower()
        if clean_search in clean_d or clean_d in clean_search:
            return _build_doc_tuple(d)

    return None

def get_doctors_by_hospital(hospital_name):
    if not hospital_name:
        return get_doctors()
    doctors = _get_all_doctors_merged()
    h_map = _get_hospital_map()
    result = []
    for d in doctors:
        h_name = d.get("hospital_name") or h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
        if hospital_name.lower() in h_name.lower() or h_name.lower() in hospital_name.lower():
            name = d.get("name")
            spec = d.get("specialization")
            fee = d.get("consultation_fee") or 500
            sched = d.get("availability") or "Mon-Sat 09:00 AM - 05:00 PM"
            result.append((name, spec, fee, sched, h_name))
    return result

def is_doctor_available_on_date(doctor_info, appointment_date: str):
    """
    Parses doctor's availability string (e.g. 'Monday to Saturday' or 'Monday, Wednesday and Friday')
    and checks if the day of week of appointment_date matches.
    Returns (is_available, day_name).
    """
    if not appointment_date:
        return True, ""
    
    norm_d = normalize_date(appointment_date)
    if not norm_d:
        return True, ""
        
    try:
        dt = datetime.strptime(norm_d, "%Y-%m-%d")
        day_name = dt.strftime("%A")
    except Exception:
        return True, ""

    avail_str = ""
    if isinstance(doctor_info, (list, tuple)) and len(doctor_info) > 4:
        avail_str = str(doctor_info[4])
    elif isinstance(doctor_info, dict):
        avail_str = str(doctor_info.get("availability") or doctor_info.get("schedule") or "")

    if not avail_str:
        return True, day_name

    avail_lower = avail_str.lower()
    day_lower = day_name.lower()

    if "monday to saturday" in avail_lower or "mon-sat" in avail_lower:
        if day_lower == "sunday":
            return False, day_name
    elif "monday to friday" in avail_lower or "mon-fri" in avail_lower:
        if day_lower in ("saturday", "sunday"):
            return False, day_name
    elif "tuesday to saturday" in avail_lower or "tue-sat" in avail_lower:
        if day_lower in ("sunday", "monday"):
            return False, day_name
    else:
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        mentioned = [d for d in days if d in avail_lower]
        if mentioned and day_lower not in mentioned:
            return False, day_name

    return True, day_name


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
    h, m = total // 60, total % 60
    if h == 0:
        return f"12:{m:02d} AM"
    elif h == 12:
        return f"12:{m:02d} PM"
    elif h > 12:
        return f"{h - 12:02d}:{m:02d} PM"
    else:
        return f"{h:02d}:{m:02d} AM"


def _day_matches(day_of_week, weekday_idx: int) -> bool:
    if not day_of_week:
        return False
    return str(day_of_week).strip().lower()[:3] == _DAY_PREFIXES[weekday_idx]


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
            # schedules table has no rows for this doctor: reuse ScheduleService.get_doctor_available_slots
            from app.services.schedule_service import ScheduleService
            avail_slots = ScheduleService.get_doctor_available_slots(doc_id, norm_date)
            matching_slot = next((
                s for s in avail_slots 
                if (normalize_time(s.get("start_time")) == norm_time or s.get("start_time") == norm_time)
            ), None)
            if not matching_slot or not matching_slot.get("available"):
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

def get_appointment_by_id(app_id):
    return SupabaseService.get_record_by_id("appointments", app_id)

def get_patient_appointments(phone):
    if not phone:
        return []
    apps = SupabaseService.get_records("appointments")
    active = ["confirmed", "pending", "booked"]
    res = []
    for a in apps:
        p_phone = a.get("patient_phone") or a.get("phone") or ""
        if phone in p_phone and a.get("status") in active:
            res.append((
                a.get("id"),
                a.get("doctor_name"),
                a.get("date") or a.get("appointment_date"),
                a.get("start_time") or a.get("appointment_time"),
                a.get("status"),
                a.get("hospital_name"),
                a.get("patient_name")
            ))
    return res

def get_user_appointments(user_id):
    """
    Fetch all appointments for a logged-in user_id from Supabase and split them
    into 'upcoming' and 'previous' lists using robust date parsing and status checks.
    """
    if not user_id:
        return {"upcoming": [], "previous": []}
        
    records = SupabaseService.get_records("appointments", {"user_id": user_id})
    if not records:
        return {"upcoming": [], "previous": []}
        
    today = datetime.now().date()
    upcoming = []
    previous = []
    
    active_statuses = {"confirmed", "pending", "booked", "active"}
    
    for r in records:
        date_raw = r.get("date") or r.get("appointment_date") or ""
        status = (r.get("status") or "confirmed").lower()
        
        parsed_date = None
        if date_raw:
            try:
                parsed_date = datetime.strptime(str(date_raw)[:10], "%Y-%m-%d").date()
            except Exception:
                parsed_date = None
                
        app_info = {
            "id": r.get("id"),
            "doctor_name": r.get("doctor_name") or "Doctor",
            "hospital_name": r.get("hospital_name") or "Clinic",
            "date": str(parsed_date) if parsed_date else str(date_raw),
            "time": r.get("start_time") or r.get("appointment_time") or "TBD",
            "status": status,
            "patient_name": r.get("patient_name") or ""
        }
        
        if status in ("completed", "cancelled") or (parsed_date and parsed_date < today):
            previous.append(app_info)
        elif status in active_statuses or (parsed_date and parsed_date >= today):
            upcoming.append(app_info)
        else:
            previous.append(app_info)
            
    upcoming.sort(key=lambda x: x["date"])
    previous.sort(key=lambda x: x["date"], reverse=True)
    
    return {"upcoming": upcoming, "previous": previous}


def get_appointment_for_cancellation(patient_name, phone):
    apps = SupabaseService.get_records("appointments")
    active = ["confirmed", "pending", "booked"]
    res = []
    for a in apps:
        p_phone = a.get("patient_phone") or a.get("phone") or ""
        p_name = a.get("patient_name") or ""
        
        match_phone = phone and (phone in p_phone)
        match_name = patient_name and (patient_name.lower() in p_name.lower() or p_name.lower() in patient_name.lower())
        
        if (match_phone or match_name) and a.get("status") in active:
            res.append((
                a.get("id"),
                a.get("doctor_name"),
                a.get("date") or a.get("appointment_date"),
                a.get("start_time") or a.get("appointment_time"),
                a.get("status"),
                a.get("hospital_name"),
                a.get("patient_name")
            ))
    return res

def cancel_appointment(appointment_id):
    updated = SupabaseService.update_record("appointments", appointment_id, {"status": "cancelled"})
    return updated is not None

def verify_appointment_booked(app_id):
    app = SupabaseService.get_record_by_id("appointments", app_id)
    if not app:
        return False
    return app.get("status") in ["confirmed", "pending", "booked"]

def verify_appointment_cancelled(app_id):
    app = SupabaseService.get_record_by_id("appointments", app_id)
    if not app:
        return True
    return app.get("status") == "cancelled"

def get_hospital_address(hospital_name):
    if not hospital_name:
        return None
    hospitals = SupabaseService.get_records("hospitals")
    for h in hospitals:
        name = h.get("hospital_name") or h.get("name") or ""
        if hospital_name.lower() in name.lower() or name.lower() in hospital_name.lower():
            address = ", ".join(filter(None, [h.get("street"), h.get("area"), h.get("city")])) or "HealthPlus Campus"
            return (name, address)
    return (hospital_name, "HealthPlus Medical Center, City Campus")


# ---------------------------------------------------------------------------
# Dynamic search – real-world hospitals/clinics via Nominatim + Overpass API
# These results are INFO-ONLY (not bookable through HealthPlus).
# ---------------------------------------------------------------------------

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_ENDPOINTS = [
    # mail.ru mirror was the only one that reliably responded in production testing
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
_GEOCODE_CACHE: dict = {}
_OVERPASS_CACHE: dict = {}
_CITY_SEARCH_CACHE: dict = {}
_CACHE_TTL = 300  # 5 minutes


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two points."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def clean_location_string(raw: str) -> str:
    if not raw:
        return ""
    text = str(raw).strip()
    # Remove conversational leading phrases
    text = re.sub(
        r'^(?:i\s+am\s+located\s+in|located\s+in|my\s+location\s+is|i\s+live\s+in|location\s+is|in\s+|at\s+|near\s+)\s*',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()
    # Remove trailing punctuation
    text = re.sub(r'[\.,!\?]+$', '', text).strip()
    return text


def geocode_location(query: str) -> dict | None:
    """Geocode a city/area name to lat/lng using OpenStreetMap Nominatim.
    Returns {"lat": float, "lng": float, "display_name": str} or None.
    """
    import httpx

    query = clean_location_string(query)
    clean_q = query.lower()
    if not clean_q:
        return None

    now = time.time()
    if clean_q in _GEOCODE_CACHE:
        ts, data = _GEOCODE_CACHE[clean_q]
        if now - ts < _CACHE_TTL:
            return data

    headers = {"User-Agent": "HealthPlus-VoiceAgent/1.0 (contact@healthplus.example)"}
    params = {"q": query, "format": "json", "limit": 1}

    try:
        r = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=3.0)
        if r.status_code == 200:
            results = r.json()
            if results:
                item = results[0]
                data = {
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "display_name": item.get("display_name", query),
                }
                _GEOCODE_CACHE[clean_q] = (now, data)
                return data
    except Exception as e:
        logger.warning(f"Geocode failed for '{query}': {e}")

    return None


def search_nearby_facilities(lat: float, lng: float, radius_m: int = 5000,
                              specialty: str | None = None) -> list[dict]:
    """Query Overpass API for real hospitals/clinics/doctors near coordinates.
    Returns list of facility dicts sorted by distance. INFO-ONLY, not bookable.
    """
    import httpx

    spec_key = (specialty or "").strip().lower()
    cache_key = (round(lat, 3), round(lng, 3), radius_m, spec_key)
    now = time.time()

    if cache_key in _OVERPASS_CACHE:
        ts, cached = _OVERPASS_CACHE[cache_key]
        if now - ts < _CACHE_TTL:
            return cached

    # Targeted, fast query for medical facilities
    overpass_query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"doctors|clinic|hospital"](around:{radius_m},{lat},{lng});
      way["amenity"~"doctors|clinic|hospital"](around:{radius_m},{lat},{lng});
      node["healthcare"~"hospital|clinic|doctor|centre"](around:{radius_m},{lat},{lng});
    );
    out center 25;
    """

    headers = {"User-Agent": "HealthPlus-VoiceAgent/1.0 (contact@healthplus.example)"}
    elements = []

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            r = httpx.post(endpoint, data={"data": overpass_query}, headers=headers, timeout=3.0)
            if r.status_code == 200:
                elements = r.json().get("elements", [])
                if elements:
                    break
            else:
                logger.warning(f"Overpass endpoint {endpoint} returned status {r.status_code}")
        except Exception as e:
            logger.warning(f"Overpass endpoint {endpoint} failed: {e}")

    facilities = []

    for el in elements:
        tags = el.get("tags", {})
        el_lat = el.get("lat") or el.get("center", {}).get("lat")
        el_lng = el.get("lon") or el.get("center", {}).get("lon")
        if el_lat is None or el_lng is None:
            continue

        # Skip pharmacies/drugstores — we only want hospitals, clinics, doctors
        amenity_val = tags.get("amenity", "").lower()
        healthcare_val = tags.get("healthcare", "").lower()
        if amenity_val in ("pharmacy", "veterinary") or healthcare_val in ("pharmacy",):
            continue

        osm_spec = tags.get("healthcare:speciality") or tags.get("speciality") or amenity_val
        raw_name = tags.get("name") or tags.get("name:en")
        name = raw_name if raw_name else (f"Dr. {osm_spec.title()} Clinic" if osm_spec else "Medical Centre")

        # Specialty filter
        if spec_key:
            combined = f"{osm_spec} {name} {tags.get('amenity', '')}".lower()
            if spec_key not in combined:
                continue

        dist = _haversine(lat, lng, float(el_lat), float(el_lng))

        phone = tags.get("phone") or tags.get("contact:phone") or tags.get("phone:mobile")

        addr_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:suburb"),
            tags.get("addr:city"),
            tags.get("addr:postcode"),
        ]
        address = ", ".join(p for p in addr_parts if p) or tags.get("addr:full") or f"Near {name}"

        facilities.append({
            "name": name,
            "specialty": (osm_spec or specialty or "General").replace("_", " ").title(),
            "address": address,
            "phone": phone,
            "distance_meters": round(dist, 1),
            "amenity_type": tags.get("amenity", "clinic").replace("_", " ").title(),
            "bookable": False,
        })

    facilities.sort(key=lambda x: x["distance_meters"])
    facilities = facilities[:20]

    _OVERPASS_CACHE[cache_key] = (now, facilities)
    return facilities


def _search_facilities_nominatim(city_name: str, specialty: str | None = None) -> list[dict]:
    """Fallback: query Nominatim POI search directly for medical facilities in city.
    Calculates real Haversine distances from city center, deduplicates facility names,
    and filters out non-medical nodes like highways/roads. Fast (<0.5s) and reliable.
    """
    import httpx

    city_name = clean_location_string(city_name)
    if not city_name:
        return []

    geo = geocode_location(city_name)
    city_lat = geo["lat"] if geo else 19.0760
    city_lng = geo["lng"] if geo else 72.8777

    spec_str = f" {specialty}" if specialty else ""
    query = f"hospitals{spec_str} in {city_name}"
    headers = {"User-Agent": "HealthPlus-VoiceAgent/1.0 (contact@healthplus.example)"}
    params = {"q": query, "format": "json", "limit": 20}
    try:
        r = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=3.0)
        if r.status_code == 200:
            results = r.json()
            facilities = []
            seen_names = set()

            for item in results:
                display = item.get("display_name", "")
                name = display.split(",")[0].strip() if display else f"Hospital in {city_name}"
                if not name:
                    continue

                name_lower = name.lower()
                # Skip roads, highways, junctions, flyovers
                if any(w in name_lower for w in ("highway", "road", "expressway", "flyover", "marg", "naka", "bridge", "station", "junction")):
                    continue

                # Case-insensitive deduplication
                clean_name_key = re.sub(r'[^a-z0-9]', '', name_lower)
                if clean_name_key in seen_names:
                    continue
                seen_names.add(clean_name_key)

                item_lat = float(item["lat"]) if "lat" in item else city_lat
                item_lng = float(item["lon"]) if "lon" in item else city_lng
                dist_m = _haversine(city_lat, city_lng, item_lat, item_lng)

                facilities.append({
                    "name": name,
                    "specialty": specialty.title() if specialty else "General",
                    "address": display or f"Near {city_name}",
                    "phone": None,
                    "distance_meters": round(dist_m, 1),
                    "amenity_type": "Hospital",
                    "bookable": False,
                })

            facilities.sort(key=lambda x: x["distance_meters"])
            return facilities
    except Exception as e:
        logger.warning(f"Nominatim POI search fallback failed for '{city_name}': {e}")
    return []


def search_facilities_by_city(city_name: str, specialty: str | None = None) -> list[dict]:
    """High-level: geocode a city name then search nearby facilities.
    Main entry point for the voice agent's nearby_search intent.
    Tries Nominatim POI search first for sub-second speed (<0.5s), with Overpass fallback.
    """
    city_name = clean_location_string(city_name)
    if not city_name:
        return []

    cache_key = (city_name.lower(), (specialty or "").lower())
    now = time.time()
    if cache_key in _CITY_SEARCH_CACHE:
        ts, cached = _CITY_SEARCH_CACHE[cache_key]
        if now - ts < _CACHE_TTL:
            return cached

    facilities = _search_facilities_nominatim(city_name, specialty)
    if not facilities:
        geo = geocode_location(city_name)
        if geo:
            facilities = search_nearby_facilities(geo["lat"], geo["lng"], radius_m=10000, specialty=specialty)

    if facilities:
        _CITY_SEARCH_CACHE[cache_key] = (now, facilities)
    return facilities
