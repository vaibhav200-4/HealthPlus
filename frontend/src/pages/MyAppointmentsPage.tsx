import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { Appointment } from '../types';
import { EmptyState } from '../components/EmptyState';
import { SkeletonTableRow } from '../components/SkeletonLoader';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  XCircle, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  FileText
} from 'lucide-react';

export const MyAppointmentsPage: React.FC = () => {
  const { showToast } = useToast();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [reschedulingApp, setReschedulingApp] = useState<Appointment | null>(null);

  // Reschedule form modal
  const [newDate, setNewDate] = useState('');
  const [newStartTime, setNewStartTime] = useState('10:00 AM');
  const [rescheduling, setRescheduling] = useState(false);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const res = await api.get('/appointments/my');
      setAppointments(res.data || []);
    } catch (err) {
      console.error('Failed to fetch appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      const res = await api.patch(`/appointments/${id}/cancel`);
      if (res.data.success) {
        showToast('Appointment cancelled successfully', 'info');
        fetchAppointments();
      }
    } catch (err) {
      showToast('Failed to cancel appointment', 'error');
    }
  };

  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reschedulingApp || !newDate) return;

    setRescheduling(true);
    try {
      const res = await api.patch(`/appointments/${reschedulingApp.id}/reschedule`, {
        date: newDate,
        start_time: newStartTime,
        end_time: '10:30 AM'
      });

      if (res.data.success) {
        showToast('Appointment rescheduled successfully!', 'success');
        setReschedulingApp(null);
        fetchAppointments();
      } else {
        showToast(res.data.message || 'Slot unavailable for rescheduling', 'error');
      }
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Rescheduling failed', 'error');
    } finally {
      setRescheduling(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-800 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <span className="text-xs font-bold text-tealmed-300 uppercase tracking-wider">Patient Portal</span>
        <h1 className="text-3xl font-extrabold tracking-tight">My Appointments</h1>
        <p className="text-xs sm:text-sm text-slate-300">View appointment history, cancel bookings, or request reschedule slots.</p>
      </div>

      {/* Appointments List / Table */}
      {loading ? (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/4 animate-pulse"></div>
          <table className="w-full">
            <tbody>
              <SkeletonTableRow />
              <SkeletonTableRow />
              <SkeletonTableRow />
            </tbody>
          </table>
        </div>
      ) : appointments.length === 0 ? (
        <EmptyState
          title="No Appointments Found"
          description="You have not booked any hospital appointments yet."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {appointments.map((app) => {
            const isConfirmed = app.status === 'confirmed';
            const isCancelled = app.status === 'cancelled';

            return (
              <div
                key={app.id}
                className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold ${
                        isConfirmed
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : isCancelled
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {app.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">ID: {app.id.substring(0, 8)}</span>
                  </div>

                  <h3 className="text-lg font-extrabold text-slate-900">{app.doctor_name}</h3>
                  <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-medical-600" />
                    {app.hospital_name}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-600 pt-2">
                    <span className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
                      <Calendar className="w-3.5 h-3.5 text-medical-600" />
                      {app.date}
                    </span>
                    <span className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
                      <Clock className="w-3.5 h-3.5 text-medical-600" />
                      {app.start_time} - {app.end_time}
                    </span>
                    {app.patient_name && (
                      <span className="text-slate-500">Patient: <strong>{app.patient_name}</strong></span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                {!isCancelled && (
                  <div className="flex items-center gap-2 w-full md:w-auto">
                    <button
                      onClick={() => {
                        setReschedulingApp(app);
                        setNewDate(app.date);
                      }}
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors flex items-center justify-center gap-1.5 flex-1 md:flex-initial"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Reschedule
                    </button>
                    <button
                      onClick={() => handleCancel(app.id)}
                      className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-xs rounded-xl transition-colors flex items-center justify-center gap-1.5 flex-1 md:flex-initial"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Reschedule Modal */}
      {reschedulingApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Reschedule Appointment</h3>
            <p className="text-xs text-slate-500">Select new date and time for {reschedulingApp.doctor_name}</p>

            <form onSubmit={handleRescheduleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Date</label>
                <input
                  type="date"
                  value={newDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Start Time</label>
                <select
                  value={newStartTime}
                  onChange={(e) => setNewStartTime(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                >
                  <option value="10:00 AM">10:00 AM</option>
                  <option value="10:30 AM">10:30 AM</option>
                  <option value="11:00 AM">11:00 AM</option>
                  <option value="03:00 PM">03:00 PM</option>
                  <option value="04:00 PM">04:00 PM</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setReschedulingApp(null)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rescheduling}
                  className="px-4 py-2 bg-medical-600 text-white rounded-xl text-xs font-semibold shadow"
                >
                  {rescheduling ? 'Saving...' : 'Confirm Reschedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
