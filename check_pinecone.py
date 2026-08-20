"""
Diagnostic script: checks what doctor_id values are actually stored in your
Pinecone index, so you can compare them against data.json (D001-D010).

Run from backend/ directory so it can import app.config:
    python check_pinecone_doctor_ids.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.config import settings
from pinecone import Pinecone

def main():
    if not settings.PINECONE_API_KEY:
        print("PINECONE_API_KEY not set in .env — cannot check.")
        return

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)

    stats = index.describe_index_stats()
    print(f"Index: {settings.PINECONE_INDEX_NAME}")
    print(f"Total vectors: {stats.get('total_vector_count')}\n")

    # Dummy near-zero vector just to pull back a sample of records with metadata.
    # Dimension must match your embedding config (768 per pinecone_service.py).
    dim = 768
    dummy_vector = [0.0001] * dim

    result = index.query(vector=dummy_vector, top_k=20, include_metadata=True)

    print(f"Sample of {len(result.matches)} stored vectors:\n")
    print(f"{'doctor_id':<12} {'doctor_name':<25} {'hospital_id':<12} {'specialization':<20}")
    print("-" * 70)
    for match in result.matches:
        md = match.metadata or {}
        print(f"{str(md.get('doctor_id')):<12} {str(md.get('doctor_name')):<25} "
              f"{str(md.get('hospital_id')):<12} {str(md.get('specialization')):<20}")

    print("\nExpected IDs from data.json: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010")
    print("Expected hospital IDs: H001, H002, H003, H004, H005")
    print("\nCompare the doctor_id / hospital_id columns above against these.")
    print("If they don't match, Pinecone data needs to be re-seeded to align with Supabase.")

if __name__ == "__main__":
    main()