import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { Doctor } from '../types';
import { DoctorCard } from '../components/DoctorCard';
import { PractoSearchBar } from '../components/PractoSearchBar';
import { AppointmentModal } from '../components/AppointmentModal';
import { SkeletonDoctorCard } from '../components/SkeletonLoader';
import { EmptyState } from '../components/EmptyState';
import { getDoctorImage } from '../utils/doctorImages';
import { Search, Sparkles, RefreshCw, Stethoscope, MapPin, Globe } from 'lucide-react';

export const DoctorsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';
  const initialSpec = searchParams.get('specialization') || '';

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>(initialSearch);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  const [searchMode, setSearchMode] = useState<'standard' | 'nearby' | 'vector'>('nearby');
  const [activeLocationName, setActiveLocationName] = useState<string>('Indore, MP');
  const [activeSpecialty, setActiveSpecialty] = useState<string>(initialSpec);

  useEffect(() => {
    // Default initial search around Indore coordinates
    fetchNearbyDoctors({
      lat: 22.7533,
      lng: 75.8937,
      locationName: 'Indore, MP',
      specialty: initialSpec
    });
  }, []);

  const fetchNearbyDoctors = async (params: { lat: number; lng: number; locationName: string; specialty: string }) => {
    setLoading(true);
    setSearchMode('nearby');
    setActiveLocationName(params.locationName);
    setActiveSpecialty(params.specialty);

    try {
      let url = `/doctors/nearby?lat=${params.lat}&lng=${params.lng}&radius_m=10000`;
      if (params.specialty) {
        url += `&specialty=${encodeURIComponent(params.specialty)}`;
      }

      const res = await api.get(url);
      const rawResults = res.data?.results || [];

      const mappedDoctors: Doctor[] = rawResults.map((d: any) => ({
        ...d,
        image_url: d.image_url || getDoctorImage({ id: d.id, name: d.name })
      }));

      setDoctors(mappedDoctors);
    } catch (err) {
      console.error('Failed to fetch nearby doctors:', err);
      // Fallback to standard doctor list on error
      fetchStandardDoctors(params.specialty);
    } finally {
      setLoading(false);
    }
  };

  const fetchStandardDoctors = async (specialization?: string) => {
    setLoading(true);
    setSearchMode('standard');
    try {
      let url = '/doctors';
      if (specialization) url += `?specialization=${encodeURIComponent(specialization)}`;
      const res = await api.get(url);
      setDoctors(res.data || []);
    } catch (err) {
      console.error('Failed to fetch doctors:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVectorSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) {
      fetchStandardDoctors();
      return;
    }

    setLoading(true);
    setSearchMode('vector');
    try {
      const res = await api.post('/doctors/search', { query: search, limit: 12 });
      const results = res.data.results || [];
      const mappedDoctors: Doctor[] = results.map((r: any) => ({
        id: r.doctor_id || r.id,
        hospital_id: r.hospital_id,
        name: r.doctor_name || r.name,
        degree: r.degree,
        specialization: r.specialization,
        experience_years: r.experience_years || 5,
        designation: r.designation,
        languages: ['English', 'Hindi'],
        consultation_fee: r.consultation_fee || 500,
        availability: r.availability,
        image_url: getDoctorImage({ id: r.doctor_id || r.id, name: r.doctor_name || r.name }),
        source: 'registered',
        bookable: true
      }));
      setDoctors(mappedDoctors);
    } catch (err) {
      console.error('Doctor vector search failed:', err);
      fetchStandardDoctors();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header Section with Practo-Style Dual Search Bar */}
      <div className="bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 text-xs font-semibold text-tealmed-300 border border-white/20">
          <Stethoscope className="w-4 h-4" /> Practo-Style Nearby Doctor Search
        </div>

        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Find Nearby Specialist Doctors</h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl mt-1 leading-relaxed">
            Set your location and select a medical specialty to find bookable clinic doctors and external facilities near you.
          </p>
        </div>

        {/* Practo Dual Search Bar */}
        <PractoSearchBar
          onSearch={fetchNearbyDoctors}
          initialSpecialty={initialSpec}
        />

        {/* Secondary AI Vector Text Search */}
        <form onSubmit={handleVectorSearch} className="flex items-center gap-2 pt-2 border-t border-white/10 max-w-2xl">
          <span className="text-xs text-slate-300 font-semibold flex-shrink-0">Or search symptoms/names:</span>
          <div className="relative flex-1">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="e.g. Cardiologist with 10+ years experience..."
              className="w-full pl-9 pr-3 py-1.5 bg-white/10 hover:bg-white/15 text-white rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-tealmed-400 placeholder:text-slate-400 border border-white/10"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          </div>
          <button
            type="submit"
            className="px-3.5 py-1.5 bg-tealmed-500 hover:bg-tealmed-600 text-white font-bold text-xs rounded-xl shadow flex items-center gap-1 flex-shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5" /> AI Search
          </button>
        </form>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            {searchMode === 'nearby' && <MapPin className="w-5 h-5 text-medical-600" />}
            {searchMode === 'nearby'
              ? `Nearby Doctors & Clinics (${activeLocationName})`
              : searchMode === 'vector'
              ? 'AI Search Results'
              : 'Available Doctors'}
            <span className="text-xs text-slate-500 font-normal">({doctors.length} found)</span>
          </h2>
          {activeSpecialty && (
            <p className="text-xs text-medical-600 font-semibold mt-0.5">
              Filtered by Specialty: {activeSpecialty}
            </p>
          )}
        </div>

        {searchMode !== 'standard' && (
          <button
            onClick={() => fetchStandardDoctors()}
            className="text-xs text-medical-600 font-semibold flex items-center gap-1 hover:underline"
          >
            <RefreshCw className="w-3.5 h-3.5" /> View All Registered Doctors
          </button>
        )}
      </div>

      {/* Doctor Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => <SkeletonDoctorCard key={i} />)}
        </div>
      ) : doctors.length === 0 ? (
        <EmptyState
          title="No doctors or clinics found"
          description="We couldn't find any doctor matching your specified location or specialty."
          action={
            <button
              onClick={() => {
                setSearch('');
                fetchNearbyDoctors({ lat: 22.7533, lng: 75.8937, locationName: 'Indore, MP', specialty: '' });
              }}
              className="px-4 py-2 bg-medical-600 text-white font-semibold text-xs rounded-xl shadow"
            >
              Reset Search
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doc) => (
            <DoctorCard
              key={doc.id}
              doctor={doc}
              hospitalName={doc.hospital_name || (doc.hospital_id === 'H001' ? 'Sunrise Hospital' : 'Green Valley Centre')}
              onBook={(d) => {
                setSelectedDoctor(d);
                setModalOpen(true);
              }}
            />
          ))}
        </div>
      )}

      {/* OpenStreetMap Attribution */}
      {doctors.some((d) => d.source === 'external') && (
        <div className="pt-6 border-t border-slate-200 text-center text-xs text-slate-500 flex items-center justify-center gap-1.5">
          <Globe className="w-4 h-4 text-slate-400" />
          <span>External clinic & geolocation data provided by</span>
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noopener noreferrer"
            className="font-bold text-medical-600 hover:underline"
          >
            © OpenStreetMap contributors
          </a>
        </div>
      )}

      <AppointmentModal
        doctor={selectedDoctor}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
};
