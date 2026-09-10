-- ===========================================================================
-- Migration 19: Add hospital_id to profiles and update role check constraint for hospital_admin
-- ===========================================================================

-- 1. Add hospital_id column to profiles table if it does not exist
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE SET NULL;

-- 2. Update profiles_role_check constraint to include 'hospital_admin'
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check 
    CHECK (role IN ('patient', 'user', 'doctor', 'staff', 'admin', 'super_admin', 'hospital_admin'));
