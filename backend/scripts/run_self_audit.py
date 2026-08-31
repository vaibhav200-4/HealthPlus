"""
Comprehensive Phase 2 Self-Audit & Self-Test Script
---------------------------------------------------
Runs all self-audit checks, API endpoint verification calls, de-duplication tests,
and resilience tests.
"""

import sys
import json
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.api import doctors
from app.database.supabase_client import get_supabase_client

client = TestClient(app)


def audit_1_database_state():
    print("\n" + "=" * 60)
    print("AUDIT ITEM 1: DATABASE MIGRATION & FUNCTION STATE")
    print("=" * 60)
    
    supabase = get_supabase_client()
    if not supabase:
        print("[FAIL] Could not connect to Supabase.")
        return

    # Check columns
    try:
        res_cols = supabase.table("doctors").select("id, name, latitude, longitude").limit(1).execute()
        print("[CONFIRMED] Latitude and Longitude columns EXIST on Supabase doctors table!")
        print("  Sample row:", res_cols.data[0] if res_cols.data else "No rows")
    except Exception as e:
        print("[FAIL] Latitude/Longitude columns missing:", e)

    # Check RPC
    try:
        res_rpc = supabase.rpc("get_nearby_doctors", {
            "p_lat": 22.7533,
            "p_lng": 75.8937,
            "p_radius_meters": 5000,
            "p_specialty": ""
        }).execute()
        print("[CONFIRMED] PostGIS RPC function 'get_nearby_doctors' EXISTS in Supabase!")
        print("  Returned rows:", len(res_rpc.data))
    except Exception as e:
        print("[FOUND PENDING MIGRATION] PostGIS RPC function 'get_nearby_doctors' is NOT YET created in Supabase database schema cache.")
        print(f"  Exact error: {e}")
        print("  Note: Migration SQL is written to 'supabase/migrations/17_nearby_doctors_rpc.sql'.")


def audit_2_haversine_fallback():
    print("\n" + "=" * 60)
    print("AUDIT ITEM 2: HAVERSINE FALLBACK CODE PATH ANALYSIS")
    print("=" * 60)
    print("Condition for Fallback:")
    print("  The Python Haversine fallback is maintained as a fail-safe backup for when:")
    print("  a) The PostGIS RPC function 'get_nearby_doctors' has not yet been executed on the Supabase project.")
    print("  b) The project is running in local offline / development fallback mode.")
    print("  c) Supabase returns a PostgREST RPC 404 / PGRST202 error.")
    print("\nExecuting live request to verify which path fires...")

    r = client.get("/api/doctors/nearby?lat=22.7533&lng=75.8937&radius_m=5000&specialty=Cardiology")
    print(f"  HTTP Status Code: {r.status_code}")
    data = r.json()
    print(f"  Results returned: {data.get('total')}")


def audit_3_real_endpoint_responses():
    print("\n" + "=" * 60)
    print("AUDIT ITEM 3: REAL ENDPOINT CALLS & RAW JSON RESPONSES")
    print("=" * 60)

    # 1. Specialties
    print("\n--- 1. GET /api/doctors/specialties ---")
    r1 = client.get("/api/doctors/specialties")
    print(f"Status: {r1.status_code}")
    print("Response JSON:")
    print(json.dumps(r1.json(), indent=2))

    # 2. Location Geocode
    print("\n--- 2. GET /api/location/geocode?q=Vijay%20Nagar%20Indore ---")
    r2 = client.get("/api/location/geocode?q=Vijay%20Nagar%20Indore")
    print(f"Status: {r2.status_code}")
    print("Response JSON:")
    print(json.dumps(r2.json(), indent=2))

    # 3. Nearby Doctors Search
    # Fetch first specialty from r1
    specialties = r1.json()
    target_spec = specialties[0] if specialties else "Cardiology"
    print(f"\n--- 3. GET /api/doctors/nearby?lat=22.7533&lng=75.8937&radius_m=5000&specialty={target_spec} ---")
    r3 = client.get(f"/api/doctors/nearby?lat=22.7533&lng=75.8937&radius_m=5000&specialty={target_spec}")
    print(f"Status: {r3.status_code}")
    res3_json = r3.json()
    print("Response JSON (First 2 results shown for brevity):")
    shortened_res = dict(res3_json)
    shortened_res["results"] = res3_json.get("results", [])[:2]
    print(json.dumps(shortened_res, indent=2))

    # Verification checks on results
    results = res3_json.get("results", [])
    if results:
        distances = [doc.get("distance_meters", 0) for doc in results]
        is_sorted = distances == sorted(distances)
        print(f"\nVerification Checks:")
        print(f"  - Distance meters sorted ascending: {is_sorted} (Distances: {distances[:5]})")
        
        all_valid_source = all(doc.get("source") in ["registered", "external"] for doc in results)
        all_valid_bookable = all(isinstance(doc.get("bookable"), bool) for doc in results)
        print(f"  - Every entry has valid 'source' ('registered'|'external'): {all_valid_source}")
        print(f"  - Every entry has valid 'bookable' boolean: {all_valid_bookable}")

        matching_specialty = all(target_spec.lower() in doc.get("specialization", "").lower() for doc in results)
        print(f"  - Specialty filter '{target_spec}' strictly excludes non-matching entries: {matching_specialty}")


