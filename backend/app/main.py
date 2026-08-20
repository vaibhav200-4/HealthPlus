import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, doctors, hospitals, schedules, appointments, chat, admin, telegram_webhook
from seed_data import seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hospital_app")

app = FastAPI(
    title="Hospital Appointment System API",
    description="Full-stack FastAPI backend integrated with n8n AI agent workflow, Supabase, and Pinecone",
    version="1.0.0"
)

# Configure CORS explicitly for frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows localhost Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(hospitals.router)
app.include_router(schedules.router)
app.include_router(appointments.router)
app.include_router(chat.router)
app.include_router(telegram_webhook.router)
app.include_router(admin.router)

# @app.on_event("startup")
# def on_startup():
#     logger.info("Initializing Hospital System Backend...")
#     try:
#         seed()
#     except Exception as e:
#         logger.warning(f"Seeding warning: {e}")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "n8n_webhook_configured": bool(settings.N8N_WEBHOOK_URL),
        "supabase_configured": bool(settings.SUPABASE_URL and "your-supabase" not in settings.SUPABASE_URL),
        "pinecone_configured": bool(settings.PINECONE_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
