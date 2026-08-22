import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { Clock, Calendar, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

export const DoctorSchedulePage: React.FC = () => {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [doctorInfo, setDoctorInfo] = useState<any>(null);
  const [slots, setSlots] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchSchedule();
  }, []);

  useEffect(() => {
    if (doctorInfo?.doctor?.id) {
      fetchSlotsForDate(doctorInfo.doctor.id, selectedDate);
    }
  }, [selectedDate, doctorInfo]);

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const [docRes, schedRes] = await Promise.all([
        api.get('/doctors/me'),
        api.get('/doctors/me/schedule')
      ]);
      setDoctorInfo(docRes.data);
      setSchedules(schedRes.data || []);
    } catch (err) {
      console.error('Failed to fetch doctor schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSlotsForDate = async (docId: string, dateStr: string) => {
    try {
      const res = await api.get(`/schedules/doctor/${docId}?date=${dateStr}`);
      setSlots(res.data?.slots || []);
    } catch (err) {
      console.error('Failed to fetch slots:', err);
    }
  };

  const doc = doctorInfo?.doctor;

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-tealmed-900 to-medical-900 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Doctor Schedule & Availability</h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Powered directly by Supabase `schedules` table — single source of truth for patient & AI bookings.
        </p>
      </div>

      {/* Grid: Shift Configuration & Slot Checker */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Schedule Config Card */}
        <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-tealmed-600" />
            Configured Working Hours
          </h2>

          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-3 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Assigned Doctor ID</span>
              <span className="font-bold text-slate-900">{doc?.id || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Doctor Name</span>
              <span className="font-bold text-slate-900">{doc?.name || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Specialization</span>
              <span className="font-bold text-tealmed-700">{doc?.specialization || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 font-medium">Declared Availability</span>
              <span className="font-semibold text-slate-800">{doc?.availability || 'Standard Shift'}</span>
            </div>
          </div>

          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active DB Shift Records</h3>
          {schedules.length === 0 ? (
            <div className="p-4 bg-amber-50 rounded-xl text-xs text-amber-900 border border-amber-200">
              Using standard default shift slots (10:00 AM - 02:00 PM).
            </div>
          ) : (
            <div className="space-y-2">
              {schedules.map((sch) => (
                <div key={sch.id} className="p-3 bg-tealmed-50/60 rounded-xl border border-tealmed-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-slate-900">{sch.day_of_week}</span>
                    <span className="block text-[10px] text-slate-500">{sch.start_time} - {sch.end_time} ({sch.slot_duration_minutes} mins)</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    {sch.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Real-time Available Slots Checker */}
        <div className="lg:col-span-7 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-tealmed-600" />
              Live Available Slot Grid
            </h2>

            <div className="flex items-center gap-2">
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:ring-2 focus:ring-tealmed-500"
              />
            </div>
          </div>

          <p className="text-xs text-slate-500">
            Cross-referencing database schedule with confirmed bookings for <span className="font-bold text-slate-900">{selectedDate}</span>:
          </p>

          {slots.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">No slot data available for this date.</div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
              {slots.map((slot, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-2xl border text-center transition-all ${
                    slot.available
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                      : 'bg-rose-50/70 border-rose-200 text-rose-900 opacity-80'
                  }`}
                >
                  <span className="block font-extrabold text-xs">{slot.start_time} - {slot.end_time}</span>
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[9px] font-extrabold uppercase ${
                    slot.available ? 'bg-emerald-200/80 text-emerald-900' : 'bg-rose-200/80 text-rose-900'
                  }`}>
                    {slot.available ? 'Available' : 'Booked'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
