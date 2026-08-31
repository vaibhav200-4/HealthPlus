import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, Query, HTTPException
import httpx

logger = logging.getLogger("hospital_app.location")

router = APIRouter(prefix="/api/location", tags=["Location"])
alias_router = APIRouter(prefix="/location", tags=["Location Alias"])

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "HealthPulse-Location-Geocoder/1.0 (contact@healthpulse.example)"
_GEOCODE_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
CACHE_TTL = 300  # 5 minutes


def _perform_geocode(q: str) -> List[Dict[str, Any]]:
    clean_q = q.strip().lower()
    now = time.time()

    # Check in-memory cache
    if clean_q in _GEOCODE_CACHE:
        timestamp, data = _GEOCODE_CACHE[clean_q]
        if now - timestamp < CACHE_TTL:
            return data

    headers = {"User-Agent": USER_AGENT}
    params = {"q": q, "format": "json", "limit": 5}

    try:
        r = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=8.0)
        if r.status_code == 200:
            raw_results = r.json()
            results = []
            for item in raw_results:
                results.append({
                    "display_name": item.get("display_name"),
                    "lat": float(item.get("lat")),
                    "lng": float(item.get("lon")),
                    "boundingbox": item.get("boundingbox")
                })
            _GEOCODE_CACHE[clean_q] = (now, results)
            return results
        else:
            logger.warning(f"Nominatim returned status {r.status_code} for query '{q}'")
            return []
    except Exception as e:
        logger.error(f"Error querying Nominatim for '{q}': {e}")
        return []


@router.get("/geocode")
@alias_router.get("/geocode")
def geocode_location(q: Optional[str] = Query(None, description="Address or place name to geocode")):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    
    results = _perform_geocode(q)
    return {"query": q, "results": results}
