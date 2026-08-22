-- Migration 03: Patient Model & Auto-generated Patient Code

CREATE SEQUENCE IF NOT EXISTS public.patient_code_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS public.patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE CASCADE,
    patient_code TEXT UNIQUE NOT NULL DEFAULT ('PT-' || lpad(nextval('public.patient_code_seq')::text, 6, '0')),
    date_of_birth DATE,
    gender TEXT,
    blood_group TEXT,
    address TEXT,
    emergency_contact TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
