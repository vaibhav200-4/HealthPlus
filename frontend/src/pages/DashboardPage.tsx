import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import api from '../services/api';
import { Appointment, Doctor } from '../types';
import { AppointmentModal } from '../components/AppointmentModal';
import { DoctorCard } from '../components/DoctorCard';
import { SkeletonDoctorCard } from '../components/SkeletonLoader';
import { EmptyState } from '../components/EmptyState';
import { 
  Calendar, 
  Clock, 
  Bot, 
  Stethoscope, 
  Search, 
  User as UserIcon, 
  CheckCircle2, 
  XCircle, 
  ArrowRight,
  Sparkles,
  MapPin
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { setIsOpen } = useChat();

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [featuredDoctors, setFeaturedDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [appRes, docRes] = await Promise.all([
        api.get('/appointments/my'),
        api.get('/doctors')
      ]);
      setAppointments(appRes.data || []);
      setFeaturedDoctors((docRes.data || []).slice(0, 3));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const upcomingAppointment = appointments.find(
    (a) => a.status === 'confirmed' || a.status === 'pending'
  );

  return (
    <div className="space-y-8 pb-12">
      {/* Header Welcome Section */}
      <div className="bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-800 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-semibold text-tealmed-300">
            <Sparkles className="w-4 h-4 text-tealmed-300" /> Patient Dashboard
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {user?.name || 'Patient'}!
          </h1>
          <p className="text-xs sm:text-sm text-slate-300">
            Manage your hospital bookings, check active slots, or consult our AI Health Assistant.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-tealmed-500 hover:bg-tealmed-600 text-white font-bold text-xs shadow-lg shadow-tealmed-500/20 transition-all"
          >
            <Bot className="w-4 h-4" /> AI Health Assistant
          </button>
          <Link
            to="/doctors"
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-white text-slate-900 font-bold text-xs hover:bg-slate-100 transition-all shadow-sm"
          >
            <Stethoscope className="w-4 h-4 text-medical-600" /> Book Doctor
          </Link>
        </div>
      </div>

      {/* Grid: Upcoming Appointment & Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upcoming Appointment Card */}
        <div className="lg:col-span-8 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-medical-600" />
              Upcoming Appointment
            </h2>
            {upcomingAppointment && (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                Confirmed
              </span>
            )}
          </div>

          {upcomingAppointment ? (
            <div className="p-5 bg-medical-50/60 rounded-2xl border border-medical-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <span className="text-[11px] font-bold text-medical-700 uppercase tracking-wider">
                  {upcomingAppointment.hospital_name}
                </span>
                <h3 className="text-lg font-extrabold text-slate-900">
                  {upcomingAppointment.doctor_name}
                </h3>
                <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-600 pt-1">
                  <span className="flex items-center gap-1.5 bg-white px-3 py-1 rounded-lg border border-slate-200">
                    <Calendar className="w-3.5 h-3.5 text-medical-600" />
                    {upcomingAppointment.date}
                  </span>
                  <span className="flex items-center gap-1.5 bg-white px-3 py-1 rounded-lg border border-slate-200">
                    <Clock className="w-3.5 h-3.5 text-medical-600" />
                    {upcomingAppointment.start_time} - {upcomingAppointment.end_time}
                  </span>
                </div>
              </div>

              <Link
                to="/my-appointments"
                className="px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold text-xs rounded-xl shadow-sm transition-colors flex-shrink-0"
              >
                Manage Booking
              </Link>
            </div>
          ) : (
            <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
              <Clock className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-700">No upcoming appointments scheduled.</p>
              <p className="text-xs text-slate-500 mb-4">Book your consultation with top specialists today.</p>
              <Link
                to="/doctors"
                className="px-4 py-2 bg-medical-600 text-white font-semibold text-xs rounded-xl shadow-sm hover:bg-medical-700 transition-colors inline-block"
              >
                Find & Book Doctor
              </Link>
            </div>
          )}
        </div>

        {/* Quick Stats / Account Card */}
        <div className="lg:col-span-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900">Account Summary</h2>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
              <span className="text-slate-500 font-medium">Total Bookings</span>
              <span className="font-extrabold text-slate-900 text-sm">{appointments.length}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
              <span className="text-slate-500 font-medium">Active Telegram Sync</span>
              <span className={`font-bold px-2 py-0.5 rounded ${user?.telegram_id ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'}`}>
                {user?.telegram_id ? 'Linked' : 'Not Linked'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
              <span className="text-slate-500 font-medium">Account Role</span>
              <span className="font-bold text-medical-700 uppercase">{user?.role || 'user'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Doctors */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-900">Recommended Specialists</h2>
          <Link to="/doctors" className="text-xs font-bold text-medical-600 hover:underline flex items-center gap-1">
            View All <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => <SkeletonDoctorCard key={i} />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {featuredDoctors.map((doc) => (
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
      </div>

      <AppointmentModal
        doctor={selectedDoctor}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={fetchDashboardData}
      />
    </div>
  );
};
