-- Voice agent alignment migration
-- Additive and idempotent: no drops, no type changes, no destructive updates.
-- Put this in supabase/migrations/. Run 00_diagnostics.sql first.

-- 1. Backfill appointments.hospital_id from the doctor's hospital where it is missing.
update public.appointments a
set hospital_id = d.hospital_id
from public.doctors d
where a.hospital_id is null
  and a.doctor_id = d.id
  and d.hospital_id is not null;

-- 1b. Rows whose doctor link is gone (doctor_id is null): fall back to the stored hospital name.
update public.appointments a
set hospital_id = h.id
from public.hospitals h
where a.hospital_id is null
  and a.hospital_name = h.hospital_name;

-- 2. Lookup indexes for the queries the voice agent runs.
create index if not exists idx_appointments_doctor_date
  on public.appointments (doctor_id, date);
create index if not exists idx_appointments_user
  on public.appointments (user_id);
create index if not exists idx_appointments_patient_phone
  on public.appointments (patient_phone);
create index if not exists idx_schedules_doctor
  on public.schedules (doctor_id);
create index if not exists idx_doctor_leaves_doctor_date
  on public.doctor_leaves (doctor_id, leave_date);
create index if not exists idx_blocked_slots_doctor_date
  on public.blocked_slots (doctor_id, slot_date);

-- 3. Idempotency: the same key can never create two appointments.
do $$
begin
  if exists (
    select 1 from public.appointments
    where idempotency_key is not null
    group by idempotency_key having count(*) > 1
  ) then
    raise notice 'Skipped uq_appointments_idempotency_key: duplicate keys exist.';
  else
    create unique index if not exists uq_appointments_idempotency_key
      on public.appointments (idempotency_key)
      where idempotency_key is not null;
  end if;
end $$;

-- 4. Database-level double-booking guard (backstop for the race between check and insert).
do $$
begin
  if exists (
    select 1 from public.appointments
    where doctor_id is not null
      and status in ('confirmed','pending','booked','checked_in','in_progress')
    group by doctor_id, date, start_time having count(*) > 1
  ) then
    raise notice 'Skipped uq_appointments_active_slot: duplicate active bookings exist. Resolve diagnostics #8 and re-run.';
  else
    create unique index if not exists uq_appointments_active_slot
      on public.appointments (doctor_id, date, start_time)
      where doctor_id is not null
        and status in ('confirmed','pending','booked','checked_in','in_progress');
  end if;
end $$;

-- 5. RLS: handled in the separate file 30_rls_lockdown.sql (run it only after its checklist).
-- The commented list below is superseded by that file; leave it commented.
-- alter table public.patients          enable row level security;
-- alter table public.medical_records   enable row level security;
-- alter table public.prescriptions     enable row level security;
-- alter table public.prescription_items enable row level security;
-- alter table public.sessions          enable row level security;
-- alter table public.episodes          enable row level security;
-- alter table public.notifications     enable row level security;
-- alter table public.audit_logs        enable row level security;
-- alter table public.patient_summaries enable row level security;
-- alter table public.patient_intake_notes enable row level security;
