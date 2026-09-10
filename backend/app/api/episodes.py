from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from app.services.episode_service import EpisodeService
from app.services.summary_service import SummaryService
from app.auth.auth_handler import get_identity_context, require_doctor

router = APIRouter(prefix="/api/episodes", tags=["Clinical Episodes"])

@router.get("/patient/{patient_id}")
def get_patient_episodes(patient_id: str, identity: dict = Depends(get_identity_context)):
    return EpisodeService.get_patient_episodes(patient_id)

@router.get("/{episode_id}/summary")
def get_episode_summary(
    episode_id: str,
    force_regenerate: bool = Query(False),
    identity: dict = Depends(get_identity_context)
):
    return SummaryService.generate_episode_summary(episode_id, force_regenerate=force_regenerate)

@router.post("/{episode_id}/summary/regenerate")
def regenerate_episode_summary(
    episode_id: str,
    identity: dict = Depends(get_identity_context)
):
    return SummaryService.generate_episode_summary(episode_id, force_regenerate=True)

@router.post("/{episode_id}/resolve")
def resolve_episode(episode_id: str, doctor_info: dict = Depends(require_doctor)):
    doc_id = doctor_info["doctor"]["id"]
    updated = EpisodeService.resolve_episode(episode_id, doctor_id=doc_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {"success": True, "message": "Episode resolved successfully", "episode": updated}

