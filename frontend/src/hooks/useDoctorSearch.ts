import { useState, useRef, useCallback, useEffect } from 'react';
import api from '../services/api';
import { Doctor } from '../types';
import { getDoctorImage } from '../utils/doctorImages';

export interface SearchNearbyParams {
  lat: number;
  lng: number;
  locationName: string;
  specialty: string;
  registeredOnly?: boolean;
}

export function useDoctorSearch() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState<'standard' | 'nearby' | 'vector'>('nearby');
  const [activeLocationName, setActiveLocationName] = useState<string>('Indore, MP');
  const [activeSpecialty, setActiveSpecialty] = useState<string>('');

  const abortControllerRef = useRef<AbortController | null>(null);

  // Clean up pending requests on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const getNewAbortSignal = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    return abortControllerRef.current.signal;
  }, []);

  const sanitizeSpecialty = (spec: string): string => {
    if (!spec) return '';
    const trimmed = spec.trim().toLowerCase();
    const exactAllValues = new Set([
      '',
      'all',
      'all specialties',
      'all specializations',
      'all specialties / specializations',
      'none',
      'null'
    ]);
    if (exactAllValues.has(trimmed)) {
      return '';
    }
    return spec.trim();
  };

  const searchStandardInternal = async (specialization?: string, signal?: AbortSignal, registeredOnly?: boolean) => {
    try {
      let url = '/doctors';
      const cleanSpec = sanitizeSpecialty(specialization || '');
      if (cleanSpec) {
        url += `?specialization=${encodeURIComponent(cleanSpec)}`;
      }
      const res = await api.get(url, { signal });
      let list: Doctor[] = res.data || [];
      if (registeredOnly) {
        list = list.filter((d: any) => d.source !== 'external');
      }
      setDoctors(list);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED' || err?.name === 'AbortError') {
        return;
      }
      console.error('Failed to fetch standard doctors:', err);
      setError('Failed to load doctor directory. Please check network connection.');
      setDoctors([]);
    }
  };

  const searchNearby = useCallback(async (params: SearchNearbyParams) => {
    const signal = getNewAbortSignal();
    setLoading(true);
    setError(null);
    setSearchMode('nearby');
    setActiveLocationName(params.locationName || 'Specified Location');

    const cleanSpecialty = sanitizeSpecialty(params.specialty);
    setActiveSpecialty(cleanSpecialty);

    try {
      let url = `/doctors/nearby?lat=${params.lat}&lng=${params.lng}&radius_m=10000`;
      if (cleanSpecialty) {
        url += `&specialty=${encodeURIComponent(cleanSpecialty)}`;
      }
      if (params.registeredOnly) {
        url += `&registered_only=true`;
      }

      const res = await api.get(url, { signal });
      const rawResults = res.data?.results || [];

      if (rawResults.length === 0) {
        // Fallback to standard registered doctor list if nearby returns zero results
        setError('No nearby results matched your query. Showing registered doctor directory.');
        await searchStandardInternal(cleanSpecialty, signal, params.registeredOnly);
      } else {
        const mappedDoctors: Doctor[] = rawResults.map((d: any) => ({
          ...d,
          image_url: d.image_url || getDoctorImage({ id: d.id, name: d.name })
        }));
        setDoctors(mappedDoctors);
      }
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED' || err?.name === 'AbortError') {
        return;
      }
      console.error('Failed to fetch nearby doctors:', err);
      setError('Nearby location search encountered an issue. Showing registered doctor directory.');
      await searchStandardInternal(cleanSpecialty, signal, params.registeredOnly);
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [getNewAbortSignal]);

  const searchStandard = useCallback(async (specialization?: string) => {
    const signal = getNewAbortSignal();
    setLoading(true);
    setError(null);
    setSearchMode('standard');
    const cleanSpec = sanitizeSpecialty(specialization || '');
    setActiveSpecialty(cleanSpec);

    try {
      await searchStandardInternal(cleanSpec, signal);
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [getNewAbortSignal]);

  const searchVector = useCallback(async (query: string) => {
    if (!query.trim()) {
      await searchStandard();
      return;
    }

    const signal = getNewAbortSignal();
    setLoading(true);
    setError(null);
    setSearchMode('vector');

    try {
      const res = await api.post('/doctors/search', { query: query.trim(), limit: 12 }, { signal });
      const results = res.data?.results || [];
      const mappedDoctors: Doctor[] = results.map((r: any) => ({
        id: r.doctor_id || r.id,
        hospital_id: r.hospital_id || 'H001',
        hospital_name: r.hospital_name || 'Sunrise Hospital',
        name: r.doctor_name || r.name,
        degree: r.degree || 'MBBS',
        specialization: r.specialization || 'General Medicine',
        experience_years: r.experience_years || 5,
        designation: r.designation || 'Consultant',
        languages: ['English', 'Hindi'],
        consultation_fee: r.consultation_fee || 500,
        availability: r.availability || 'Mon-Sat, 10 AM - 4 PM',
        image_url: getDoctorImage({ id: r.doctor_id || r.id, name: r.doctor_name || r.name }),
        source: 'registered',
        bookable: true
      }));
      setDoctors(mappedDoctors);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED' || err?.name === 'AbortError') {
        return;
      }
      console.error('Doctor vector search failed:', err);
      setError('AI search service encountered an error. Falling back to registered directory.');
      await searchStandardInternal('', signal);
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [getNewAbortSignal, searchStandard]);

  return {
    doctors,
    loading,
    error,
    searchMode,
    activeLocationName,
    activeSpecialty,
    searchNearby,
    searchStandard,
    searchVector,
    clearError: () => setError(null)
  };
}
