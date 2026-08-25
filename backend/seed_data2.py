"""
===================================================================================
MANUAL DEMO-DATA SEEDING SCRIPT: seed_data2.py
===================================================================================
IMPORTANT: This is a standalone, developer-facing manual demo script.
It MUST NEVER be imported, called, or wired into application startup (main.py,
seed_data.py, or any background worker).

To execute manually:
    export ALLOW_DEMO_SEED=true  (or set in .env)
    py -3.10 backend/seed_data2.py
===================================================================================
"""

import sys
import os
import uuid
import logging
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.supabase_client import SupabaseService
from app.auth.auth_handler import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hospital_app.seed_data2")

DEMO_PATIENT_EMAIL_PREFIX = "demo_patient_"

def seed_demo_patients_and_bookings(force: bool = False):
    """
    Populates realistic patients, appointments, clinical sessions, prescriptions,
    medical records, and reviews for every doctor in the database.
    Guarded by ALLOW_DEMO_SEED environment setting.
    Idempotent: Skips execution if demo patients already exist.
    """

    if not settings.ALLOW_DEMO_SEED and not force:
        logger.warning("ALLOW_DEMO_SEED is False. Skipping demo patient & clinical data seeding.")
        logger.info("To run this manual script, set ALLOW_DEMO_SEED=true in your environment or .env file.")
        sys.exit(0)

    logger.info("Executing manual demo seeding for patients, appointments, and clinical records...")

    doctors = SupabaseService.get_records("doctors")
    if not doctors:
        logger.warning("No doctors found in database. Run seed_data.py first to populate hospitals and doctors.")
        return

    existing_demo_patients = SupabaseService.get_records("profiles")
    existing_demo_emails = [p.get("email", "") for p in existing_demo_patients if p.get("email", "").startswith(DEMO_PATIENT_EMAIL_PREFIX)]
    
    if existing_demo_emails and not force:
        logger.info(f"Found {len(existing_demo_emails)} existing demo patients. Seeding is already complete — skipping to prevent duplicates.")
        return

    logger.info(f"Found {len(doctors)} doctors. Seeding patient and clinical records for each doctor...")

    sample_names = ["Ramesh Kumar", "Priya Sharma", "Anita Verma", "Vikram Singh", "Sunita Patel", "Rahul Gupta", "Neha Kapoor", "Sanjay Reddy"]
    statuses_pool = ["completed", "confirmed", "cancelled"]
    password_hash = hash_password("patientdemo123")

    total_patients_created = 0
    total_appointments_created = 0
    total_sessions_created = 0
    total_prescriptions_created = 0
    total_reviews_created = 0
    total_records_created = 0

    for idx, doc in enumerate(doctors):
        doc_id = doc["id"]
        doc_name = doc.get("name", "Doctor")
        hospital_id = doc.get("hospital_id", "H001")
        
        hospitals = SupabaseService.get_records("hospitals", {"id": hospital_id})
        hospital_name = hospitals[0].get("hospital_name", "City Hospital") if hospitals else "City Hospital"

        num_patients = 2 + (idx % 2)
        for p_idx in range(num_patients):
            patient_uuid = str(uuid.uuid4())
            p_name = sample_names[(idx * 2 + p_idx) % len(sample_names)]
            p_email = f"{DEMO_PATIENT_EMAIL_PREFIX}{doc_id.lower()}_{p_idx+1}_{patient_uuid[:6]}@hospital.com"

            # 1. Create Profile
            profile_rec = {
                "id": patient_uuid,
                "name": p_name,
                "email": p_email,
                "password_hash": password_hash,
                "phone": f"+91 98765{idx:02d}{p_idx:03d}",
                "role": "patient"
            }
            SupabaseService.insert_record("profiles", profile_rec)

            # 2. Create Patient Record
            patient_code_val = f"PT-{uuid.uuid4().hex[:6].upper()}"
            patient_rec = {
                "id": str(uuid.uuid4()),
                "profile_id": patient_uuid,
                "hospital_id": hospital_id,
                "patient_code": patient_code_val,
                "gender": "Male" if p_idx % 2 == 0 else "Female",
                "blood_group": "O+" if p_idx % 2 == 0 else "A+",
                "address": f"{100 + idx*10 + p_idx} MG Road, {hospital_name}"
            }
            inserted_patient = SupabaseService.insert_record("patients", patient_rec)
            patient_db_id = inserted_patient.get("id") if inserted_patient else patient_rec["id"]
            total_patients_created += 1

            # 2b. Create 2-3 Mock Medical Records per patient (Task 7)
            sample_records = [
                {
                    "id": str(uuid.uuid4()),
                    "patient_id": patient_db_id,
                    "doctor_id": doc_id,
                    "record_type": "diagnosis",
                    "title": "Clinical Consultation & Diagnostic Summary",
                    "description": f"Initial clinical evaluation for {p_name}. Vitals stable, advised regular medication.",
                    "file_url": f"{patient_db_id}/consultation_summary.pdf",
                    "uploaded_by": "doctor",
                    "file_type": "pdf",
                    "file_size_bytes": 245000,
                    "created_at": "2026-08-15T10:30:00+00:00"
                },
                {
                    "id": str(uuid.uuid4()),
                    "patient_id": patient_db_id,
                    "doctor_id": doc_id,
                    "record_type": "lab_report",
                    "title": "Complete Blood Count (CBC) Panel",
                    "description": "Routine blood examination. Hemoglobin, RBC, and WBC within standard reference ranges.",
                    "file_url": f"{patient_db_id}/cbc_lab_report.pdf",
                    "uploaded_by": "patient",
                    "file_type": "pdf",
                    "file_size_bytes": 512000,
                    "created_at": "2026-08-18T14:15:00+00:00"
                },
                {
                    "id": str(uuid.uuid4()),
                    "patient_id": patient_db_id,
                    "doctor_id": doc_id,
                    "record_type": "xray" if p_idx % 2 == 0 else "mri",
                    "title": "Chest X-Ray AP View" if p_idx % 2 == 0 else "Brain MRI Scan Report",
                    "description": "Diagnostic radiological scan. No acute focal lesions or abnormalities detected.",
                    "file_url": f"{patient_db_id}/diagnostic_scan.png",
                    "uploaded_by": "doctor" if p_idx % 2 == 0 else "patient",
                    "file_type": "png",
                    "file_size_bytes": 1048576,
                    "created_at": "2026-08-20T09:00:00+00:00"
                }
            ]
            for rec in sample_records:
                SupabaseService.insert_record("medical_records", rec)
                total_records_created += 1

            # 3. Create 2 appointments for this patient with this doctor
            app_dates = [f"2026-08-{10 + (p_idx * 2):02d}", f"2026-09-{1 + (p_idx * 2):02d}"]
            for a_idx, a_date in enumerate(app_dates):
                app_id = str(uuid.uuid4())
                status_val = "completed" if a_idx == 0 else statuses_pool[(idx + p_idx) % len(statuses_pool)]
                
                app_rec = {
                    "id": app_id,
                    "user_id": patient_uuid,
                    "doctor_id": doc_id,
                    "hospital_id": hospital_id,
                    "doctor_name": doc_name,
                    "hospital_name": hospital_name,
                    "date": a_date,
                    "start_time": "10:00 AM" if a_idx == 0 else "03:00 PM",
                    "end_time": "10:30 AM" if a_idx == 0 else "03:30 PM",
                    "status": status_val,
                    "patient_name": p_name,
                    "patient_phone": profile_rec["phone"],
                    "patient_email": p_email,
                    "notes": f"Routine checkup and consultation for {doc.get('specialization', 'General')}."
                }
                SupabaseService.insert_record("appointments", app_rec)
                total_appointments_created += 1

                # 4. For completed appointments, create Clinical Session, Prescription, and Review
                if status_val == "completed":
                    session_id = str(uuid.uuid4())
                    session_rec = {
                        "id": session_id,
                        "appointment_id": app_id,
                        "doctor_id": doc_id,
                        "patient_id": patient_db_id,
                        "status": "completed",
                        "symptoms": "Mild fever, fatigue, seasonal allergies",
                        "diagnosis": f"Routine consultation for {doc.get('specialization', 'General')}",
                        "doctor_notes": f"Confidential: Patient is recovering well. Advised regular exercise and medication adherence."
                    }
                    SupabaseService.insert_record("sessions", session_rec)
                    total_sessions_created += 1

                    # Prescription
                    presc_id = str(uuid.uuid4())
                    presc_rec = {
                        "id": presc_id,
                        "patient_id": patient_db_id,
                        "doctor_id": doc_id,
                        "session_id": session_id,
                        "notes": "Take medications strictly after meals."
                    }
                    SupabaseService.insert_record("prescriptions", presc_rec)
                    total_prescriptions_created += 1

                    # Prescription Items
                    SupabaseService.insert_record("prescription_items", {
                        "id": str(uuid.uuid4()),
                        "prescription_id": presc_id,
                        "medicine_name": "Paracetamol 500mg",
                        "dosage": "1 tablet",
                        "frequency": "Twice daily",
                        "duration": "5 days",
                        "instructions": "After food"
                    })
                    SupabaseService.insert_record("prescription_items", {
                        "id": str(uuid.uuid4()),
                        "prescription_id": presc_id,
                        "medicine_name": "Vitamin C 500mg",
                        "dosage": "1 tablet",
                        "frequency": "Once daily",
                        "duration": "10 days",
                        "instructions": "Morning"
                    })

                    # Doctor Review
                    review_rec = {
                        "id": str(uuid.uuid4()),
                        "patient_id": patient_uuid,
                        "doctor_id": doc_id,
                        "appointment_id": app_id,
                        "rating": 5,
                        "review": f"Dr. {doc_name} was extremely attentive and gave excellent advice!"
                    }
                    SupabaseService.insert_record("doctor_reviews", review_rec)
                    total_reviews_created += 1

    logger.info("=" * 60)
    logger.info("DEMO SEEDING COMPLETED SUCCESSFULLY!")
    logger.info(f" -> Patients Created: {total_patients_created}")
    logger.info(f" -> Medical Records Created: {total_records_created}")
    logger.info(f" -> Appointments Created: {total_appointments_created}")
    logger.info(f" -> Clinical Sessions Created: {total_sessions_created}")
    logger.info(f" -> Prescriptions Created: {total_prescriptions_created}")
    logger.info(f" -> Doctor Reviews Created: {total_reviews_created}")
    logger.info("=" * 60)

if __name__ == "__main__":
    seed_demo_patients_and_bookings(force=False)
