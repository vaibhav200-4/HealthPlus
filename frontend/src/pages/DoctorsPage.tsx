import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { Doctor } from '../types';
import { DoctorCard } from '../components/DoctorCard';
import { AppointmentModal } from '../components/AppointmentModal';
import { SkeletonDoctorCard } from '../components/SkeletonLoader';
import { EmptyState } from '../components/EmptyState';
import { Search, Filter, Sparkles, RefreshCw, Stethoscope } from 'lucide-react';

export const DoctorsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';
  const initialSpec = searchParams.get('specialization') || '';

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>(initialSearch);
  const [specialization, setSpecialization] = useState<string>(initialSpec);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [isVectorSearch, setIsVectorSearch] = useState<boolean>(false);

  useEffect(() => {
    fetchDoctors();
  }, [specialization]);

  const fetchDoctors = async () => {
    setLoading(true);
    try {
      let url = '/doctors';
      const params: string[] = [];
      if (specialization) params.push(`specialization=${encodeURIComponent(specialization)}`);
      if (search) params.push(`search=${encodeURIComponent(search)}`);
      if (params.length > 0) url += `?${params.join('&')}`;

      const res = await api.get(url);
      setDoctors(res.data || []);
      setIsVectorSearch(false);
    } catch (err) {
      console.error('Failed to fetch doctors:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVectorSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) {
      fetchDoctors();
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/doctors/search', { query: search, limit: 6 });
      const results = res.data.results || [];
      const mappedDoctors: Doctor[] = results.map((r: any) => ({
        id: r.doctor_id,
        hospital_id: r.hospital_id,
        name: r.doctor_name,
        degree: r.degree,
        specialization: r.specialization,
        experience_years: r.experience_years || 5,
        designation: r.designation,
        languages: ['English', 'Hindi'],
        consultation_fee: r.consultation_fee || 500,
        availability: r.availability,
        image_url: 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80'
      }));
      setDoctors(mappedDoctors);
      setIsVectorSearch(true);
    } catch (err) {
      console.error('Pinecone vector search failed:', err);
      fetchDoctors();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-900 rounded-3xl p-8 text-white shadow-xl space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 text-xs font-semibold text-tealmed-300 border border-white/20">
          <Stethoscope className="w-4 h-4" /> Verified Medical Directory & Pinecone Search
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight">Find Top Specialist Doctors</h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
          Search by doctor name, specialization, or medical concern. Powered by standard filtering and Pinecone vector semantic search.
        </p>

        {/* Search Bar */}
        <form onSubmit={handleVectorSearch} className="flex flex-col sm:flex-row gap-3 pt-2 max-w-2xl">
          <div className="relative flex-1">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="e.g. Cardiologist with 10+ years experience..."
              className="w-full pl-10 pr-4 py-3 bg-white text-slate-900 rounded-2xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-tealmed-400 placeholder:text-slate-400"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-tealmed-500 hover:bg-tealmed-600 text-white font-bold text-sm rounded-2xl shadow-lg shadow-tealmed-500/20 flex items-center justify-center gap-2 transition-all"
          >
            <Sparkles className="w-4 h-4" /> AI Vector Search
          </button>
        </form>
      </div>

      {/* Specialization Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-4">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-2 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5" /> Specialty:
        </span>
        {['All', 'Cardiology', 'Neurology', 'Pediatrics', 'Dermatology'].map((spec) => {
          const isSel = (spec === 'All' && !specialization) || specialization.toLowerCase() === spec.toLowerCase();
          return (
            <button
              key={spec}
              onClick={() => setSpecialization(spec === 'All' ? '' : spec)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                isSel
                  ? 'bg-medical-600 text-white shadow-md shadow-medical-500/20'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {spec}
            </button>
          );
        })}
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">
          {isVectorSearch ? 'Pinecone Semantic Search Results' : 'Available Doctors'}{' '}
          <span className="text-xs text-slate-500 font-normal">({doctors.length} found)</span>
        </h2>
        {isVectorSearch && (
          <button
            onClick={fetchDoctors}
            className="text-xs text-medical-600 font-semibold flex items-center gap-1 hover:underline"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reset Filters
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
          title="No doctors found"
          description="We couldn't find any doctor matching your search query or department filter."
          action={
            <button
              onClick={() => {
                setSearch('');
                setSpecialization('');
                fetchDoctors();
              }}
              className="px-4 py-2 bg-medical-600 text-white font-semibold text-xs rounded-xl shadow"
            >
              Clear Filters
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doc) => (
            <DoctorCard
              key={doc.id}
              doctor={doc}
              hospitalName={doc.hospital_id === 'H001' ? 'Sunrise Hospital' : 'Green Valley Centre'}
              onBook={(d) => {
                setSelectedDoctor(d);
                setModalOpen(true);
              }}
            />
          ))}
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
