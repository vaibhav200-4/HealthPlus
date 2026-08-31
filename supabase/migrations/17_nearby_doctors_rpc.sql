-- Migration 17: PostGIS RPC Function for Nearby Doctor Search

CREATE OR REPLACE FUNCTION get_nearby_doctors(
  p_lat DOUBLE PRECISION,
  p_lng DOUBLE PRECISION,
  p_radius_meters DOUBLE PRECISION DEFAULT 10000,
  p_specialty TEXT DEFAULT NULL
)
RETURNS TABLE (
  id TEXT,
  profile_id UUID,
  hospital_id TEXT,
  name TEXT,
  degree TEXT,
  specialization TEXT,
  experience_years INTEGER,
  designation TEXT,
  languages TEXT[],
  consultation_fee NUMERIC,
  availability TEXT,
  image_url TEXT,
  created_at TIMESTAMPTZ,
  department_id UUID,
  rating NUMERIC,
  total_reviews INTEGER,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  distance_meters DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    d.id,
    d.profile_id,
    d.hospital_id,
    d.name,
    d.degree,
    d.specialization,
    d.experience_years,
    d.designation,
    d.languages,
    d.consultation_fee,
    d.availability,
    d.image_url,
    d.created_at,
    d.department_id,
    d.rating,
    d.total_reviews,
    d.latitude,
    d.longitude,
    ST_Distance(
      d.location,
      ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
    ) AS distance_meters
  FROM public.doctors d
  WHERE d.location IS NOT NULL
    AND ST_DWithin(
      d.location,
      ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography,
      p_radius_meters
    )
    AND (
      p_specialty IS NULL 
      OR p_specialty = '' 
      OR LOWER(d.specialization) LIKE '%' || LOWER(p_specialty) || '%'
    )
  ORDER BY distance_meters ASC;
END;
$$;
