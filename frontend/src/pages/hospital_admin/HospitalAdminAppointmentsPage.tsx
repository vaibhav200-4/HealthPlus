import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { HospitalAdminSidebar } from '../../components/HospitalAdminSidebar';
import { Appointment } from '../../types';
import { ClipboardList, CheckCircle2, XCircle, Clock, Check, AlertCircle, RefreshCw } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

export const HospitalAdminAppointmentsPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const { showToast } = useToast();

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const res = await api.get('/hospital-admin/appointments');
      setAppointments(res.data || []);
    } catch (err) {
      console.error('Failed to fetch hospital appointments:', err);
      showToast('Failed to load appointments', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (appointmentId: string, newStatus: string) => {
    try {
      await api.patch(`/hospital-admin/appointments/${appointmentId}/status`, { status: newStatus });
      showToast(`Appointment status updated to ${newStatus}`, 'success');
      fetchAppointments();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update status', 'error');
    }
  };

  const filteredAppointments = appointments.filter((app) => {
    if (filterStatus === 'all') return true;
    return (app.status || '').toLowerCase() === filterStatus.toLowerCase();
  });

  const getStatusBadge = (status: string) => {
    switch ((status || '').toLowerCase()) {
      case 'confirmed':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Confirmed</span>;
      case 'pending':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Pending</span>;
      case 'cancelled':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">Cancelled</span>;
      case 'completed':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200">Completed</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">{status}</span>;
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <HospitalAdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Hospital Appointments</h1>
            <p className="text-xs text-slate-500">Monitor patient consultations and change booking statuses</p>
          </div>
          <button
            onClick={fetchAppointments}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 border-b border-slate-200 pb-2 text-xs font-semibold overflow-x-auto">
          {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3.5 py-1.5 rounded-xl capitalize transition-colors ${
                filterStatus === st
                  ? 'bg-slate-900 text-white font-bold'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-white rounded-2xl border border-slate-200 animate-pulse"></div>
            ))}
          </div>
        ) : filteredAppointments.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3 max-w-md mx-auto my-8">
            <ClipboardList className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-base font-bold text-slate-900">No Appointments Found</h3>
            <p className="text-xs text-slate-500">No bookings match the selected status filter for your hospital.</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Patient Name</th>
                  <th className="py-3.5 px-4">Doctor</th>
                  <th className="py-3.5 px-4">Date & Time</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Update Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {filteredAppointments.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900">{app.patient_name}</div>
                      <div className="text-[10px] text-slate-500">{app.patient_phone || app.patient_email || 'N/A'}</div>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-800">{app.doctor_name}</td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <div>{app.date}</div>
                      <div className="text-[10px] text-slate-500">{app.start_time} - {app.end_time}</div>
                    </td>
                    <td className="py-3.5 px-4">{getStatusBadge(app.status)}</td>
                    <td className="py-3.5 px-4 text-right">
                      <select
                        value={app.status}
                        onChange={(e) => handleStatusChange(app.id, e.target.value)}
                        className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                      >
                        <option value="pending">pending</option>
                        <option value="confirmed">confirmed</option>
                        <option value="completed">completed</option>
                        <option value="cancelled">cancelled</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};
