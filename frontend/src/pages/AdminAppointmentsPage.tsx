import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { AdminSidebar } from '../components/AdminSidebar';
import { Appointment } from '../types';
import { ClipboardList, CheckCircle2, XCircle, Clock } from 'lucide-react';

export const AdminAppointmentsPage: React.FC = () => {
  const { showToast } = useToast();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const res = await api.get('/admin/appointments');
      setAppointments(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      await api.patch(`/admin/appointments/${id}/status`, { status: newStatus });
      showToast(`Appointment status changed to ${newStatus}`, 'success');
      fetchAppointments();
    } catch (err) {
      showToast('Failed to update status', 'error');
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <AdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">Hospital Appointments Log</h1>
          <p className="text-xs text-slate-500">Monitor all user bookings across doctors and hospitals.</p>
        </div>

        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-bold">
              <tr>
                <th className="p-4">App ID</th>
                <th className="p-4">Patient</th>
                <th className="p-4">Doctor & Hospital</th>
                <th className="p-4">Date & Time</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Update Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {appointments.map((app) => (
                <tr key={app.id} className="hover:bg-slate-50">
                  <td className="p-4 font-mono text-slate-500">{app.id.substring(0, 8)}</td>
                  <td className="p-4">
                    <span className="font-bold block text-slate-900">{app.patient_name}</span>
                    <span className="text-[10px] text-slate-400">{app.patient_phone || app.patient_email}</span>
                  </td>
                  <td className="p-4">
                    <span className="font-bold text-slate-900 block">{app.doctor_name}</span>
                    <span className="text-[10px] text-slate-500">{app.hospital_name}</span>
                  </td>
                  <td className="p-4">
                    <span className="font-semibold block">{app.date}</span>
                    <span className="text-[10px] text-slate-500">{app.start_time} - {app.end_time}</span>
                  </td>
                  <td className="p-4">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        app.status === 'confirmed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : app.status === 'cancelled'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {app.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-4 text-right space-x-1">
                    <button
                      onClick={() => handleStatusChange(app.id, 'confirmed')}
                      className="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-[10px] font-bold"
                    >
                      Confirm
                    </button>
                    <button
                      onClick={() => handleStatusChange(app.id, 'completed')}
                      className="px-2 py-1 bg-sky-50 text-sky-700 hover:bg-sky-100 rounded text-[10px] font-bold"
                    >
                      Complete
                    </button>
                    <button
                      onClick={() => handleStatusChange(app.id, 'cancelled')}
                      className="px-2 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded text-[10px] font-bold"
                    >
                      Cancel
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
};
