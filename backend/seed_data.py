import json
import uuid
from pathlib import Path
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import hash_password
from app.config import settings

def seed(force: bool = False):
    allow_seed = settings.ALLOW_DEMO_SEED or force
    if not allow_seed:
        print("ALLOW_DEMO_SEED is False. Skipping demo data seeding.")
        return

    print("Seeding Database from data.json...")

    root_dir = Path(__file__).resolve().parent.parent
    data_file = root_dir / "data.json"
    
    if not data_file.exists():
        print(f"data.json not found at {data_file}")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        hospitals_data = json.load(f)

    # Doctor image URLs mapping for UI
    doctor_images = {
        "D001": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=500&auto=format&fit=crop&q=80",
        "D002": "https://images.unsplash.com/photo-1594824813566-788b5608d084?w=500&auto=format&fit=crop&q=80",
        "D003": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=500&auto=format&fit=crop&q=80",
        "D004": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&auto=format&fit=crop&q=80",
        "D005": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=500&auto=format&fit=crop&q=80",
        "D006": "https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=500&auto=format&fit=crop&q=80",
        "D007": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=500&auto=format&fit=crop&q=80",
        "D008": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80",
        "D009": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&auto=format&fit=crop&q=80",
        "D010": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500&auto=format&fit=crop&q=80",
    }

    # 1. Seed Admin User Idempotently
    admin_profile = SupabaseService.get_record_by_id("profiles", settings.ADMIN_USER_ID)
    if not admin_profile:
        admin_by_email = SupabaseService.get_records("profiles", {"email": "admin@hospital.com"})
        if not admin_by_email:
            SupabaseService.insert_record("profiles", {
                "id": settings.ADMIN_USER_ID,
                "name": "System Administrator",
                "email": "admin@hospital.com",
                "password_hash": hash_password("admin123"),
                "role": "admin"
            })
            print("Admin user seeded: admin@hospital.com")

    # 2. Seed Hospitals & Doctors Idempotently
    for h in hospitals_data:
        hospital_id = h["hospital_id"]
        addr = h.get("address", {})
        
        existing_hospital = SupabaseService.get_record_by_id("hospitals", hospital_id)
        if not existing_hospital:
            hospital_rec = {
                "id": hospital_id,
                "hospital_name": h["hospital_name"],
                "street": addr.get("street", ""),
                "area": addr.get("area", ""),
                "city": addr.get("city", "Indore"),
                "state": addr.get("state", "Madhya Pradesh"),
                "pincode": addr.get("pincode", ""),
                "country": addr.get("country", "India"),
                "phone": h.get("phone", ""),
                "email": h.get("email", ""),
                "departments": h.get("departments", [])
            }
            SupabaseService.insert_record("hospitals", hospital_rec)

        dept_map = {}
        for dept_name in h.get("departments", []):
            existing_depts = SupabaseService.get_records("departments", {"hospital_id": hospital_id, "name": dept_name})
            if not existing_depts:
                dept_id = str(uuid.uuid4())
                dept_rec = {
                    "id": dept_id,
                    "hospital_id": hospital_id,
                    "name": dept_name,
                    "description": f"{dept_name} Department at {h['hospital_name']}",
                    "status": "active"
                }
                SupabaseService.insert_record("departments", dept_rec)
                dept_map[dept_name.lower()] = dept_id
            else:
                dept_map[dept_name.lower()] = existing_depts[0]["id"]

        for d in h.get("doctors", []):
            doc_id = d["doctor_id"]
            img = doctor_images.get(doc_id, "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80")
            
            # Match doctor department_id based on specialization
            spec = d.get("specialization", "").lower()
            dept_id = None
            for d_name, d_id in dept_map.items():
                if d_name in spec or spec in d_name:
                    dept_id = d_id
                    break
            if not dept_id and dept_map:
                dept_id = list(dept_map.values())[0]

            # Formulate doctor email: e.g. Dr. Arjun Mehta -> arjun@hospital.com
            doc_first_name = d["name"].replace("Dr. ", "").split()[0].lower()
            doc_email = f"{doc_first_name}@hospital.com"

            # Create or fetch doctor profile idempotently
            doc_profiles = SupabaseService.get_records("profiles", {"email": doc_email})
            if not doc_profiles:
                profile_id = str(uuid.uuid4())
                profile_rec = {
                    "id": profile_id,
                    "name": d["name"],
                    "email": doc_email,
                    "password_hash": hash_password("doctor123"),
                    "role": "doctor"
                }
                SupabaseService.insert_record("profiles", profile_rec)
            else:
                profile_id = doc_profiles[0]["id"]

            existing_doc = SupabaseService.get_record_by_id("doctors", doc_id)
            if not existing_doc:
                doc_rec = {
                    "id": doc_id,
                    "profile_id": profile_id,
                    "hospital_id": hospital_id,
                    "department_id": dept_id,
                    "name": d["name"],
                    "degree": d.get("degree", ""),
                    "specialization": d.get("specialization", "General"),
                    "experience_years": d.get("experience_years", 5),
                    "designation": d.get("designation", "Specialist"),
                    "languages": d.get("languages", ["English", "Hindi"]),
                    "consultation_fee": d.get("consultation_fee", 500),
                    "availability": d.get("availability", "Monday to Saturday, 10:00 AM - 2:00 PM"),
                    "image_url": img,
                    "rating": 5.0,
                    "total_reviews": 0
                }
                SupabaseService.insert_record("doctors", doc_rec)
            else:
                existing_doc["profile_id"] = profile_id
                existing_doc["department_id"] = dept_id
                SupabaseService.update_record("doctors", doc_id, {"profile_id": profile_id, "department_id": dept_id})

            # Seed hospital_members record for doctor idempotently
            existing_memberships = SupabaseService.get_records("hospital_members", {
                "hospital_id": hospital_id,
                "user_id": profile_id
            })
            if not existing_memberships:
                SupabaseService.insert_record("hospital_members", {
                    "id": str(uuid.uuid4()),
                    "hospital_id": hospital_id,
                    "user_id": profile_id,
                    "role": "doctor"
                })

            # Seed default schedule slots for doctor idempotently
            existing_schedules = SupabaseService.get_records("schedules", {"doctor_id": doc_id})
            if not existing_schedules:
                SupabaseService.insert_record("schedules", {
                    "id": str(uuid.uuid4()),
                    "doctor_id": doc_id,
                    "day_of_week": "ALL",
                    "start_time": "10:00 AM",
                    "end_time": "02:00 PM",
                    "slot_duration_minutes": 30,
                    "is_active": True
                })

    print("Seeding complete!")

if __name__ == "__main__":
    seed(force=True)
