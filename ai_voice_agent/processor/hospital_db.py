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
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
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
        if found_month < today.month:
            year += 1
        try:
            return datetime(year, found_month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None

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
        return t.strftime("%H:%M:00")
    except:
        try:
            t = datetime.strptime(time_str, "%I:%M %p")
            return t.strftime("%H:%M:00")
        except:
            pass
            
    # Fallback for bare numbers like "4" or "4:30"
    match = re.match(r"^(\d{1,2})(?::(\d{2}))?$", time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        if 1 <= hour <= 7:
            hour += 12
        return f"{hour:02d}:{minute:02d}:00"
        
    return "09:00:00"

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


def _get_hospital_map():
    hospitals = SupabaseService.get_records("hospitals")
    return {h.get("id"): h.get("hospital_name") for h in hospitals if h.get("id") and not _is_test_hospital(h)}

def get_all_context_string():
    try:
        hospitals = SupabaseService.get_records("hospitals")
        doctors = SupabaseService.get_records("doctors")
        
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
    hospitals = SupabaseService.get_records("hospitals")
    result = []
    for h in hospitals:
        if _is_test_hospital(h):
            continue
        name = h.get("hospital_name") or h.get("name")
        address = ", ".join(filter(None, [h.get("street"), h.get("area"), h.get("city")])) or "Indore"
        if name:
            result.append((name, address))
    return result

MASTER_DOCTORS = [
    # Sunrise Multispeciality Hospital (H001)
    {"id": "D001", "hospital_id": "H001", "hospital_name": "Sunrise Multispeciality Hospital", "name": "Dr. Arjun Mehta", "specialization": "Cardiology", "consultation_fee": 900, "availability": "Monday to Saturday, 10:00 AM - 2:00 PM"},
    {"id": "D002", "hospital_id": "H001", "hospital_name": "Sunrise Multispeciality Hospital", "name": "Dr. Neha Sharma", "specialization": "Neurology", "consultation_fee": 800, "availability": "Monday, Wednesday and Friday, 3:00 PM - 6:00 PM"},
    {"id": "D101", "hospital_id": "H001", "hospital_name": "Sunrise Multispeciality Hospital", "name": "Dr. Amit Shah", "specialization": "General Medicine", "consultation_fee": 600, "availability": "Monday to Saturday, 9:00 AM - 1:00 PM"},
    {"id": "D102", "hospital_id": "H001", "hospital_name": "Sunrise Multispeciality Hospital", "name": "Dr. Shalini Verma", "specialization": "Dermatology", "consultation_fee": 700, "availability": "Tuesday to Saturday, 2:00 PM - 5:00 PM"},

    # Green Valley Medical Centre (H002)
    {"id": "D003", "hospital_id": "H002", "hospital_name": "Green Valley Medical Centre", "name": "Dr. Riya Kapoor", "specialization": "Pediatrics", "consultation_fee": 700, "availability": "Monday to Friday, 9:00 AM - 1:00 PM"},
    {"id": "D004", "hospital_id": "H002", "hospital_name": "Green Valley Medical Centre", "name": "Dr. Vikram Joshi", "specialization": "Dermatology", "consultation_fee": 650, "availability": "Tuesday to Saturday, 4:00 PM - 7:00 PM"},
    {"id": "D103", "hospital_id": "H002", "hospital_name": "Green Valley Medical Centre", "name": "Dr. Suresh Nambiar", "specialization": "Cardiology", "consultation_fee": 850, "availability": "Monday to Saturday, 11:00 AM - 3:00 PM"},
    {"id": "D104", "hospital_id": "H002", "hospital_name": "Green Valley Medical Centre", "name": "Dr. Pooja Gupta", "specialization": "General Medicine", "consultation_fee": 550, "availability": "Monday to Saturday, 10:00 AM - 2:00 PM"},

    # Central City Hospital (H003)
    {"id": "D005", "hospital_id": "H003", "hospital_name": "Central City Hospital", "name": "Dr. Sameer Patel", "specialization": "Endocrinology", "consultation_fee": 1000, "availability": "Monday to Friday, 11:00 AM - 3:00 PM"},
    {"id": "D006", "hospital_id": "H003", "hospital_name": "Central City Hospital", "name": "Dr. Ananya Rao", "specialization": "Orthopedics", "consultation_fee": 850, "availability": "Monday, Tuesday, Thursday and Saturday, 2:00 PM - 6:00 PM"},
    {"id": "D105", "hospital_id": "H003", "hospital_name": "Central City Hospital", "name": "Dr. Harshvardhan Kapoor", "specialization": "Cardiology", "consultation_fee": 950, "availability": "Monday to Saturday, 10:00 AM - 2:00 PM"},
    {"id": "D106", "hospital_id": "H003", "hospital_name": "Central City Hospital", "name": "Dr. Divya Agrawal", "specialization": "Dermatology", "consultation_fee": 700, "availability": "Monday to Friday, 3:00 PM - 6:00 PM"},

    # Harmony Care Hospital (H004)
    {"id": "D007", "hospital_id": "H004", "hospital_name": "Harmony Care Hospital", "name": "Dr. Priya Nair", "specialization": "Gynecology", "consultation_fee": 750, "availability": "Monday to Saturday, 10:00 AM - 1:00 PM"},
    {"id": "D008", "hospital_id": "H004", "hospital_name": "Harmony Care Hospital", "name": "Dr. Rahul Verma", "specialization": "Psychiatry", "consultation_fee": 900, "availability": "Monday to Friday, 5:00 PM - 8:00 PM"},
    {"id": "D107", "hospital_id": "H004", "hospital_name": "Harmony Care Hospital", "name": "Dr. Vivek Saxena", "specialization": "General Medicine", "consultation_fee": 600, "availability": "Monday to Saturday, 9:00 AM - 1:00 PM"},

    # Lifeline Advanced Hospital (H005)
    {"id": "D009", "hospital_id": "H005", "hospital_name": "Lifeline Advanced Hospital", "name": "Dr. Karan Malhotra", "specialization": "Pulmonology", "consultation_fee": 850, "availability": "Monday to Friday, 9:00 AM - 12:00 PM"},
    {"id": "D010", "hospital_id": "H005", "hospital_name": "Lifeline Advanced Hospital", "name": "Dr. Meera Iyer", "specialization": "General Surgery", "consultation_fee": 950, "availability": "Tuesday to Saturday, 11:00 AM - 3:00 PM"},
    {"id": "D108", "hospital_id": "H005", "hospital_name": "Lifeline Advanced Hospital", "name": "Dr. Alok Tripathi", "specialization": "Cardiology", "consultation_fee": 900, "availability": "Monday to Saturday, 2:00 PM - 6:00 PM"},

    # Vijay Nagar Medical Clinic (H_SEED_1)
    {"id": "D109", "hospital_id": "H_SEED_1", "hospital_name": "Vijay Nagar Medical Clinic", "name": "Dr. Rajesh Singhania", "specialization": "Cardiology", "consultation_fee": 800, "availability": "Monday to Saturday, 10:00 AM - 2:00 PM"},
    {"id": "D110", "hospital_id": "H_SEED_1", "hospital_name": "Vijay Nagar Medical Clinic", "name": "Dr. Sunita Saxena", "specialization": "Dermatology", "consultation_fee": 600, "availability": "Monday to Friday, 4:00 PM - 7:00 PM"},
    {"id": "D111", "hospital_id": "H_SEED_1", "hospital_name": "Vijay Nagar Medical Clinic", "name": "Dr. Manish Choudhary", "specialization": "General Medicine", "consultation_fee": 500, "availability": "Monday to Saturday, 9:00 AM - 1:00 PM"},
    {"id": "D112", "hospital_id": "H_SEED_1", "hospital_name": "Vijay Nagar Medical Clinic", "name": "Dr. Kavita Sharma", "specialization": "Gynecology", "consultation_fee": 650, "availability": "Monday to Saturday, 2:00 PM - 5:00 PM"},

    # Old Palasia Medical Clinic (H_SEED_2)
    {"id": "D113", "hospital_id": "H_SEED_2", "hospital_name": "Old Palasia Medical Clinic", "name": "Dr. Rohan Deshmukh", "specialization": "Orthopedics", "consultation_fee": 700, "availability": "Monday to Saturday, 11:00 AM - 3:00 PM"},
    {"id": "D114", "hospital_id": "H_SEED_2", "hospital_name": "Old Palasia Medical Clinic", "name": "Dr. Sneha Kulkarni", "specialization": "Pediatrics", "consultation_fee": 600, "availability": "Monday to Friday, 9:00 AM - 1:00 PM"},
    {"id": "D115", "hospital_id": "H_SEED_2", "hospital_name": "Old Palasia Medical Clinic", "name": "Dr. Deepak Jain", "specialization": "General Medicine", "consultation_fee": 500, "availability": "Monday to Saturday, 4:00 PM - 8:00 PM"},

    # Rajwada Medical Clinic (H_SEED_3)
    {"id": "D116", "hospital_id": "H_SEED_3", "hospital_name": "Rajwada Medical Clinic", "name": "Dr. Ashok Mishra", "specialization": "General Medicine", "consultation_fee": 500, "availability": "Monday to Saturday, 9:00 AM - 1:00 PM"},
    {"id": "D117", "hospital_id": "H_SEED_3", "hospital_name": "Rajwada Medical Clinic", "name": "Dr. Priyanka Joshi", "specialization": "Dermatology", "consultation_fee": 650, "availability": "Tuesday to Saturday, 3:00 PM - 6:00 PM"},
    {"id": "D118", "hospital_id": "H_SEED_3", "hospital_name": "Rajwada Medical Clinic", "name": "Dr. Tarun Sen", "specialization": "Cardiology", "consultation_fee": 850, "availability": "Monday to Saturday, 10:00 AM - 2:00 PM"},

    # Bhawarkuan Medical Clinic (H_SEED_4)
    {"id": "D119", "hospital_id": "H_SEED_4", "hospital_name": "Bhawarkuan Medical Clinic", "name": "Dr. Nitin Agrawal", "specialization": "General Medicine", "consultation_fee": 500, "availability": "Monday to Saturday, 10:00 AM - 2:00 PM"},
    {"id": "D120", "hospital_id": "H_SEED_4", "hospital_name": "Bhawarkuan Medical Clinic", "name": "Dr. Swati Bhatt", "specialization": "Pediatrics", "consultation_fee": 600, "availability": "Monday to Saturday, 4:00 PM - 7:00 PM"},
    {"id": "D121", "hospital_id": "H_SEED_4", "hospital_name": "Bhawarkuan Medical Clinic", "name": "Dr. Gopal Yadav", "specialization": "Orthopedics", "consultation_fee": 700, "availability": "Monday to Friday, 2:00 PM - 6:00 PM"},

    # Sudama Nagar Medical Clinic (H_SEED_5)
    {"id": "D122", "hospital_id": "H_SEED_5", "hospital_name": "Sudama Nagar Medical Clinic", "name": "Dr. Archana Tiwari", "specialization": "Gynecology", "consultation_fee": 650, "availability": "Monday to Saturday, 10:00 AM - 1:00 PM"},
    {"id": "D123", "hospital_id": "H_SEED_5", "hospital_name": "Sudama Nagar Medical Clinic", "name": "Dr. Sanjay Dubey", "specialization": "General Medicine", "consultation_fee": 500, "availability": "Monday to Saturday, 5:00 PM - 8:00 PM"},
    {"id": "D124", "hospital_id": "H_SEED_5", "hospital_name": "Sudama Nagar Medical Clinic", "name": "Dr. Rakesh Bansal", "specialization": "Dermatology", "consultation_fee": 600, "availability": "Tuesday to Saturday, 2:00 PM - 5:00 PM"},
]

def _get_all_doctors_merged():
    remote_docs = SupabaseService.get_records("doctors") or []
    h_map = _get_hospital_map()
    
    seen_ids = set()
    seen_names = set()
    merged = []
    
    # 1. Add remote non-test docs
    for d in remote_docs:
        if _is_test_doctor(d):
            continue
        d_id = str(d.get("id") or "")
        d_name = str(d.get("name") or "").strip().lower()
        if d_name:
            seen_ids.add(d_id)
            seen_names.add(d_name)
            merged.append(d)
            
    # 2. Merge master doctors for complete hospital & specialization coverage
    for m in MASTER_DOCTORS:
        m_id = str(m["id"])
        m_name = str(m["name"]).strip().lower()
        if m_id not in seen_ids and m_name not in seen_names:
            merged.append(m)
            
    return merged

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
    doctors = _get_all_doctors_merged()
    h_map = _get_hospital_map()
    result = []
    for d in doctors:
        spec = d.get("specialization") or ""
        if specialization and specialization.lower() in spec.lower():
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
    
    for d in doctors:
        d_name = d.get("name") or ""
        clean_d = re.sub(r'^(dr\.?|doctor)\s+', '', d_name.strip(), flags=re.I).lower()
        if clean_search in clean_d or clean_d in clean_search:
            doc_id = d.get("id")
            name = d.get("name")
            spec = d.get("specialization") or "General Medicine"
            fee = d.get("consultation_fee") or 500
            sched = d.get("availability") or "Mon-Sat 09:00 AM - 05:00 PM"
            h_name = d.get("hospital_name") or h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
            return (doc_id, name, spec, fee, sched, h_name)
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

def check_slot_available(doctor_name, appointment_date, appointment_time):
    norm_date = normalize_date(appointment_date)
    norm_time = normalize_time(appointment_time)
    if not norm_date or not norm_time:
        return True
        
    doc = get_doctor_by_name(doctor_name)
    doc_id = doc[0] if doc else None
    
    apps = SupabaseService.get_records("appointments")
    active_statuses = ["confirmed", "pending", "checked_in", "in_progress", "booked"]
    
    for a in apps:
        if a.get("status") in active_statuses:
            a_date = str(a.get("date") or a.get("appointment_date"))
            a_time = str(a.get("start_time") or a.get("appointment_time"))
            d_name = a.get("doctor_name") or ""
            
            if norm_date == a_date and norm_time[:5] in a_time:
                if doc_id and a.get("doctor_id") == doc_id:
                    return False
                if doctor_name and doctor_name.lower() in d_name.lower():
                    return False
    return True

def create_appointment(patient_name, phone, address, doctor_name, appointment_date, appointment_time):
    norm_date = normalize_date(appointment_date) or datetime.now().strftime("%Y-%m-%d")
    norm_time = normalize_time(appointment_time) or "09:00:00"
    
    doc = get_doctor_by_name(doctor_name)
    doc_id = doc[0] if doc else "DOC-001"
    doc_real_name = doc[1] if doc else doctor_name
    hospital_name = doc[5] if doc else "HealthPlus Central Hospital"
    
    voice_user_id = "00000000-0000-0000-0000-000000000001"
    # Try using BookingService
    try:
        success, msg, app_data = BookingService.create_appointment(
            user_id=voice_user_id,
            doctor_id=str(doc_id),
            doctor_name=doc_real_name,
            hospital_name=hospital_name,
            date=norm_date,
            start_time=norm_time,
            end_time=norm_time, # approximate duration
            patient_name=patient_name,
            patient_phone=phone or "",
            patient_email="",
            notes=f"Booked via Voice AI Assistant. Address: {address or 'N/A'}"
        )
        if success and app_data and app_data.get("id"):
            return app_data["id"]
        if not success:
            print(f"[DB ERROR] BookingService reported failure: {msg}")
            return None
    except Exception as e:
        print(f"[DB WARN] BookingService call failed, trying direct insert: {e}")
        
    # Direct fallback insert
    app_data = {
        "user_id": voice_user_id,
        "doctor_id": str(doc_id),
        "doctor_name": doc_real_name,
        "hospital_name": hospital_name,
        "date": norm_date,
        "appointment_date": norm_date,
        "start_time": norm_time,
        "appointment_time": norm_time,
        "end_time": norm_time,
        "patient_name": patient_name,
        "patient_phone": phone,
        "phone": phone,
        "address": address,
        "status": "confirmed"
    }
    inserted = SupabaseService.insert_record("appointments", app_data)
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
