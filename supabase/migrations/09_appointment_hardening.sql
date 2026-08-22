-- Migration 09: Appointment Lifecycle, Idempotency & Partial Unique Constraint

ALTER TABLE public.appointments
    ADD COLUMN IF NOT EXISTS hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS schedule_id UUID REFERENCES public.schedules(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reason TEXT,
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

-- Update appointment status check constraint
ALTER TABLE public.appointments DROP CONSTRAINT IF EXISTS appointments_status_check;
ALTER TABLE public.appointments ADD CONSTRAINT appointments_status_check
    CHECK (status IN ('pending', 'confirmed', 'checked_in', 'in_progress', 'completed', 'cancelled', 'rejected', 'no_show'));

-- Partial unique index for active appointment slots to prevent race-condition double bookings
CREATE UNIQUE INDEX IF NOT EXISTS idx_active_appointments_slot 
    ON public.appointments(doctor_id, date, start_time) 
    WHERE status IN ('confirmed', 'pending', 'checked_in', 'in_progress');

CREATE INDEX IF NOT EXISTS idx_appointments_idempotency_key ON public.appointments(idempotency_key);
