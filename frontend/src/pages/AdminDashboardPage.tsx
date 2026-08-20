import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { AdminSidebar } from '../components/AdminSidebar';
import { 
  Stethoscope, 
  Building2, 
  ClipboardList, 
  Users, 
  MessageSquare, 
  TrendingUp, 
  CheckCircle2, 
  Clock, 
  XCircle,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await api.get('/admin/stats');
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch admin stats:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <AdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-8 bg-slate-50/50 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-amber-600 uppercase tracking-wider">Hospital Administration</span>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">System Overview</h1>
          </div>
        </div>

        {/* Analytics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">Total Doctors</span>
              <div className="w-10 h-10 rounded-2xl bg-medical-50 text-medical-600 flex items-center justify-center">
                <Stethoscope className="w-5 h-5" />
              </div>
            </div>
            <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_doctors || 0}</span>
            <span className="text-xs text-slate-500 font-medium">Verified Medical Staff</span>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">Appointments</span>
              <div className="w-10 h-10 rounded-2xl bg-tealmed-50 text-tealmed-600 flex items-center justify-center">
                <ClipboardList className="w-5 h-5" />
              </div>
            </div>
            <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_appointments || 0}</span>
            <div className="flex gap-2 text-[10px] font-bold">
              <span className="text-emerald-600">{stats?.confirmed_appointments || 0} Confirmed</span>
              <span className="text-rose-600">{stats?.cancelled_appointments || 0} Cancelled</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">Hospital Nodes</span>
              <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Building2 className="w-5 h-5" />
              </div>
            </div>
            <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_hospitals || 0}</span>
            <span className="text-xs text-slate-500 font-medium">Network Health Centres</span>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">AI Chat Logged</span>
              <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <MessageSquare className="w-5 h-5" />
              </div>
            </div>
            <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_chat_messages || 0}</span>
            <span className="text-xs text-slate-500 font-medium">Web & Telegram Messages</span>
          </div>
        </div>

        {/* Action Shortcuts */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          <Link
            to="/admin/doctors"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-medical-50 text-medical-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Stethoscope className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Doctors Management</h3>
            <p className="text-xs text-slate-500">Add, edit, or remove doctors and update consultation fees.</p>
            <span className="text-xs font-bold text-medical-600 flex items-center gap-1">
              Manage Doctors <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>

          <Link
            to="/admin/schedules"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-tealmed-50 text-tealmed-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Schedule & Sheets Sync</h3>
            <p className="text-xs text-slate-500">Update doctor shift availability and sync with Google Sheets for n8n AI.</p>
            <span className="text-xs font-bold text-tealmed-600 flex items-center gap-1">
              Manage Schedules <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>

          <Link
            to="/admin/appointments"
            className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-all space-y-3 group"
          >
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <ClipboardList className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Appointments Monitor</h3>
            <p className="text-xs text-slate-500">View real-time booking logs and update appointment status.</p>
            <span className="text-xs font-bold text-indigo-600 flex items-center gap-1">
              View Appointments <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </Link>
        </div>
      </main>
    </div>
  );
};
