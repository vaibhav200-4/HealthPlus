"""
Backfill Doctor Geolocation Script
-----------------------------------
Populates `latitude` and `longitude` columns on the `doctors` table in Supabase
using OpenStreetMap Nominatim geocoding.

Key features:
- Uses Supabase Python client with service role key to bypass RLS policies.
- Idempotent: skips doctor rows that already have non-null latitude and longitude.
- Retrieves address from doctor record or joined hospital record.
- Enforces OpenStreetMap Nominatim 1 req/sec rate limit with progressive fallback geocoding.
- Logs any failed geocoding attempts for manual resolution.
- Reports final summary of geocoded vs missing/bad address doctors.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Ensure backend module path is accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from supabase import create_client, Client
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("backfill_doctor_geolocation")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "HealthPulse-Doctor-Geocoder/1.0 (contact@healthpulse.example)"
RATE_LIMIT_DELAY_SECONDS = 1.1


def get_service_role_client() -> Client:
    """Initialize Supabase client using Service Role key for administrative write access."""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured in environment.")
    logger.info("Initializing Supabase client with service role key...")
    return create_client(url, key)


def format_address_from_hospital(hospital: Dict[str, Any]) -> Optional[str]:
    """Format address string from a hospital object."""
    if not hospital:
        return None
    street = hospital.get("street") or ""
    area = hospital.get("area") or ""
    city = hospital.get("city") or ""
    state = hospital.get("state") or ""
    pincode = hospital.get("pincode") or ""
    country = hospital.get("country") or "India"

    parts = [p.strip() for p in [street, area, city, state, pincode, country] if p and p.strip()]
    return ", ".join(parts) if parts else None


def format_doctor_address(doc: Dict[str, Any], hospital: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Extract and format address from doctor record or fallback to hospital address."""
    doc_addr = doc.get("address")
    if doc_addr:
        if isinstance(doc_addr, str) and doc_addr.strip():
            return doc_addr.strip()
        elif isinstance(doc_addr, dict):
            parts = [
                doc_addr.get("street"),
                doc_addr.get("area"),
                doc_addr.get("city"),
                doc_addr.get("state"),
                doc_addr.get("pincode"),
                doc_addr.get("country") or "India"
            ]
            valid_parts = [str(p).strip() for p in parts if p and str(p).strip()]
            if valid_parts:
                return ", ".join(valid_parts)

    if hospital:
        return format_address_from_hospital(hospital)

    return None


