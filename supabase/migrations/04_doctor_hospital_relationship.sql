-- Migration 04: Doctor-Hospital Relationship & Indexing

-- Create explicit indexes on profile_id and hospital_id for doctors
CREATE INDEX IF NOT EXISTS idx_doctors_profile_id ON public.doctors(profile_id);
CREATE INDEX IF NOT EXISTS idx_doctors_hospital_id ON public.doctors(hospital_id);
CREATE INDEX IF NOT EXISTS idx_hospital_members_user_id ON public.hospital_members(user_id);
CREATE INDEX IF NOT EXISTS idx_hospital_members_hospital_id ON public.hospital_members(hospital_id);
