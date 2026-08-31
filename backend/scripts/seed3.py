"""
Seed Script for Doctor Geolocation Testing (seed3.py)
------------------------------------------------------
Generates test doctors with valid latitude and longitude coordinates clustered
around real Indore neighborhoods for end-to-end testing of nearby doctor search.

Usage:
  python backend/scripts/seed3.py [--count 30] [--clean]
"""

import sys
import random
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure backend path is accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from supabase import create_client, Client
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed3_doctor_geolocation")

INDORE_NEIGHBORHOODS = [
    {"name": "Vijay Nagar", "lat": 22.7533, "lng": 75.8937},
    {"name": "Old Palasia", "lat": 22.7247, "lng": 75.8872},
    {"name": "Rajwada", "lat": 22.7196, "lng": 75.8577},
    {"name": "Bhawarkuan", "lat": 22.6926, "lng": 75.8676},
    {"name": "Sudama Nagar", "lat": 22.6953, "lng": 75.8340},
]

SPECIALTIES = [
    "Cardiology",
    "Dermatology",
    "Pediatrics",
    "Neurology",
    "Orthopedics",
    "General Medicine",
    "Dentistry",
    "Gynecology"
]

FIRST_NAMES = ["Rajesh", "Sunita", "Amit", "Pooja", "Sanjay", "Kavita", "Vikas", "Anjali", "Ramesh", "Deepa", "Manish", "Priya", "Alok", "Neha", "Suresh"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Joshi", "Patel", "Mehta", "Rao", "Nair", "Malhotra", "Singh", "Chouhan", "Trivedi", "Agrawal", "Deshmukh"]

DEGREES = {
    "Cardiology": "MBBS, MD, DM (Cardiology)",
    "Dermatology": "MBBS, MD (Dermatology)",
    "Pediatrics": "MBBS, MD (Pediatrics)",
    "Neurology": "MBBS, MD, DM (Neurology)",
    "Orthopedics": "MBBS, MS (Orthopedics)",
    "General Medicine": "MBBS, MD (Medicine)",
    "Dentistry": "BDS, MDS",
    "Gynecology": "MBBS, MS (Obstetrics & Gynecology)"
}

SEED_PREFIX = "[TEST]"

def get_supabase_client() -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured.")
    return create_client(url, key)

def clean_seed_data(client: Client):
    """Deletes previously seeded test doctors starting with [TEST]."""
    logger.info("Cleaning up previously seeded [TEST] doctor records...")
    
    # Query all test doctors
    res = client.table("doctors").select("id, profile_id, hospital_id").like("name", f"{SEED_PREFIX}%").execute()
    test_docs = res.data or []
    
    if not test_docs:
        logger.info("No existing [TEST] doctor records found to clean.")
        return

    doc_ids = [d["id"] for d in test_docs]
    profile_ids = [d["profile_id"] for d in test_docs if d.get("profile_id")]
    hospital_ids = list({d["hospital_id"] for d in test_docs if d.get("hospital_id") and str(d.get("hospital_id")).startswith("H_SEED_")})

    # Delete doctor records
    for doc_id in doc_ids:
        client.table("doctors").delete().eq("id", doc_id).execute()
    logger.info(f"Deleted {len(doc_ids)} test doctor records.")

    # Delete associated test profiles
    for prof_id in profile_ids:
        try:
            client.table("profiles").delete().eq("id", prof_id).execute()
        except Exception:
            pass

    # Delete associated test hospitals
    for h_id in hospital_ids:
        try:
            client.table("hospitals").delete().eq("id", h_id).execute()
        except Exception:
            pass

    logger.info("Clean process completed.")


def seed_doctors(count: int = 30):
    client = get_supabase_client()

    logger.info(f"Seeding {count} doctor records with realistic Indore coordinates...")

    # Ensure 5 seed hospitals exist for reference
    seed_hospitals = []
    for i, nh in enumerate(INDORE_NEIGHBORHOODS, start=1):
        h_id = f"H_SEED_{i}"
        h_name = f"{nh['name']} Medical Clinic"
        existing = client.table("hospitals").select("id").eq("id", h_id).execute()
        if not existing.data:
            h_rec = {
                "id": h_id,
                "hospital_name": h_name,
                "street": f"Main Road, {nh['name']}",
                "area": nh["name"],
                "city": "Indore",
                "state": "Madhya Pradesh",
                "pincode": "452001",
                "country": "India",
                "phone": f"+91-731-49000{i:02d}",
                "email": f"info@{nh['name'].lower().replace(' ', '')}-clinic.example",
                "departments": SPECIALTIES
            }
            client.table("hospitals").insert(h_rec).execute()
        seed_hospitals.append(h_id)

    specialty_counts: Dict[str, int] = {s: 0 for s in SPECIALTIES}
    lats: List[float] = []
    lngs: List[float] = []

    for i in range(1, count + 1):
        doc_id = f"D_SEED_{i:03d}"
        neighborhood = random.choice(INDORE_NEIGHBORHOODS)
        specialty = random.choice(SPECIALTIES)
        specialty_counts[specialty] += 1

        # Small random jitter (~0.5 - 2 km spread) around neighborhood center
        lat_jitter = random.uniform(-0.015, 0.015)
        lng_jitter = random.uniform(-0.015, 0.015)
        doc_lat = round(neighborhood["lat"] + lat_jitter, 6)
        doc_lng = round(neighborhood["lng"] + lng_jitter, 6)

        lats.append(doc_lat)
        lngs.append(doc_lng)

        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{SEED_PREFIX} Dr. {first} {last}"
        fee = random.choice([400, 500, 600, 750, 900, 1000, 1200])
        exp = random.randint(3, 22)
        degree = DEGREES.get(specialty, "MBBS, MD")

        doc_rec = {
            "id": doc_id,
            "hospital_id": random.choice(seed_hospitals),
            "name": full_name,
            "degree": degree,
            "specialization": specialty,
            "experience_years": exp,
            "designation": f"Senior {specialty} Specialist",
            "languages": ["English", "Hindi"],
            "consultation_fee": fee,
            "availability": "Monday to Saturday, 10:00 AM - 4:00 PM",
            "image_url": f"https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
            "rating": round(random.uniform(4.2, 5.0), 1),
            "total_reviews": random.randint(15, 140),
            "latitude": doc_lat,
            "longitude": doc_lng
        }

        try:
            client.table("doctors").insert(doc_rec).execute()
        except Exception as e:
            # If primary key conflict, try updating
            try:
                client.table("doctors").update(doc_rec).eq("id", doc_id).execute()
            except Exception as ex:
                logger.error(f"Failed to insert doctor {doc_id}: {ex}")

    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)

    print("\n" + "=" * 60)
    print("DOCTOR GEOLOCATION SEEDING REPORT")
    print("=" * 60)
    print(f"Total doctors seeded              : {count}")
    print("\nSpecialty Breakdown:")
    for spec, c in specialty_counts.items():
        print(f"  - {spec:<20}: {c}")
    print("\nGeographic Bounding Box (Indore Cluster):")
    print(f"  - Latitude Range  : [{min_lat:.6f}, {max_lat:.6f}]")
    print(f"  - Longitude Range : [{min_lng:.6f}, {max_lng:.6f}]")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Seed test doctors with valid lat/lng coordinates in Indore.")
    parser.add_argument("--count", type=int, default=30, help="Number of test doctors to generate (default: 30)")
    parser.add_argument("--clean", action="store_true", help="Delete existing [TEST] doctor records before seeding")

    args = parser.parse_args()
    client = get_supabase_client()

    if args.clean:
        clean_seed_data(client)

    seed_doctors(args.count)

if __name__ == "__main__":
    main()
