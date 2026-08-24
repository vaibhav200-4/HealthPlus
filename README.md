# HealthPulse — Production-Style Hospital Appointment System

Full-stack hospital appointment web application built around an existing **n8n AI Agent workflow**, **Pinecone Vector Store**, **Google Gemini API**, **Google Calendar**, and **Supabase Database & Auth**.

---

## 🌟 Architecture Overview

- **Frontend**: React (v18), Vite, Tailwind CSS, Lucide Icons, Framer Motion
- **Backend**: FastAPI (Python 3.10+), Uvicorn, Pydantic, HTTPX
- **Database**: Supabase PostgreSQL (or local fallback mode for offline dev)
- **Authentication**: Supabase Auth (or JWT bearer token authentication)
- **AI Agent Workflow**: Existing n8n Webhook & Postgres Chat Memory
- **Semantic Vector Search**: Pinecone Vector Index (`hospital-doctors`) + Google Gemini Embeddings (`models/gemini-embedding-001`)
- **Calendar & Availability**: Google Calendar + Google Sheets schedule synchronization

---

## 🔑 Environment Variables Setup

Create a `.env` file at the project root using `.env.example`:

```env
# n8n AI Agent Production Webhook URL
N8N_WEBHOOK_URL=

# Supabase Credentials
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Pinecone Vector Search
PINECONE_API_KEY=
PINECONE_INDEX_NAME=hospital-doctors

# Google Gemini API Key
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-google-api-key
```

> [!CAUTION]
> Secrets like `SUPABASE_SERVICE_ROLE_KEY`, `PINECONE_API_KEY`, and `GOOGLE_API_KEY` are strictly used on the FastAPI backend and never exposed to client-side browser JavaScript.

---

## 🚀 How to Run locally

### 1. Run Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Run Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```
- Local Web App: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Demo Login Credentials

- **Admin Account**:
  - Email: `admin@hospital.com`
  - Password: `admin123`

---

## 🏛️ Database Migrations

SQL schema definition file is stored at:
`supabase/migrations/01_init_schema.sql`

Tables included:
1. `profiles`: User account details, role (`user` | `admin`), and optional `telegram_id`
2. `hospitals`: Hospital nodes (e.g. Sunrise Multispeciality, Green Valley Centre)
3. `doctors`: Medical specialists, consultation fees, and degree info
4. `schedules`: Shift availability synchronized with Google Sheets
5. `appointments`: Double-booking validated appointment records
6. `chat_messages`: Persisted Web Chat and Telegram AI transcripts

---

## 🛡️ Double Booking Protection & Unified Booking Logic

Both **Manual Web Booking** and **AI Assistant Booking** use the exact same server-side validation workflow (`BookingService`).
When a slot is booked, the backend verifies slot availability before confirming and inserting the appointment record into Supabase. If a double-booking attempt occurs, the API returns:
```json
{
  "success": false,
  "message": "This slot is no longer available."
}
```
