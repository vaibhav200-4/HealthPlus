-- Migration 18: Add Episodes Table and Extend Medical Records with OCR Fields

-- 1. Create Episodes Table
CREATE TABLE IF NOT EXISTS public.episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES public.patients(id) ON DELETE CASCADE,
    condition TEXT NOT NULL DEFAULT 'General Health',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ NULLABLE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved')),
    summary TEXT NULLABLE,
    summary_generated_at TIMESTAMPTZ NULLABLE,
    summary_source_record_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Extend Medical Records Table with OCR & Episode Link
ALTER TABLE public.medical_records
  ADD COLUMN IF NOT EXISTS extracted_text TEXT,
  ADD COLUMN IF NOT EXISTS ocr_status TEXT NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'completed', 'failed')),
  ADD COLUMN IF NOT EXISTS ocr_processed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS episode_id UUID REFERENCES public.episodes(id) ON DELETE SET NULL;

-- 3. Indexes for Efficient Episode & OCR Lookups
CREATE INDEX IF NOT EXISTS idx_episodes_patient_status ON public.episodes(patient_id, status);
CREATE INDEX IF NOT EXISTS idx_medical_records_episode_id ON public.medical_records(episode_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_ocr_status ON public.medical_records(ocr_status);