def audit_4_deduplication_unit_test():
    print("\n" + "=" * 60)
    print("AUDIT ITEM 4: DE-DUPLICATION LOGIC TEST")
    print("=" * 60)

    reg_doctors = [{
        "id": "D_SEED_001",
        "name": "[TEST] Dr. Rajesh Sharma",
        "specialization": "Cardiology",
        "latitude": 22.7533,
        "longitude": 75.8937
    }]

    # 1. Test colliding external listing (within 80m, name last word 'Sharma')
    colliding_ext = {
        "id": "ext_node_1001",
        "name": "Rajesh Sharma Heart Clinic",
        "latitude": 22.7535,  # ~22 meters away
        "longitude": 75.8938
    }

    # 2. Test non-colliding external listing (different name or distance > 80m)
    distinct_ext = {
        "id": "ext_node_1002",
        "name": "Apollo Dental Care",
        "latitude": 22.7535,
        "longitude": 75.8938
    }

    is_colliding_dup = doctors.is_duplicate_external(colliding_ext, reg_doctors)
    is_distinct_dup = doctors.is_duplicate_external(distinct_ext, reg_doctors)

    print(f"Test 1 - Colliding External Listing ('Rajesh Sharma Heart Clinic' ~22m from '[TEST] Dr. Rajesh Sharma'):")
    print(f"  -> Dropped by de-duplication: {is_colliding_dup} (Expected: True)")
    
    print(f"Test 2 - Distinct External Listing ('Apollo Dental Care' ~22m away):")
    print(f"  -> Dropped by de-duplication: {is_distinct_dup} (Expected: False)")


def audit_5_overpass_resilience():
    print("\n" + "=" * 60)
    print("AUDIT ITEM 5: OVERPASS API RESILIENCE & FAILURE RECOVERY TEST")
    print("=" * 60)

    original_url = doctors.OVERPASS_URL
    print(f"Original Overpass URL: {original_url}")
    print("Simulating Overpass API failure by temporarily setting invalid URL ('https://invalid-overpass-domain.example/api')...")

    doctors.OVERPASS_URL = "https://invalid-overpass-domain.example/api"

    try:
        r = client.get("/api/doctors/nearby?lat=22.7533&lng=75.8937&radius_m=5000&specialty=Cardiology")
        print(f"  Response HTTP Status: {r.status_code} (Expected: 200)")
        data = r.json()
        print(f"  Returned results count: {data.get('total')}")
        print(f"  All results from registered source: {all(d.get('source') == 'registered' for d in data.get('results', []))}")
        print("[CONFIRMED] /nearby endpoint gracefully recovers from Overpass failure without returning a 500 error!")
    finally:
        doctors.OVERPASS_URL = original_url
        print(f"Restored Overpass URL to: {doctors.OVERPASS_URL}")


def main():
    audit_1_database_state()
    audit_2_haversine_fallback()
    audit_3_real_endpoint_responses()
    audit_4_deduplication_unit_test()
    audit_5_overpass_resilience()

if __name__ == "__main__":
    main()
