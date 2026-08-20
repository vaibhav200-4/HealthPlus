import json
import uuid
from pathlib import Path
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import hash_password
from app.config import settings

def seed():
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
        "D001": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
        "D002": "https://images.unsplash.com/photo-1594824813566-788b5608d084?w=400&auto=format&fit=crop&q=80",
        "D003": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&auto=format&fit=crop&q=80",
        "D004": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&auto=format&fit=crop&q=80",
    }

    # 1. Seed Admin User
    admin_profile = SupabaseService.get_record_by_id("profiles", settings.ADMIN_USER_ID)
    if not admin_profile:
        SupabaseService.insert_record("profiles", {
            "id": settings.ADMIN_USER_ID,
            "name": "System Administrator",
            "email": "admin@hospital.com",
            "password_hash": hash_password("admin123"),
            "role": "admin"
        })
        print("Admin user seeded: admin@hospital.com / admin123")

    # 2. Seed Hospitals & Doctors
    for h in hospitals_data:
        hospital_id = h["hospital_id"]
        addr = h.get("address", {})
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

        for d in h.get("doctors", []):
            doc_id = d["doctor_id"]
            img = doctor_images.get(doc_id, "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80")
            doc_rec = {
                "id": doc_id,
                "hospital_id": hospital_id,
                "name": d["name"],
                "degree": d.get("degree", ""),
                "specialization": d.get("specialization", "General"),
                "experience_years": d.get("experience_years", 5),
                "designation": d.get("designation", "Specialist"),
                "languages": d.get("languages", ["English", "Hindi"]),
                "consultation_fee": d.get("consultation_fee", 500),
                "availability": d.get("availability", "Monday to Saturday, 10:00 AM - 2:00 PM"),
                "image_url": img
            }
            SupabaseService.insert_record("doctors", doc_rec)

            # Seed default schedule slots for each doctor
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
    seed()
