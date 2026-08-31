import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { Clock, Calendar, CheckCircle, AlertCircle, RefreshCw, UserCheck, ShieldCheck } from 'lucide-react';

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
      {/* Reusable Doctor Portal Hero */}
      <DoctorPortalHero
        badgeText="Shift & Availability Control"
        badgeIcon={<Clock className="w-4 h-4 text-tealmed-700" />}
        title="Doctor Shift Schedule & Live Slot Grid"
        subtitle="Single source of truth for patient web bookings, Google Sheets schedule sync, and AI Assistant availability queries."
        metadata={[
          { icon: <ShieldCheck className="w-3.5 h-3.5 text-tealmed-600" />, label: 'Supabase `schedules` DB Table Active' }
        ]}
      />

      {/* Grid: Shift Configuration & Slot Checker */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Schedule Config Card */}
        <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4">
          <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-tealmed-600" />
            Configured Shift Details
          </h2>

          <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-3 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Assigned Doctor ID</span>
              <span className="font-mono font-bold text-slate-900">{doc?.id || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Doctor Name</span>
              <span className="font-extrabold text-slate-900">{doc?.name || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Specialization</span>
              <span className="font-bold text-tealmed-800">{doc?.specialization || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 font-medium">Declared Availability</span>
              <span className="font-semibold text-slate-800">{doc?.availability || 'Standard Shift'}</span>
            </div>
          </div>

          <h3 className="text-xs font-extrabold text-slate-500 uppercase tracking-wider">Active DB Shift Records</h3>
          {schedules.length === 0 ? (
            <div className="p-4 bg-amber-50 rounded-2xl text-xs text-amber-900 border border-amber-200/80 font-medium">
              Using standard default shift slots (10:00 AM - 02:00 PM).
            </div>
          ) : (
            <div className="space-y-2">
              {schedules.map((sch) => (
                <div key={sch.id} className="p-3.5 bg-tealmed-50/50 rounded-2xl border border-tealmed-100/80 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-extrabold text-slate-900 block">{sch.day_of_week}</span>
                    <span className="text-[10px] text-slate-500 font-semibold">{sch.start_time} - {sch.end_time} ({sch.slot_duration_minutes} mins)</span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-900 border border-emerald-200">
                    {sch.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Real-time Available Slots Checker */}
        <div className="lg:col-span-7 bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-tealmed-600" />
              Live Available Slot Grid
            </h2>

            <div className="flex items-center gap-2">
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-bold text-slate-900 focus:ring-2 focus:ring-tealmed-500 outline-none"
              />
            </div>
          </div>

          <p className="text-xs text-slate-500 font-medium">
            Cross-referencing database schedule with confirmed bookings for <span className="font-bold text-slate-900">{selectedDate}</span>:
          </p>

          {slots.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">No slot data available for this date.</div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
              {slots.map((slot, i) => (
                <div
                  key={i}
                  className={`p-3.5 rounded-2xl border text-center transition-all ${
                    slot.available
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                      : 'bg-rose-50/70 border-rose-200 text-rose-900 opacity-80'
                  }`}
                >
                  <span className="block font-extrabold text-xs">{slot.start_time} - {slot.end_time}</span>
                  <span className={`inline-block mt-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-extrabold uppercase ${
                    slot.available ? 'bg-emerald-200/80 text-emerald-950' : 'bg-rose-200/80 text-rose-950'
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
