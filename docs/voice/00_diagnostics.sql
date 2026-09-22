-- READ-ONLY. Run each block separately in the Supabase SQL editor and paste the results back.
-- These answer what the schema export cannot show: FKs, CHECKs, RLS state, real data values.

-- 1. Foreign keys / checks / uniques on the tables the voice agent touches
select conrelid::regclass as table_name, conname, contype, pg_get_constraintdef(oid) as definition
from pg_constraint
where contype in ('f', 'c', 'u')
  and conrelid = any (array[
    'public.appointments','public.doctors','public.hospitals','public.profiles',
    'public.patients','public.schedules','public.doctor_leaves',
    'public.hospital_holidays','public.blocked_slots'
  ]::regclass[])
order by 1, 2;

-- 2. Is RLS enabled per table? (tables with rls_enabled = false are open to anyone holding the anon key)
select c.relname as table_name,
       c.relrowsecurity as rls_enabled,
       (select count(*) from pg_policies p
         where p.schemaname = 'public' and p.tablename = c.relname) as policy_count
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r'
order by c.relrowsecurity, c.relname;

-- 3. Status values actually stored in appointments
select status, count(*) from public.appointments group by 1 order by 2 desc;

-- 4. Specialization spellings actually stored (Orthopedics vs Orthopaedics, Gynecology vs Gynaecology)
select specialization, count(*) from public.doctors group by 1 order by 1;

-- 5. Which hospitals really exist (compare with MASTER_DOCTORS and HOSPITAL_ALIASES)
select id, hospital_name, status, city, area from public.hospitals order by id;

-- 6. Doctors pointing at a hospital that does not exist
select d.id, d.name, d.hospital_id
from public.doctors d
left join public.hospitals h on h.id = d.hospital_id
where d.hospital_id is not null and h.id is null;

-- 7. Doctor ids in the DB (are D001.., D101.. from MASTER_DOCTORS present?)
select id, name, specialization, hospital_id from public.doctors order by id;

-- 8. Duplicate active bookings (these would block the unique index in the migration)
select doctor_id, date, start_time, count(*)
from public.appointments
where status in ('confirmed','pending','booked','checked_in','in_progress')
group by 1, 2, 3
having count(*) > 1;

-- 9. Appointments missing hospital_id (staff dashboards that filter by hospital will not see them)
select count(*) filter (where hospital_id is null) as missing_hospital_id, count(*) as total
from public.appointments;

-- 10. How schedules are stored (day_of_week format decides the day matching in the patch)
select distinct day_of_week from public.schedules order by 1;
select doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, is_active
from public.schedules limit 20;

-- 11. How start_time is stored in appointments ("09:00", "09:00:00", "9 AM"?)
select distinct start_time from public.appointments order by 1 limit 30;

-- 12. Rows booked by the anonymous voice sentinel user
select count(*) from public.appointments
where user_id = '00000000-0000-0000-0000-000000000001';
