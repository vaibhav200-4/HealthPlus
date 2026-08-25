-- Migration 15: Extend Medical Records Table with uploaded_by, file_type, and file_size_bytes

ALTER TABLE public.medical_records 
  ADD COLUMN IF NOT EXISTS uploaded_by TEXT NOT NULL DEFAULT 'patient' CHECK (uploaded_by IN ('patient','doctor','admin')),
  ADD COLUMN IF NOT EXISTS file_type TEXT,
  ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER;
