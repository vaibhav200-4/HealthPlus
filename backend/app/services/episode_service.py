import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from app.database.supabase_client import SupabaseService
from app.services.patient_service import PatientService

logger = logging.getLogger("hospital_app.episodes")


class EpisodeService:
    @staticmethod
    def get_or_create_active_episode(patient_id_or_ref: str, condition: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the current 'active' clinical episode for a patient,
        or creates a new active episode if none exists.
        """
        patient = PatientService.resolve_patient(patient_id_or_ref)
        patient_id = patient.get("id")

        episodes = SupabaseService.get_records("episodes", {"patient_id": patient_id, "status": "active"})
        if episodes:
            logger.info(f"Reusing active episode {episodes[0]['id']} for patient {patient_id}")
            return episodes[0]

        now_str = datetime.now(timezone.utc).isoformat()
        new_episode = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "condition": condition.strip() if condition and condition.strip() else "General Health Care",
            "started_at": now_str,
            "resolved_at": None,
            "status": "active",
            "summary": None,
            "summary_generated_at": None,
            "summary_source_record_ids": [],
            "created_at": now_str,
            "updated_at": now_str
        }

        created = SupabaseService.insert_record("episodes", new_episode)
        logger.info(f"Created new active episode {new_episode['id']} for patient {patient_id}")
        return created or new_episode

    @staticmethod
    def resolve_episode(episode_id: str, doctor_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Marks an episode of care as 'resolved'.
        """
        episode = SupabaseService.get_record_by_id("episodes", episode_id)
        if not episode:
            return None

        now_str = datetime.now(timezone.utc).isoformat()
        updates = {
            "status": "resolved",
            "resolved_at": now_str,
            "updated_at": now_str
        }

        updated = SupabaseService.update_record("episodes", episode_id, updates)
        logger.info(f"Resolved episode {episode_id} (Resolved by doctor: {doctor_id or 'System'})")
        return updated

    @staticmethod
    def get_patient_episodes(patient_id_or_ref: str) -> Dict[str, Any]:
        """
        Fetches all episodes for a patient, categorized into active and past resolved episodes.
        Refreshes active episode summary if stale using lazy caching.
        """
        patient = PatientService.resolve_patient(patient_id_or_ref)
        patient_id = patient.get("id")

        all_episodes = SupabaseService.get_records("episodes", {"patient_id": patient_id})
        all_episodes.sort(key=lambda x: x.get("started_at") or "", reverse=True)

        active = None
        past = []

        for ep in all_episodes:
            if ep.get("status") == "active" and active is None:
                active = ep
            else:
                past.append(ep)

        if active:
            try:
                from app.services.summary_service import SummaryService
                sum_res = SummaryService.generate_episode_summary(active["id"])
                if sum_res and "summary" in sum_res:
                    active["summary"] = sum_res["summary"]
                    active["summary_generated_at"] = sum_res.get("generated_at")
            except Exception as e:
                logger.warning(f"Could not refresh summary for active episode {active.get('id')}: {e}")

        return {
            "patient_id": patient_id,
            "active_episode": active,
            "past_episodes": past,
            "total_episodes": len(all_episodes)
        }

