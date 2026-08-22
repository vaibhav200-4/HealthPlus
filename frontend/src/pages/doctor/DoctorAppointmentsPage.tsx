import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { Appointment } from '../../types';
import { Calendar, Clock, Filter, CheckCircle2, XCircle, Search } from 'lucide-react';

export const DoctorAppointmentsPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const res = await api.get('/doctors/me/appointments');
      setAppointments(res.data || []);
    } catch (err) {
      console.error('Failed to fetch doctor appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (appId: string, newStatus: string) => {
    try {
      await api.patch(`/admin/appointments/${appId}/status`, { status: newStatus });
      fetchAppointments();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const filtered = appointments.filter((app) => {
    const matchesStatus = statusFilter === 'all' || app.status.toLowerCase() === statusFilter.toLowerCase();
    const matchesSearch = !searchTerm || 
      app.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.date.includes(searchTerm);
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-tealmed-900 to-medical-900 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Your Patient Appointments</h1>
        <p className="text-xs sm:text-sm text-slate-300">View and update status for consultations assigned directly to your doctor profile.</p>
      </div>

      {/* Filters & Search Bar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full sm:w-auto max-w-md">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search patient name or date (YYYY-MM-DD)..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-tealmed-500"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {['all', 'confirmed', 'pending', 'completed', 'cancelled'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold capitalize transition-all ${
                statusFilter === st
                  ? 'bg-tealmed-600 text-white shadow-md'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Appointments List / Table */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">
            Appointments <span className="text-xs text-slate-500 font-normal">({filtered.length} matching)</span>
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading appointments...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <Calendar className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No appointments found matching your filter criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3">Patient</th>
                  <th className="p-3">Contact info</th>
                  <th className="p-3">Date & Time</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filtered.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold text-slate-900">{app.patient_name}</td>
                    <td className="p-3 text-slate-600">{app.patient_email || app.patient_phone || 'N/A'}</td>
                    <td className="p-3">
                      <span className="font-semibold text-slate-800">{app.date}</span>
                      <span className="block text-[10px] text-tealmed-700 font-bold">{app.start_time} - {app.end_time}</span>
                    </td>
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
                      <div className="flex items-center justify-end gap-1.5">
                        {app.status !== 'completed' && (
                          <button
                            onClick={() => handleUpdateStatus(app.id, 'completed')}
                            className="px-3 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-xl text-[10px] font-bold transition-colors"
                          >
                            Mark Completed
                          </button>
                        )}
                        {app.status !== 'cancelled' && (
                          <button
                            onClick={() => handleUpdateStatus(app.id, 'cancelled')}
                            className="px-3 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-xl text-[10px] font-bold transition-colors"
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
