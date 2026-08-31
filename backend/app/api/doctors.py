import math
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from fastapi import APIRouter, HTTPException, Query, Depends
import httpx

from app.schemas.doctor_schema import DoctorBase, DoctorSearchRequest
from app.database.supabase_client import SupabaseService, get_supabase_client
from app.services.pinecone_service import PineconeService
from app.auth.auth_handler import get_doctor_user

logger = logging.getLogger("hospital_app.doctors")

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])
alias_router = APIRouter(prefix="/doctors", tags=["Doctors Alias"])

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_CACHE: Dict[Tuple[float, float, int, str], Tuple[float, List[Dict[str, Any]]]] = {}
OVERPASS_CACHE_TTL = 300  # 5 minutes in seconds


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in meters between two points on the Earth."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def fetch_external_osm_doctors(lat: float, lng: float, radius_m: int, specialty: Optional[str] = None) -> List[Dict[str, Any]]:
    spec_key = (specialty or "").strip().lower()
    cache_key = (round(lat, 3), round(lng, 3), radius_m, spec_key)
    now = time.time()

    if cache_key in OVERPASS_CACHE:
        timestamp, cached_data = OVERPASS_CACHE[cache_key]
        if now - timestamp < OVERPASS_CACHE_TTL:
            return cached_data

    overpass_query = f"""
    [out:json][timeout:15];
    (
      node["amenity"~"doctors|clinic|hospital"](around:{radius_m},{lat},{lng});
      way["amenity"~"doctors|clinic|hospital"](around:{radius_m},{lat},{lng});
    );
    out center;
    """

    headers = {"User-Agent": "HealthPulse-Nearby-Search/1.0 (contact@healthpulse.example)"}

    try:
        r = httpx.post(OVERPASS_URL, data={"data": overpass_query}, headers=headers, timeout=10.0)
        if r.status_code != 200:
            logger.warning(f"Overpass API returned status {r.status_code}")
            return []

        data = r.json()
        elements = data.get("elements", [])
        external_doctors = []

        for el in elements:
            tags = el.get("tags", {})
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lng = el.get("lon") or el.get("center", {}).get("lon")

            if el_lat is None or el_lng is None:
                continue

            osm_spec = tags.get("healthcare:speciality") or tags.get("speciality") or tags.get("amenity", "")
            raw_name = tags.get("name") or tags.get("name:en")
            doc_name = raw_name if raw_name else (f"Dr. {osm_spec.title()} Clinic" if osm_spec else "Medical Centre")
            
            # Filter by specialty if requested
            if spec_key:
                combined_text = f"{osm_spec} {doc_name} {tags.get('amenity', '')}".lower()
                if spec_key not in combined_text:
                    continue

            dist = haversine_distance(lat, lng, float(el_lat), float(el_lng))

            # Format phone
            phone = tags.get("phone") or tags.get("contact:phone") or tags.get("phone:mobile")

            # Format address
            addr_parts = [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:suburb"),
                tags.get("addr:city"),
                tags.get("addr:postcode")
            ]
            address_str = ", ".join([p for p in addr_parts if p]) or tags.get("addr:full") or f"Near {doc_name}"

            external_doctors.append({
                "id": f"ext_{el.get('type')}_{el.get('id')}",
                "name": doc_name,
                "degree": (osm_spec or "General Practice").replace("_", " ").title(),
                "specialization": (osm_spec or specialty or "General Medicine").replace("_", " ").title(),
                "experience_years": 5,
                "designation": tags.get("amenity", "clinic").replace("_", " ").title() + " Specialist",
                "languages": ["English", "Hindi"],
                "consultation_fee": 500,
                "availability": "Contact clinic for hours",
                "image_url": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&auto=format&fit=crop&q=80",
                "rating": 4.5,
                "total_reviews": 10,
                "hospital_id": f"hosp_ext_{el.get('id')}",
                "hospital_name": tags.get("operator") or tags.get("name") or "External Healthcare Facility",
                "address": address_str,
                "phone": phone,
                "latitude": float(el_lat),
                "longitude": float(el_lng),
                "distance_meters": round(dist, 1),
                "source": "external",
                "bookable": False
            })

        # Sort external doctors by distance and limit to closest 20
        external_doctors.sort(key=lambda x: x["distance_meters"])
        external_doctors = external_doctors[:20]

        OVERPASS_CACHE[cache_key] = (now, external_doctors)
        return external_doctors

    except Exception as e:
        logger.warning(f"Overpass API query failed: {e}. Returning empty external listings.")
        return []


