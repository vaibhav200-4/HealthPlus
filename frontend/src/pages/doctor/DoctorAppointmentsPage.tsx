import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { Appointment } from '../../types';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { StatusBadge } from '../../components/doctor/StatusBadge';
import { Calendar, Clock, Filter, CheckCircle2, XCircle, Search, Mail, Phone, Building } from 'lucide-react';

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
      (app.patient_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (app.date || '').includes(searchTerm) ||
      (app.hospital_name || '').toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const counts = {
    all: appointments.length,
    confirmed: appointments.filter(a => a.status === 'confirmed').length,
    pending: appointments.filter(a => a.status === 'pending').length,
    completed: appointments.filter(a => a.status === 'completed').length,
    cancelled: appointments.filter(a => a.status === 'cancelled').length,
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Reusable Doctor Portal Hero */}
      <DoctorPortalHero
        badgeText="Appointment Management"
        badgeIcon={<Calendar className="w-4 h-4 text-tealmed-700" />}
        title="Your Patient Appointments Queue"
        subtitle="Review schedules, manage consultation status, and view patient booking details."
        metadata={[
          { icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />, label: `${counts.confirmed} Confirmed` },
          { icon: <Clock className="w-3.5 h-3.5 text-amber-600" />, label: `${counts.pending} Pending` }
        ]}
      />

      {/* Filters & Search Toolbar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full max-w-md">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search patient name, date (YYYY-MM-DD), or hospital..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-tealmed-500 focus:bg-white transition-all"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          {(['all', 'confirmed', 'pending', 'completed', 'cancelled'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-all flex items-center gap-1.5 ${
                statusFilter === st
                  ? 'bg-tealmed-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200/80'
              }`}
            >
              <span>{st}</span>
              <span className={`px-1.5 py-0.2 rounded-md text-[10px] ${
                statusFilter === st ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'
              }`}>
                {counts[st]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Appointments Table Card */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-tealmed-600" />
            Appointments List <span className="text-xs text-slate-500 font-normal">({filtered.length} matching)</span>
          </h2>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-tealmed-500 border-t-transparent rounded-full animate-spin"></div>
            Loading assigned appointments...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 space-y-2">
            <Calendar className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No appointments match your search/filter criteria.</p>
            <button
              onClick={() => { setStatusFilter('all'); setSearchTerm(''); }}
              className="text-xs font-bold text-tealmed-700 hover:underline"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3.5 rounded-l-xl">Patient</th>
                  <th className="p-3.5">Contact Info</th>
                  <th className="p-3.5">Date & Time</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right rounded-r-xl">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filtered.map((app) => {
                  const initial = app.patient_name ? app.patient_name.charAt(0).toUpperCase() : 'P';
                  return (
                    <tr key={app.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="p-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-tealmed-50 text-tealmed-800 flex items-center justify-center font-extrabold text-xs border border-tealmed-200/80 flex-shrink-0">
                            {initial}
                          </div>
                          <div>
                            <span className="font-extrabold text-slate-900 block">{app.patient_name}</span>
                            <span className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                              <Building className="w-3 h-3 text-slate-400" /> {app.hospital_name || 'Hospital Node'}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="p-3.5">
                        <div className="space-y-0.5 text-slate-600">
                          {app.patient_email && (
                            <div className="flex items-center gap-1.5">
                              <Mail className="w-3 h-3 text-slate-400" />
                              <span className="truncate max-w-[180px]">{app.patient_email}</span>
                            </div>
                          )}
                          {app.patient_phone && (
                            <div className="flex items-center gap-1.5">
                              <Phone className="w-3 h-3 text-slate-400" />
                              <span>{app.patient_phone}</span>
                            </div>
                          )}
                          {!app.patient_email && !app.patient_phone && (
                            <span className="text-slate-400 italic">No contact info</span>
                          )}
                        </div>
                      </td>

                      <td className="p-3.5">
                        <span className="font-bold text-slate-800 block">{app.date}</span>
                        <span className="text-[10px] text-tealmed-700 font-semibold">{app.start_time} - {app.end_time}</span>
                      </td>

                      <td className="p-3.5">
                        <StatusBadge status={app.status} />
                      </td>

                      <td className="p-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {app.status !== 'completed' && (
                            <button
                              onClick={() => handleUpdateStatus(app.id, 'completed')}
                              className="px-2.5 py-1 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200/60 rounded-xl text-[10px] font-bold transition-colors"
                            >
                              Mark Completed
                            </button>
                          )}
                          {app.status !== 'cancelled' && (
                            <button
                              onClick={() => handleUpdateStatus(app.id, 'cancelled')}
                              className="px-2.5 py-1 bg-rose-50 text-rose-800 hover:bg-rose-100 border border-rose-200/60 rounded-xl text-[10px] font-bold transition-colors"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
