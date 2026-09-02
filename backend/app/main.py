import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, doctors, hospitals, departments, schedules, appointments, chat, admin, telegram_webhook, sessions, prescriptions, medical_records, reviews, ai_tools, location

from app.database.supabase_client import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hospital_app")

app = FastAPI(
    title="Hospital Appointment System API",
    description="Full-stack FastAPI backend integrated with LangGraph in-process agent, Supabase, and Pinecone",
    version="1.0.0"
)

# Configure CORS explicitly for configured origins and Vercel domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(doctors.alias_router)
app.include_router(location.router)
app.include_router(location.alias_router)
app.include_router(hospitals.router)
app.include_router(departments.router)
app.include_router(schedules.router)
app.include_router(appointments.router)
app.include_router(sessions.router)
app.include_router(prescriptions.router)
app.include_router(medical_records.router)
app.include_router(reviews.router)
app.include_router(chat.router)
app.include_router(telegram_webhook.router)
app.include_router(admin.router)
app.include_router(ai_tools.router)

from app.agent.memory import setup_checkpointer

@app.on_event("startup")
async def on_startup():
    logger.info("Initializing Hospital System Backend...")
    is_active = SupabaseService.is_supabase_active()
    if settings.ENVIRONMENT.lower() == "production" and not is_active:
        logger.critical("CRITICAL: Application set to production mode but Supabase database credentials are missing or invalid!")
        raise RuntimeError("CRITICAL: Production startup failed! Active Supabase database connection is required in production.")
    elif not is_active:
        logger.warning("WARNING: Running in DEVELOPMENT mode with in-memory local database fallback.")

    await setup_checkpointer()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "LangGraph Agent Hospital Assistant",
        "supabase_configured": bool(settings.SUPABASE_URL and "your-supabase" not in settings.SUPABASE_URL),
        "pinecone_configured": bool(settings.PINECONE_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
