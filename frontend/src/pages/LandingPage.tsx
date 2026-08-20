import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useChat } from '../context/ChatContext';
import api from '../services/api';
import { Doctor } from '../types';
import { DoctorCard } from '../components/DoctorCard';
import { AppointmentModal } from '../components/AppointmentModal';
import { SkeletonDoctorCard } from '../components/SkeletonLoader';
import { 
  HeartPulse, 
  Search, 
  Bot, 
  Sparkles, 
  ShieldCheck, 
  Clock, 
  Calendar, 
  ArrowRight, 
  Award, 
  Users, 
  Activity,
  CheckCircle,
  Brain,
  Stethoscope,
  Heart,
  Baby
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { setIsOpen, sendMessage } = useChat();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  useEffect(() => {
    fetchFeaturedDoctors();
  }, []);

  const fetchFeaturedDoctors = async () => {
    try {
      const res = await api.get('/doctors');
      setDoctors(res.data.slice(0, 4));
    } catch (err) {
      console.error('Failed to fetch doctors:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/doctors?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleBookDoctor = (doc: Doctor) => {
    setSelectedDoctor(doc);
    setModalOpen(true);
  };

  const specializations = [
    { title: 'Cardiology', count: '12+ Specialists', icon: Heart, color: 'bg-rose-50 text-rose-600 border-rose-100' },
    { title: 'Neurology', count: '8+ Specialists', icon: Brain, color: 'bg-indigo-50 text-indigo-600 border-indigo-100' },
    { title: 'Pediatrics', count: '10+ Specialists', icon: Baby, color: 'bg-amber-50 text-amber-600 border-amber-100' },
    { title: 'Dermatology', count: '6+ Specialists', icon: Stethoscope, color: 'bg-tealmed-50 text-tealmed-600 border-tealmed-100' },
  ];

  return (
    <div className="space-y-20 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-medical-50/70 via-slate-50 to-white pt-12 pb-20 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Content */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-medical-100/80 border border-medical-200 text-medical-800 text-xs font-bold">
                <Sparkles className="w-4 h-4 text-medical-600" />
                <span>Next-Gen n8n AI Healthcare Platform</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
                Smart Hospital Appointments &{' '}
                <span className="bg-gradient-to-r from-medical-600 via-medical-500 to-tealmed-600 bg-clip-text text-transparent">
                  AI Consultation
                </span>
              </h1>

              <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl">
                Experience seamless healthcare booking. Search verified specialist doctors, check real-time schedule availability, or ask our intelligent AI Assistant to guide your healthcare journey.
              </p>

              {/* Search Bar */}
              <form onSubmit={handleSearchSubmit} className="relative max-w-xl">
                <div className="flex items-center bg-white p-2 rounded-2xl shadow-xl border border-slate-200/80 focus-within:border-medical-500 transition-all">
                  <Search className="w-5 h-5 text-slate-400 ml-3 flex-shrink-0" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search doctor name, cardiology, hospital..."
                    className="w-full px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="px-5 py-2.5 bg-medical-600 hover:bg-medical-700 text-white font-semibold text-sm rounded-xl shadow-md shadow-medical-500/20 transition-all"
                  >
                    Search
                  </button>
                </div>
              </form>

              {/* CTAs */}
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  onClick={() => setIsOpen(true)}
                  className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-tealmed-500 to-medical-600 text-white font-bold text-sm shadow-xl shadow-tealmed-500/20 hover:scale-[1.02] transition-all"
                >
                  <Bot className="w-5 h-5" />
                  Ask AI Healthcare Assistant
                </button>
                <Link
                  to="/doctors"
                  className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-white border border-slate-200 text-slate-800 font-bold text-sm hover:bg-slate-50 transition-all shadow-sm"
                >
                  Browse Doctors Directory
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                </Link>
              </div>

              {/* Key Trust Stats */}
              <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-200/60 max-w-lg">
                <div>
                  <span className="block text-2xl font-extrabold text-slate-900">50+</span>
                  <span className="text-xs font-medium text-slate-500">Expert Doctors</span>
                </div>
                <div>
                  <span className="block text-2xl font-extrabold text-slate-900">100%</span>
                  <span className="text-xs font-medium text-slate-500">Real-Time Sync</span>
                </div>
                <div>
                  <span className="block text-2xl font-extrabold text-slate-900">24/7</span>
                  <span className="text-xs font-medium text-slate-500">AI Support</span>
                </div>
              </div>
            </div>

            {/* Right Hero Image Card */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md rounded-3xl overflow-hidden shadow-2xl border-4 border-white bg-white">
                <img
                  src="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&auto=format&fit=crop&q=80"
                  alt="Modern Hospital Facility"
                  className="w-full h-[420px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent"></div>

                {/* Floating Info Overlay */}
                <div className="absolute bottom-6 left-6 right-6 p-4 bg-white/90 backdrop-blur-md rounded-2xl border border-white/50 text-slate-900 shadow-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-medical-700 uppercase tracking-wider">Top Hospital Partner</span>
                    <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-ping"></span>
                  </div>
                  <h4 className="font-extrabold text-sm text-slate-900">Sunrise Multispeciality Hospital</h4>
                  <p className="text-xs text-slate-600">45 Vijay Nagar Main Road, Indore, MP</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Specialization Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
          <span className="text-xs font-bold uppercase tracking-wider text-medical-600">Specialist Departments</span>
          <h2 className="text-3xl font-extrabold text-slate-900">Explore Medical Specialties</h2>
          <p className="text-sm text-slate-500">Consult top verified medical specialists across key departments.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {specializations.map((spec, idx) => {
            const Icon = spec.icon;
            return (
              <Link
                key={idx}
                to={`/doctors?specialization=${encodeURIComponent(spec.title)}`}
                className={`p-6 rounded-3xl border ${spec.color} transition-all duration-300 hover:-translate-y-1 hover:shadow-xl group`}
              >
                <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center shadow-sm mb-4 group-hover:scale-110 transition-transform">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-1">{spec.title}</h3>
                <p className="text-xs text-slate-500 font-medium mb-3">{spec.count}</p>
                <span className="text-xs font-bold flex items-center gap-1 group-hover:underline">
                  View Doctors <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Featured Doctors Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between mb-8">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-medical-600">Verified Specialists</span>
            <h2 className="text-3xl font-extrabold text-slate-900">Featured Hospital Doctors</h2>
          </div>
          <Link
            to="/doctors"
            className="text-xs font-bold text-medical-700 hover:text-medical-800 flex items-center gap-1"
          >
            View All ({doctors.length}+) <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => <SkeletonDoctorCard key={i} />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {doctors.map((doc) => (
              <DoctorCard
                key={doc.id}
                doctor={doc}
                hospitalName={doc.hospital_id === 'H001' ? 'Sunrise Hospital' : 'Green Valley Centre'}
                onBook={handleBookDoctor}
              />
            ))}
          </div>
        )}
      </section>

      {/* AI Assistant Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-900 rounded-3xl p-8 sm:p-12 text-white relative overflow-hidden shadow-2xl">
          <div className="relative z-10 max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-semibold text-tealmed-300 border border-white/20">
              <Bot className="w-4 h-4" /> Powered by Gemini & n8n Automation
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Need Instant Appointment Booking via Natural Chat?
            </h2>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Just open our AI Assistant and type: <br />
              <span className="font-mono text-tealmed-300 text-xs bg-slate-950/50 px-2 py-1 rounded">"Book Dr. Neha tomorrow at 4 PM"</span> or <span className="font-mono text-tealmed-300 text-xs bg-slate-950/50 px-2 py-1 rounded">"Find me a pediatrician"</span>
            </p>
            <button
              onClick={() => {
                setIsOpen(true);
                sendMessage("Find me an available doctor tomorrow");
              }}
              className="px-6 py-3.5 bg-gradient-to-r from-tealmed-400 to-medical-400 text-slate-950 font-bold text-sm rounded-xl shadow-lg hover:scale-105 transition-all inline-flex items-center gap-2"
            >
              <Bot className="w-5 h-5" /> Start AI Chat Now
            </button>
          </div>
        </div>
      </section>

      {/* Appointment Modal */}
      <AppointmentModal
        doctor={selectedDoctor}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
};
