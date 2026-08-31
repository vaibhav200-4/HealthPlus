-- Migration 16: Add Geolocation Support to Doctors Table

-- 1. Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Add two new nullable columns to doctors table for latitude and longitude
ALTER TABLE public.doctors
  ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;

-- 3. Add generated location column of type geography(Point, 4326)
-- Computed from longitude and latitude when both are present
ALTER TABLE public.doctors
  ADD COLUMN IF NOT EXISTS location GEOGRAPHY(Point, 4326)
  GENERATED ALWAYS AS (
    CASE 
      WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
      ELSE NULL
    END
  ) STORED;

-- 4. Add GIST spatial index on location column for spatial queries
CREATE INDEX IF NOT EXISTS idx_doctors_location ON public.doctors USING GIST (location);
