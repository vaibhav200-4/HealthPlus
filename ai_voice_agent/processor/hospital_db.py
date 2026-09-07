import os
import sys
import re
from datetime import datetime, timedelta

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

def _get_hospital_map():
    hospitals = SupabaseService.get_records("hospitals")
    return {h.get("id"): h.get("hospital_name") for h in hospitals if h.get("id")}

def get_all_context_string():
    try:
        hospitals = SupabaseService.get_records("hospitals")
        doctors = SupabaseService.get_records("doctors")
        
        context = "AVAILABLE HOSPITALS:\n"
        for h in hospitals:
            h_name = h.get("hospital_name") or h.get("name", "Hospital")
            city = h.get("city") or h.get("area") or "Indore"
            context += f"- {h_name} (Location: {city})\n"
        
        context += "\nAVAILABLE DOCTORS:\n"
        h_map = _get_hospital_map()
        for d in doctors:
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
        name = h.get("hospital_name") or h.get("name")
        address = ", ".join(filter(None, [h.get("street"), h.get("area"), h.get("city")])) or "Indore"
        if name:
            result.append((name, address))
    return result

def get_doctors():
    doctors = SupabaseService.get_records("doctors")
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
    doctors = SupabaseService.get_records("doctors")
    h_map = _get_hospital_map()
    result = []
    for d in doctors:
        spec = d.get("specialization") or ""
        if specialization and specialization.lower() in spec.lower():
            h_name = h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
            if hospital_name and hospital_name.lower() not in h_name.lower():
                continue
            name = d.get("name")
            fee = d.get("consultation_fee") or 500
            sched = d.get("availability") or "Mon-Sat 09:00 AM - 05:00 PM"
            result.append((name, fee, sched, h_name))
    return result

def get_all_specializations():
    doctors = SupabaseService.get_records("doctors")
    specs = set()
    for d in doctors:
        s = d.get("specialization")
        if s:
            specs.add(s)
    return list(specs)

def get_doctor_by_name(doctor_name):
    if not doctor_name:
        return None
    doctors = SupabaseService.get_records("doctors")
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
            h_name = h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
            return (doc_id, name, spec, fee, sched, h_name)
    return None

def get_doctors_by_hospital(hospital_name):
    if not hospital_name:
        return get_doctors()
    doctors = SupabaseService.get_records("doctors")
    h_map = _get_hospital_map()
    result = []
    for d in doctors:
        h_name = h_map.get(d.get("hospital_id"), "HealthPlus Hospital")
        if hospital_name.lower() in h_name.lower():
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
    
    # Try using BookingService
    try:
        success, msg, app_data = BookingService.create_appointment(
            user_id="voice-agent-user",
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
        if success and app_data.get("id"):
            return app_data["id"]
    except Exception as e:
        print(f"[DB WARN] BookingService call failed, falling back to direct insert: {e}")
        
    # Direct fallback insert
    app_data = {
        "user_id": "voice-agent-user",
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
    return inserted.get("id")

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


