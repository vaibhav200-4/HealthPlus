import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger("hospital_app.pinecone")

class PineconeService:
    _pc_client = None
    _gemini_client = None

    @classmethod
    def _init_clients(cls):
        if not cls._gemini_client and settings.GOOGLE_API_KEY:
            try:
                from google import genai
                cls._gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client in PineconeService: {e}")

        if not cls._pc_client and settings.PINECONE_API_KEY:
            try:
                from pinecone import Pinecone
                cls._pc_client = Pinecone(api_key=settings.PINECONE_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone client: {e}")

    @classmethod
    def search_doctors(cls, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        cls._init_clients()
        if not cls._pc_client or not cls._gemini_client:
            logger.warning("Pinecone or Gemini client not configured for semantic search.")
            return []

        try:
            from google.genai import types
            embedding_res = cls._gemini_client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=query,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=768
                )
            )
            query_vector = embedding_res.embeddings[0].values

            index = cls._pc_client.Index(settings.PINECONE_INDEX_NAME)
            search_res = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )

            results = []
            for match in search_res.matches:
                metadata = match.metadata or {}
                results.append({
                    "score": match.score,
                    "doctor_id": metadata.get("doctor_id"),
                    "doctor_name": metadata.get("doctor_name"),
                    "hospital_id": metadata.get("hospital_id"),
                    "hospital_name": metadata.get("hospital_name"),
                    "specialization": metadata.get("specialization"),
                    "degree": metadata.get("degree"),
                    "designation": metadata.get("designation"),
                    "experience_years": metadata.get("experience_years"),
                    "city": metadata.get("city"),
                    "consultation_fee": metadata.get("consultation_fee"),
                    "availability": metadata.get("availability"),
                    "text": metadata.get("text")
                })
            return results
        except Exception as e:
            logger.error(f"Error performing Pinecone search: {e}")
            return []
