import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { Appointment, Doctor } from '../../types';
import { 
  Calendar, 
  Clock, 
  Users, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  Stethoscope, 
  ArrowRight,
  UserCheck,
  TrendingUp
} from 'lucide-react';

export const DoctorDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchDoctorDashboardData();
  }, []);

  const fetchDoctorDashboardData = async () => {
    try {
      const [statsRes, appRes] = await Promise.all([
        api.get('/doctors/me/stats'),
        api.get('/doctors/me/appointments')
      ]);
      setStats(statsRes.data);
      setAppointments(appRes.data || []);
    } catch (err) {
      console.error('Failed to load doctor dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (appId: string, newStatus: string) => {
    try {
      await api.patch(`/admin/appointments/${appId}/status`, { status: newStatus });
      fetchDoctorDashboardData();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const doctor: Doctor | undefined = stats?.doctor;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-tealmed-900 via-tealmed-800 to-medical-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-semibold text-tealmed-300 border border-white/20">
            <Stethoscope className="w-4 h-4 text-tealmed-300" /> Attending Specialist Dashboard
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome, {doctor?.name || user?.name || 'Doctor'}!
          </h1>
          <p className="text-xs sm:text-sm text-slate-300">
            {doctor?.specialization ? `${doctor.specialization} Specialist` : 'Medical Practitioner'} • {doctor?.availability || 'Schedule Active'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/doctor/appointments"
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-tealmed-500 hover:bg-tealmed-600 text-white font-bold text-xs shadow-lg shadow-tealmed-500/20 transition-all"
          >
            <Calendar className="w-4 h-4" /> View All Appointments
          </Link>
          <Link
            to="/doctor/schedule"
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-white text-slate-900 font-bold text-xs hover:bg-slate-100 transition-all shadow-sm"
          >
            <Clock className="w-4 h-4 text-tealmed-600" /> Manage Shifts
          </Link>
        </div>
      </div>

      {/* Doctor Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Today's Appointments</span>
            <div className="w-10 h-10 rounded-2xl bg-tealmed-50 text-tealmed-600 flex items-center justify-center font-bold">
              <Calendar className="w-5 h-5" />
            </div>
          </div>
          <span className="text-3xl font-extrabold text-slate-900 block">{stats?.today_appointments_count || 0}</span>
          <span className="text-xs text-slate-500 font-medium">Scheduled for today</span>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Upcoming Consults</span>
            <div className="w-10 h-10 rounded-2xl bg-medical-50 text-medical-600 flex items-center justify-center font-bold">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <span className="text-3xl font-extrabold text-slate-900 block">{stats?.upcoming_appointments_count || 0}</span>
          <span className="text-xs text-slate-500 font-medium">Active confirmed / pending</span>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Completed</span>
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <span className="text-3xl font-extrabold text-slate-900 block">{stats?.completed_appointments_count || 0}</span>
          <span className="text-xs text-slate-500 font-medium">Successfully completed</span>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Total Patients</span>
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <span className="text-3xl font-extrabold text-slate-900 block">{stats?.total_patients_count || 0}</span>
          <span className="text-xs text-slate-500 font-medium">Unique patients seen</span>
        </div>
      </div>

      {/* Appointments Timeline Table */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-tealmed-600" />
            Appointments Assigned to You ({appointments.length})
          </h2>
          <Link to="/doctor/appointments" className="text-xs font-bold text-tealmed-600 hover:underline flex items-center gap-1">
            View All <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading doctor appointments...</div>
        ) : appointments.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <Calendar className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No appointments assigned to your profile yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3">Patient Name</th>
                  <th className="p-3">Date & Time</th>
                  <th className="p-3">Hospital</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {appointments.slice(0, 5).map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold text-slate-900">
                      {app.patient_name}
                      <span className="block text-[10px] text-slate-500 font-normal">{app.patient_email || app.patient_phone || 'No contact info'}</span>
                    </td>
                    <td className="p-3">
                      <span className="font-semibold text-slate-800">{app.date}</span>
                      <span className="block text-[10px] text-tealmed-700 font-bold">{app.start_time} - {app.end_time}</span>
                    </td>
                    <td className="p-3 text-slate-700">{app.hospital_name}</td>
                    <td className="p-3">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        app.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                        app.status === 'completed' ? 'bg-indigo-100 text-indigo-800' :
                        app.status === 'cancelled' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {app.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {app.status !== 'completed' && (
                          <button
                            onClick={() => handleUpdateStatus(app.id, 'completed')}
                            className="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-[10px] font-bold transition-colors"
                          >
                            Mark Completed
                          </button>
                        )}
                        {app.status !== 'cancelled' && (
                          <button
                            onClick={() => handleUpdateStatus(app.id, 'cancelled')}
                            className="px-2.5 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-[10px] font-bold transition-colors"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
