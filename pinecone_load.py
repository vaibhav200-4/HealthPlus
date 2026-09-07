import os
import json
from dotenv import load_dotenv

from google import genai
from google.genai import types

from pinecone import Pinecone


# ============================================================
# CONFIG
# ============================================================

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app.config import settings

GEMINI_API_KEY = settings.GOOGLE_API_KEY
PINECONE_API_KEY = settings.PINECONE_API_KEY
INDEX_NAME = settings.PINECONE_INDEX_NAME

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 3072


# ============================================================
# VALIDATE API KEYS
# ============================================================

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in .env")


# ============================================================
# INITIALIZE CLIENTS
# ============================================================

print("Initializing Gemini...")

gemini = genai.Client(
    api_key=GEMINI_API_KEY
)

print("Initializing Pinecone...")

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(INDEX_NAME)


# ============================================================
# LOAD JSON
# ============================================================

print("\nLoading data.json...")

with open("data.json", "r", encoding="utf-8") as file:
    hospitals = json.load(file)

print(f"Loaded {len(hospitals)} hospitals")


# ============================================================
# CREATE SEARCH DOCUMENT
# ============================================================

def create_document(hospital, doctor):

    address = hospital["address"]

    text = f"""
Doctor: {doctor["name"]}

Doctor ID: {doctor["doctor_id"]}

Hospital: {hospital["hospital_name"]}

Hospital ID: {hospital["hospital_id"]}

Location:
{address["street"]},
{address["area"]},
{address["city"]},
{address["state"]},
{address["pincode"]},
{address["country"]}

Degree:
{doctor["degree"]}

Specialization:
{doctor["specialization"]}

Designation:
{doctor["designation"]}

Experience:
{doctor["experience_years"]} years

Languages:
{", ".join(doctor["languages"])}

Consultation Fee:
₹{doctor["consultation_fee"]}

Availability:
{doctor["availability"]}

Hospital Departments:
{", ".join(hospital["departments"])}

Hospital Phone:
{hospital["phone"]}
"""

    return text.strip()


# ============================================================
# GENERATE GEMINI EMBEDDING
# ============================================================

def generate_embedding(text):

    result = gemini.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )

    return result.embeddings[0].values


# ============================================================
# PROCESS DOCTORS
# ============================================================

vectors = []

total_doctors = sum(
    len(hospital["doctors"])
    for hospital in hospitals
)

print(f"Found {total_doctors} doctors\n")


for hospital in hospitals:

    for doctor in hospital["doctors"]:

        doctor_id = doctor["doctor_id"]

        print(f"Embedding {doctor_id} - {doctor['name']}...")

        # Create searchable text
        document = create_document(
            hospital,
            doctor
        )

        # Generate embedding using Gemini API
        embedding = generate_embedding(document)

        # Create Pinecone vector
        vector = {
            "id": doctor_id,

            "values": embedding,

            "metadata": {
                "doctor_id": doctor_id,
                "doctor_name": doctor["name"],

                "hospital_id": hospital["hospital_id"],
                "hospital_name": hospital["hospital_name"],

                "specialization": doctor["specialization"],
                "degree": doctor["degree"],
                "designation": doctor["designation"],

                "experience_years": doctor["experience_years"],

                "city": hospital["address"]["city"],
                "area": hospital["address"]["area"],
                "pincode": hospital["address"]["pincode"],

                "languages": ", ".join(
                    doctor["languages"]
                ),

                "consultation_fee": doctor["consultation_fee"],

                "availability": doctor["availability"],

                # Original searchable document
                "text": document
            }
        }

        vectors.append(vector)


# ============================================================
# UPLOAD TO PINECONE
# ============================================================

print("\nUploading vectors to Pinecone...")

index.upsert(
    vectors=vectors
)

print("✅ Upload successful!")


# ============================================================
# VERIFY
# ============================================================

print("\nChecking Pinecone index...")

stats = index.describe_index_stats()

print(stats)

print("\n====================================")
print("DONE")
print("====================================")
print(f"Hospitals : {len(hospitals)}")
print(f"Doctors   : {total_doctors}")
print(f"Dimension : {EMBEDDING_DIMENSION}")
print(f"Index     : {INDEX_NAME}")
print("====================================")