def generate_geocode_variants(address: str) -> list:
    """
    Generate fallback query variations for Nominatim to handle mock/hypothetical street numbers.
    """
    variants = []

    # 1. Original full address
    variants.append(address)

    # Split by comma
    parts = [p.strip() for p in address.split(",") if p.strip()]

    # 2. Skip first element (e.g. street number / house number) if 4+ parts present
    if len(parts) >= 4:
        variants.append(", ".join(parts[1:]))

    # 3. Area, City, State/Country
    if len(parts) >= 4:
        # e.g. Area, City, Country
        variants.append(f"{parts[1]}, {parts[2]}, {parts[-1]}")
    
    # 4. City, State, Country
    if len(parts) >= 4:
        variants.append(f"{parts[2]}, {parts[3]}, {parts[-1]}")
    elif len(parts) >= 3:
        variants.append(f"{parts[-3]}, {parts[-2]}, {parts[-1]}")

    # Remove duplicates while preserving order
    seen = set()
    deduped = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            deduped.append(v)

    return deduped


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Geocode an address using Nominatim API, respecting the 1 req/sec rate limit.
    Returns (latitude, longitude, matched_query) or (None, None, None).
    """
    headers = {"User-Agent": USER_AGENT}
    variants = generate_geocode_variants(address)

    for query in variants:
        params = {"q": query, "format": "json", "limit": 1}
        try:
            time.sleep(RATE_LIMIT_DELAY_SECONDS)
            response = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return lat, lon, query
        except Exception as e:
            logger.warning(f"Error querying Nominatim for query '{query}': {e}")

    return None, None, None


def backfill_geocoding():
    """Main execution function for doctor geolocation backfill."""
    client = get_service_role_client()

    logger.info("Fetching doctors and associated hospital addresses...")
    response = client.table("doctors").select("*, hospitals(*)").execute()
    doctors = response.data or []

    total_doctors = len(doctors)
    logger.info(f"Total doctor records found: {total_doctors}")

    updated_count = 0
    already_geocoded_count = 0
    failed_geocoding = []
    missing_address = []

    for doc in doctors:
        doc_id = doc.get("id")
        doc_name = doc.get("name", "Unknown Doctor")
        lat = doc.get("latitude")
        lng = doc.get("longitude")

        # Re-run safety check: skip if lat and lon are already populated
        if lat is not None and lng is not None:
            already_geocoded_count += 1
            logger.info(f"[SKIP] Doctor ID {doc_id} ({doc_name}) already has coordinates ({lat}, {lng}).")
            continue

        hospital = doc.get("hospitals")
        address = format_doctor_address(doc, hospital)

        if not address:
            missing_address.append({"id": doc_id, "name": doc_name, "reason": "No address on doctor or hospital"})
            logger.warning(f"[MISSING ADDRESS] Doctor ID {doc_id} ({doc_name}) has no address available.")
            continue

        logger.info(f"[GEOCODING] Doctor ID {doc_id} ({doc_name}) | Address: '{address}'")
        found_lat, found_lng, matched_query = geocode_address(address)

        if found_lat is not None and found_lng is not None:
            # Update Supabase record
            try:
                upd_res = client.table("doctors").update({
                    "latitude": found_lat,
                    "longitude": found_lng
                }).eq("id", doc_id).execute()
                
                updated_count += 1
                logger.info(
                    f"[SUCCESS] Updated Doctor ID {doc_id} ({doc_name}) -> "
                    f"Lat: {found_lat}, Lon: {found_lng} (Matched query: '{matched_query}')"
                )
            except Exception as e:
                logger.error(f"[UPDATE ERROR] Failed to update Supabase for doctor {doc_id}: {e}")
                failed_geocoding.append({"id": doc_id, "name": doc_name, "address": address, "reason": str(e)})
        else:
            logger.error(f"[GEOCODE FAILED] Could not geocode address for Doctor ID {doc_id} ({doc_name}): '{address}'")
            failed_geocoding.append({"id": doc_id, "name": doc_name, "address": address, "reason": "Geocoding returned no results"})

    # Fetch final count of doctors with non-null coordinates
    final_res = client.table("doctors").select("id, name, latitude, longitude").execute()
    final_docs = final_res.data or []
    non_null_count = sum(1 for d in final_docs if d.get("latitude") is not None and d.get("longitude") is not None)
    still_null_docs = [d for d in final_docs if d.get("latitude") is None or d.get("longitude") is None]

    print("\n" + "=" * 60)
    print("BACKFILL GEOLOCATION SUMMARY REPORT")
    print("=" * 60)
    print(f"Total doctor rows evaluated        : {total_doctors}")
    print(f"Already geocoded prior to run     : {already_geocoded_count}")
    print(f"Newly updated in this run          : {updated_count}")
    print(f"Total doctor rows with lat/lng now : {non_null_count} / {total_doctors}")
    print(f"Doctor rows lacking lat/lng        : {len(still_null_docs)}")
    print("=" * 60)

    if still_null_docs:
        print("\nDoctors still missing latitude/longitude:")
        for d in still_null_docs:
            print(f"  - ID: {d.get('id')} | Name: {d.get('name')}")

    if failed_geocoding:
        print("\nAddresses that failed geocoding:")
        for f in failed_geocoding:
            print(f"  - ID: {f['id']} | Name: {f['name']} | Address: {f.get('address')} | Reason: {f.get('reason')}")

    if missing_address:
        print("\nDoctors missing addresses completely:")
        for m in missing_address:
            print(f"  - ID: {m['id']} | Name: {m['name']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    backfill_geocoding()
