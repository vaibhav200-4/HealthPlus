-- Migration 02: Hospital Multi-Tenancy & Membership Schema

-- 1. Extend hospitals table with additional fields
ALTER TABLE public.hospitals 
    ADD COLUMN IF NOT EXISTS registration_number TEXT,
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS logo_url TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- 2. Create hospital_members table to bind profiles to hospitals with granular roles
CREATE TABLE IF NOT EXISTS public.hospital_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'doctor', 'staff')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (hospital_id, user_id)
);

-- 3. Extend profiles role constraint to support super_admin
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check 
    CHECK (role IN ('patient', 'user', 'doctor', 'staff', 'admin', 'super_admin'));
