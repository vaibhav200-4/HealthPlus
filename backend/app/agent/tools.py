import io
import uuid
import qrcode
from typing import Annotated, Optional, Dict, Any, List
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from starlette.concurrency import run_in_threadpool

from app.database.supabase_client import SupabaseService, get_supabase_client
from app.services.schedule_service import ScheduleService
from app.services.booking_service import BookingService
from app.services.patient_service import PatientService
from app.api.medical_records import generate_signed_url
from app.agent.state import AgentState

# NOTE: user_id / thread_id / patient_id are NEVER parameters an LLM fills in below.
# They're marked Annotated[AgentState, InjectedState] instead — LangGraph's ToolNode
# strips these from the JSON schema shown to the model and injects the real values
# from graph state at call time. This is what stops the agent from asking the human
# for "your user ID" — it never sees that field exists.
# REQUIRES: agent/graph.py must invoke tools through langgraph.prebuilt.ToolNode
# (not a manual/custom tool-call loop) for injection to actually happen.

@tool
async def search_doctors(specialty: Optional[str] = None, hospital_name: Optional[str] = None, doctor_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for available doctors by specialty, hospital name, and/or the doctor's
    own name. Always call this to resolve a doctor's identity — including when the
    user names a specific doctor by name — never ask the user for a doctor ID directly."""
    def _search():
        doctors = SupabaseService.get_records("doctors")

        hospitals = {h["id"]: h.get("name", h.get("hospital_name", "")) for h in SupabaseService.get_records("hospitals")}
        departments = {d["id"]: d.get("name", "") for d in SupabaseService.get_records("departments")}

        results = []
        for doc in doctors:
            h_name = hospitals.get(doc.get("hospital_id"), "")
            dept_name = departments.get(doc.get("department_id"), "")
            doc_specialty = doc.get("specialty") or doc.get("specialization") or dept_name or ""

            if specialty and (specialty.lower() not in doc_specialty.lower() and specialty.lower() not in dept_name.lower()):
                continue

            if hospital_name and hospital_name.lower() not in h_name.lower():
                continue

            if doctor_name and doctor_name.lower() not in (doc.get("name") or "").lower():
                continue

            results.append({
                "id": doc.get("id"),
                "name": doc.get("name"),
                "specialty": doc_specialty,
                "hospital_name": h_name,
                "department_name": dept_name,
                "experience_years": doc.get("experience_years"),
                "consultation_fee": doc.get("consultation_fee"),
                "rating": doc.get("rating")
            })
        return results

    return await run_in_threadpool(_search)

@tool
async def check_availability(doctor_id: str, date: str) -> List[Dict[str, Any]]:
    """Check available time slots for a doctor on a specific date (YYYY-MM-DD). Use
    a doctor_id you got from search_doctors — never one asked directly from the user."""
    return await run_in_threadpool(ScheduleService.get_doctor_available_slots, doctor_id, date)

@tool
async def generate_mock_payment(amount_context: str) -> Dict[str, Any]:
    """Generates a mock payment reference, QR code image, stores it in Supabase medical-records bucket, and returns signed URL."""
    def _gen_payment():
        payment_reference = f"MOCK-{uuid.uuid4().hex[:8]}"  # was uuid4() — undefined, only `uuid` module was imported
        storage_path = f"payments/{payment_reference}.png"

        qr_img = qrcode.make(f"HEALTHPULSE_PAYMENT:{payment_reference}:{amount_context}")
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        file_bytes = img_buffer.getvalue()

        client = get_supabase_client()
        if client:
            try:
                try:
                    client.storage.create_bucket("medical-records", options={"public": False})
                except Exception:
                    pass
                client.storage.from_("medical-records").upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": "image/png"}
                )
            except Exception:
                pass

        signed_url = generate_signed_url(storage_path)
        return {
            "payment_reference": payment_reference,
            "qr_code_url": signed_url,
            "amount_context": amount_context,
            "status": "pending_confirmation"
        }

    return await run_in_threadpool(_gen_payment)

@tool
async def book_appointment(
    doctor_id: str,
    date: str,
    start_time: str,
    end_time: str,
    state: Annotated[AgentState, InjectedState],
    notes: Optional[str] = ""
) -> Dict[str, Any]:
    """Book an appointment for the current patient after resolving doctor details and
    verifying availability. The patient's identity is taken automatically from the
    logged-in session — never ask the user for their user ID or patient ID."""
    user_id = state["user_id"]
    thread_id = state["thread_id"]

    def _book():
        doc_rec = SupabaseService.get_record_by_id("doctors", doctor_id)
        if not doc_rec:
            return {"success": False, "message": f"Doctor {doctor_id} not found."}

        doctor_name = doc_rec.get("name", "Doctor")
        hospital_name = "Hospital"
        if doc_rec.get("hospital_id"):
            h_rec = SupabaseService.get_record_by_id("hospitals", doc_rec["hospital_id"])
            if h_rec:
                hospital_name = h_rec.get("name") or h_rec.get("hospital_name", "Hospital")

        p_rec = PatientService.resolve_patient(user_id)
        prof_rec = SupabaseService.get_record_by_id("profiles", user_id) or {}

        patient_name = prof_rec.get("name") or f"Patient ({p_rec.get('patient_code', 'PT-000')})"
        patient_phone = prof_rec.get("phone") or prof_rec.get("mobile", "")
        patient_email = prof_rec.get("email", "")

        idempotency_key = f"{thread_id}-{doctor_id}-{date}-{start_time}"

        success, msg, app_data = BookingService.create_appointment(
            user_id=user_id,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            hospital_name=hospital_name,
            date=date,
            start_time=start_time,
            end_time=end_time,
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=patient_email,
            notes=notes or "",
            idempotency_key=idempotency_key
        )
        return {"success": success, "message": msg, "appointment": app_data}

    return await run_in_threadpool(_book)

@tool
async def save_intake_note(
    content: str,
    state: Annotated[AgentState, InjectedState],
    structured_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Save post-booking patient intake notes (symptoms, prior doctor, past reports
    mentioned) into the database. Patient and appointment identity are taken
    automatically from the current conversation — never ask the user for these IDs."""
    patient_id = state["patient_id"]
    thread_id = state["thread_id"]
    appointment_id = (state.get("booking_draft") or {}).get("appointment_id")

    def _save():
        note_data = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "thread_id": thread_id,
            "content": content,
            "structured_data": structured_data or {},
            "source": "agent"
        }
        inserted = SupabaseService.insert_record("patient_intake_notes", note_data)
        return {"success": True, "note_id": inserted.get("id")}

    return await run_in_threadpool(_save)