def is_duplicate_external(ext_doc: Dict[str, Any], reg_docs: List[Dict[str, Any]]) -> bool:
    """Drop external listing if registered doctor is within 80m and shares last word of name."""
    ext_lat = ext_doc.get("latitude")
    ext_lng = ext_doc.get("longitude")
    ext_name = ext_doc.get("name", "").lower()

    if ext_lat is None or ext_lng is None:
        return False

    stopwords = {"dr", "dr.", "clinic", "hospital", "center", "centre", "specialist", "medical", "nursing", "home"}

    def get_clean_words(name_str: str) -> List[str]:
        words = [w.strip(".,;:()") for w in name_str.lower().split() if w.strip(".,;:()")]
        return [w for w in words if w not in stopwords]

    ext_words = get_clean_words(ext_name)
    if not ext_words:
        return False
    ext_last_word = ext_words[-1]

    for reg in reg_docs:
        reg_lat = reg.get("latitude")
        reg_lng = reg.get("longitude")
        reg_name = reg.get("name", "").lower()

        if reg_lat is None or reg_lng is None:
            continue

        dist = haversine_distance(ext_lat, ext_lng, reg_lat, reg_lng)
        if dist <= 80.0:
            reg_words = get_clean_words(reg_name)
            if not reg_words:
                continue
            reg_last_word = reg_words[-1]

            if (ext_last_word in reg_name) or (reg_last_word in ext_name):
                return True

    return False


