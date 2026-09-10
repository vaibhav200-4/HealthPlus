import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { HospitalAdminSidebar } from '../../components/HospitalAdminSidebar';
import { 
  Stethoscope, 
  Building2, 
  ClipboardList, 
  Clock, 
  Building,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles
} from 'lucide-react';

export const HospitalAdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [hospitalProfile, setHospitalProfile] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, profileRes] = await Promise.all([
        api.get('/hospital-admin/stats'),
        api.get('/hospital-admin/profile')
      ]);
      setStats(statsRes.data);
      setHospitalProfile(profileRes.data);
    } catch (err) {
      console.error('Failed to fetch hospital admin dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <HospitalAdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-8 bg-slate-50/50 overflow-y-auto">
        
        {/* Banner Illustration Header */}
        <div className="relative overflow-hidden bg-gradient-to-r from-teal-900 via-teal-800 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-lg shadow-teal-900/10">
          <div className="relative z-10 space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-teal-800/60 rounded-full border border-teal-700/60 text-xs font-semibold text-teal-300">
              <Sparkles className="w-3.5 h-3.5 text-teal-300" />
              <span>Hospital Operations Console</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {hospitalProfile?.hospital_name || 'Hospital Dashboard'}
            </h1>
            <p className="text-sm text-teal-100/80">
              Manage your hospital's doctors, departments, shift schedules, and patient appointments from your dedicated management hub.
            </p>
          </div>

          <div className="absolute -right-6 -bottom-8 opacity-20 md:opacity-30 pointer-events-none">
            <Building2 className="w-64 h-64 text-teal-300" />
          </div>
        </div>

        {/* Analytics Cards */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white p-6 rounded-3xl border border-slate-200 animate-pulse space-y-4">
                <div className="h-4 bg-slate-200 rounded w-1/2"></div>
                <div className="h-8 bg-slate-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase">Hospital Doctors</span>
                <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center">
                  <Stethoscope className="w-5 h-5" />
                </div>
              </div>
              <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_doctors || 0}</span>
              <span className="text-xs text-slate-500 font-medium">Assigned Practitioners</span>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase">Departments</span>
                <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
              </div>
              <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_departments || 0}</span>
              <span className="text-xs text-slate-500 font-medium">Specialty Units</span>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase">Appointments</span>
                <div className="w-10 h-10 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center">
                  <ClipboardList className="w-5 h-5" />
                </div>
              </div>
              <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_appointments || 0}</span>
              <div className="flex gap-2 text-[10px] font-bold">
                <span className="text-emerald-600 flex items-center gap-0.5"><CheckCircle2 className="w-3 h-3"/>{stats?.confirmed_appointments || 0}</span>
                <span className="text-amber-600 flex items-center gap-0.5"><AlertCircle className="w-3 h-3"/>{stats?.pending_appointments || 0}</span>
                <span className="text-rose-600 flex items-center gap-0.5"><XCircle className="w-3 h-3"/>{stats?.cancelled_appointments || 0}</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase">Completed</span>
                <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              </div>
              <span className="text-3xl font-extrabold text-slate-900 block">{stats?.completed_appointments || 0}</span>
              <span className="text-xs text-slate-500 font-medium">Finished Consultations</span>
            </div>
          </div>
        )}

        {/* Action Shortcuts */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
          <Link
            to="/hospital-admin/doctors"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Stethoscope className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Manage Doctors</h3>
            <p className="text-xs text-slate-500">Register new doctors or modify credentials and consultation fees.</p>
            <span className="text-xs font-bold text-teal-600 flex items-center gap-1">
              Go to Doctors <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>

          <Link
            to="/hospital-admin/departments"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Building2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Hospital Departments</h3>
            <p className="text-xs text-slate-500">Add or manage specialized departments and status settings.</p>
            <span className="text-xs font-bold text-indigo-600 flex items-center gap-1">
              Go to Departments <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>

          <Link
            to="/hospital-admin/schedules"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Work Schedules</h3>
            <p className="text-xs text-slate-500">Configure weekly shift times and slot durations for doctors.</p>
            <span className="text-xs font-bold text-sky-600 flex items-center gap-1">
              Go to Schedules <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>

          <Link
            to="/hospital-admin/appointments"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <ClipboardList className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Booked Appointments</h3>
            <p className="text-xs text-slate-500">View patient appointments and update booking statuses.</p>
            <span className="text-xs font-bold text-amber-600 flex items-center gap-1">
              Go to Appointments <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>

          <Link
            to="/hospital-admin/profile"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Building className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Hospital Profile</h3>
            <p className="text-xs text-slate-500">Update address, contact numbers, and general facility details.</p>
            <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
              Edit Profile <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>
        </div>
      </main>
    </div>
  );
};