@router.get("/specialties", response_model=List[str])
@alias_router.get("/specialties", response_model=List[str])
def get_doctor_specialties():
    """Return distinct list of specialties from registered doctors table."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("doctors").select("specialization").execute()
            if res.data:
                specs = sorted(list({
                    r["specialization"].strip() 
                    for r in res.data 
                    if r.get("specialization") and r["specialization"].strip()
                }))
                if specs:
                    return specs
        except Exception as e:
            logger.error(f"Error fetching specialties from Supabase: {e}")

    # Fallback to local store
    all_docs = SupabaseService.get_records("doctors")
    specs = sorted(list({
        d["specialization"].strip()
        for d in all_docs
        if d.get("specialization") and d["specialization"].strip()
    }))
    return specs or ["Cardiology", "Dermatology", "General Medicine", "Neurology", "Orthopedics", "Pediatrics"]


@router.get("/nearby")
@alias_router.get("/nearby")
def get_nearby_doctors(
    lat: float = Query(..., description="Latitude coordinate"),
    lng: float = Query(..., description="Longitude coordinate"),
    radius_m: int = Query(10000, description="Search radius in meters (max 20000)"),
    specialty: Optional[str] = Query(None, description="Optional specialty filter")
):
    """
    Search registered doctors via PostGIS RPC and external doctors via OpenStreetMap Overpass API,
    merged and sorted by distance.
    """
    # Enforce radius_m maximum cap of 20000m (20km)
    clamped_radius = min(max(100, radius_m), 20000)

    client = get_supabase_client()
    registered_docs = []

    # 1. Query Registered Doctors via PostGIS RPC Exclusively
    if client:
        try:
            rpc_res = client.rpc("get_nearby_doctors", {
                "p_lat": lat,
                "p_lng": lng,
                "p_radius_meters": float(clamped_radius),
                "p_specialty": specialty or ""
            }).execute()

            if rpc_res.data is not None:
                for row in rpc_res.data:
                    doc = dict(row)
                    doc["source"] = "registered"
                    doc["bookable"] = True
                    doc["distance_meters"] = round(float(doc.get("distance_meters", 0)), 1)
                    registered_docs.append(doc)
        except Exception as e:
            logger.error(f"PostGIS RPC get_nearby_doctors failed: {e}")
            raise HTTPException(status_code=500, detail=f"Database PostGIS RPC query failed: {e}")

    # 2. Query External Doctors via Overpass API
    external_docs = fetch_external_osm_doctors(lat, lng, clamped_radius, specialty)

    # 3. De-duplicate external doctors against registered doctors
    filtered_external = [
        ext for ext in external_docs
        if not is_duplicate_external(ext, registered_docs)
    ]

    # 4. Merge and sort by distance
    merged = registered_docs + filtered_external
    merged.sort(key=lambda x: x.get("distance_meters", 999999))

    return {
        "lat": lat,
        "lng": lng,
        "radius_m": clamped_radius,
        "specialty": specialty,
        "total": len(merged),
        "results": merged
    }


@router.get("/me")
def get_my_doctor_profile(doctor_info: dict = Depends(get_doctor_user)):
    return doctor_info


@router.get("/me/appointments")
def get_my_doctor_appointments(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    return appointments


@router.get("/me/schedule")
def get_my_doctor_schedule(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    schedules = SupabaseService.get_records("schedules", {"doctor_id": doc_id})
    return schedules


@router.get("/me/patients")
def get_my_doctor_patients(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    seen_users = {}
    for app in appointments:
        uid = app.get("user_id")
        if uid and uid not in seen_users:
            patient_code = None
            p_id = None
            try:
                pts = SupabaseService.get_records("patients", {"profile_id": uid})
                if pts:
                    patient_code = pts[0].get("patient_code")
                    p_id = pts[0].get("id")
            except Exception:
                pass

            seen_users[uid] = {
                "patient_id": p_id or uid,
                "user_id": uid,
                "patient_code": patient_code or f"PT-REF{str(uid)[:6]}",
                "patient_name": app.get("patient_name"),
                "patient_email": app.get("patient_email"),
                "patient_phone": app.get("patient_phone"),
                "last_appointment_date": app.get("date"),
                "total_appointments": len([a for a in appointments if a.get("user_id") == uid])
            }
    return list(seen_users.values())


@router.get("/patients/{patient_id}/profile")
@router.get("/me/patients/{patient_id}")
def get_doctor_patient_profile(patient_id: str, doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    
    patient_rec = SupabaseService.get_record_by_id("patients", patient_id)
    profile_id = None
    real_patient_id = patient_id

    if patient_rec:
        profile_id = patient_rec.get("profile_id")
        real_patient_id = patient_rec.get("id")
    else:
        pts = SupabaseService.get_records("patients", {"profile_id": patient_id})
        if pts:
            patient_rec = pts[0]
            profile_id = patient_id
            real_patient_id = patient_rec["id"]
        else:
            profile_id = patient_id

    profile_rec = SupabaseService.get_record_by_id("profiles", profile_id) if profile_id else None

    all_doc_appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    patient_appointments = [
        a for a in all_doc_appointments 
        if (profile_id and a.get("user_id") == profile_id) or (a.get("user_id") == patient_id)
    ]

    p_name = profile_rec.get("name") if profile_rec else None
    p_email = profile_rec.get("email") if profile_rec else None
    p_phone = profile_rec.get("phone") if profile_rec else None

    if patient_appointments:
        if not p_name:
            p_name = patient_appointments[0].get("patient_name")
        if not p_email:
            p_email = patient_appointments[0].get("patient_email")
        if not p_phone:
            p_phone = patient_appointments[0].get("patient_phone")

    return {
        "patient_id": real_patient_id,
        "profile_id": profile_id or real_patient_id,
        "patient_code": patient_rec.get("patient_code") if patient_rec else f"PT-REF{str(real_patient_id)[:6]}",
        "name": p_name or "Patient",
        "email": p_email or "No email provided",
        "phone": p_phone or "No phone provided",
        "gender": patient_rec.get("gender") if patient_rec else None,
        "blood_group": patient_rec.get("blood_group") if patient_rec else None,
        "date_of_birth": patient_rec.get("date_of_birth") if patient_rec else None,
        "address": patient_rec.get("address") if patient_rec else None,
        "emergency_contact": patient_rec.get("emergency_contact") if patient_rec else None,
        "consultation_count": len(patient_appointments),
        "appointments": patient_appointments
    }


@router.get("/me/stats")
def get_my_doctor_stats(doctor_info: dict = Depends(get_doctor_user)):
    doc_id = doctor_info["doctor"]["id"]
    appointments = SupabaseService.get_records("appointments", {"doctor_id": doc_id})
    today_str = str(date.today())
    
    today_apps = [a for a in appointments if str(a.get("date")) == today_str]
    upcoming_apps = [a for a in appointments if a.get("status") in ["confirmed", "pending"]]
    completed_apps = [a for a in appointments if a.get("status") == "completed"]
    cancelled_apps = [a for a in appointments if a.get("status") == "cancelled"]
    unique_patients = len({a.get("user_id") for a in appointments if a.get("user_id")})

    return {
        "doctor": doctor_info["doctor"],
        "total_appointments": len(appointments),
        "today_appointments_count": len(today_apps),
        "upcoming_appointments_count": len(upcoming_apps),
        "completed_appointments_count": len(completed_apps),
        "cancelled_appointments_count": len(cancelled_apps),
        "total_patients_count": unique_patients
    }


@router.get("", response_model=List[DoctorBase])
@alias_router.get("", response_model=List[DoctorBase])
def get_all_doctors(
    specialization: Optional[str] = Query(None),
    hospital_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    min_fee: Optional[float] = Query(None),
    max_fee: Optional[float] = Query(None),
    availability: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    doctors = SupabaseService.get_records("doctors")
    hospitals = {h["id"]: h for h in SupabaseService.get_records("hospitals")}
    departments = {d["id"]: d for d in SupabaseService.get_records("departments")}

    for d in doctors:
        dept_id = d.get("department_id")
        if dept_id and dept_id in departments:
            d["department_name"] = departments[dept_id].get("name")
        if d.get("languages") is None:
            d["languages"] = ["English", "Hindi"]
        if d.get("rating") is None:
            d["rating"] = 5.0
        if d.get("consultation_fee") is None:
            d["consultation_fee"] = 0.0
        if d.get("experience_years") is None:
            d["experience_years"] = 0
        if d.get("total_reviews") is None:
            d["total_reviews"] = 0

    if specialization:
        doctors = [d for d in doctors if d.get("specialization", "").lower() == specialization.lower()]
    if hospital_id:
        doctors = [d for d in doctors if d.get("hospital_id") == hospital_id]
    if department_id:
        doctors = [d for d in doctors if d.get("department_id") == department_id]
    if city:
        doctors = [
            d for d in doctors 
            if hospitals.get(d.get("hospital_id"), {}).get("city", "").lower() == city.lower()
        ]
    if min_rating is not None:
        doctors = [d for d in doctors if float(d.get("rating", 5.0)) >= min_rating]
    if min_fee is not None:
        doctors = [d for d in doctors if float(d.get("consultation_fee", 0)) >= min_fee]
    if max_fee is not None:
        doctors = [d for d in doctors if float(d.get("consultation_fee", 0)) <= max_fee]
    if availability:
        doctors = [d for d in doctors if availability.lower() in d.get("availability", "").lower()]
    if search:
        s_lower = search.lower()
        doctors = [
            d for d in doctors 
            if s_lower in d.get("name", "").lower() 
            or s_lower in d.get("specialization", "").lower()
            or s_lower in d.get("designation", "").lower()
            or s_lower in d.get("department_name", "").lower()
        ]
    return doctors


@router.get("/{doctor_id}", response_model=DoctorBase)
@alias_router.get("/{doctor_id}", response_model=DoctorBase)
def get_doctor_by_id(doctor_id: str):
    doctor = SupabaseService.get_record_by_id("doctors", doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if doctor.get("department_id"):
        dept = SupabaseService.get_record_by_id("departments", doctor["department_id"])
        if dept:
            doctor["department_name"] = dept.get("name")
    return doctor


@router.post("/search")
@alias_router.post("/search")
def search_doctors_vector(req: DoctorSearchRequest):
    if req.query:
        vector_results = PineconeService.search_doctors(query=req.query, top_k=req.limit or 10)
    else:
        vector_results = []

    if vector_results:
        filtered = vector_results
        if req.department_id:
            filtered = [r for r in filtered if r.get("department_id") == req.department_id]
        if req.specialization:
            filtered = [r for r in filtered if req.specialization.lower() in r.get("specialization", "").lower()]
        if req.hospital_id:
            filtered = [r for r in filtered if r.get("hospital_id") == req.hospital_id]
        if req.city:
            filtered = [r for r in filtered if req.city.lower() in r.get("city", "").lower()]
        if req.min_rating is not None:
            filtered = [r for r in filtered if float(r.get("rating", 5.0)) >= req.min_rating]
        if req.min_fee is not None:
            filtered = [r for r in filtered if float(r.get("consultation_fee", 0)) >= req.min_fee]
        if req.max_fee is not None:
            filtered = [r for r in filtered if float(r.get("consultation_fee", 0)) <= req.max_fee]
        return {"query": req.query, "results": filtered}

    db_docs = get_all_doctors(
        specialization=req.specialization,
        hospital_id=req.hospital_id,
        department_id=req.department_id,
        city=req.city,
        min_rating=req.min_rating,
        min_fee=req.min_fee,
        max_fee=req.max_fee,
        availability=req.availability,
        search=req.query
    )
    return {"query": req.query, "results": db_docs}
