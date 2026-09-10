import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { HospitalAdminSidebar } from '../../components/HospitalAdminSidebar';
import { Doctor } from '../../types';
import { Clock, Plus, Trash2, Calendar, CheckCircle2 } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

export const HospitalAdminSchedulesPage: React.FC = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('');
  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  const { showToast } = useToast();

  const [formData, setFormData] = useState({
    day_of_week: 'Monday',
    start_time: '09:00 AM',
    end_time: '05:00 PM',
    slot_duration_minutes: 30
  });

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    if (selectedDoctorId) {
      fetchDoctorSchedules(selectedDoctorId);
    }
  }, [selectedDoctorId]);

  const fetchDoctors = async () => {
    try {
      const res = await api.get('/hospital-admin/doctors');
      const docs = res.data || [];
      setDoctors(docs);
      if (docs.length > 0) {
        setSelectedDoctorId(docs[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch doctors:', err);
      showToast('Failed to load doctor list', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchDoctorSchedules = async (doctorId: string) => {
    try {
      const res = await api.get(`/schedules/doctor/${doctorId}?date=${new Date().toISOString().split('T')[0]}`);
      // Also fetch raw schedule rules if available or general schedules endpoint
      const allSchedulesRes = await api.get('/schedules');
      const docSchedules = (allSchedulesRes.data || []).filter((s: any) => s.doctor_id === doctorId);
      setSchedules(docSchedules);
    } catch (err) {
      console.error('Failed to fetch doctor schedule slots:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctorId) {
      showToast('Please select a doctor', 'error');
      return;
    }
    try {
      await api.post('/hospital-admin/schedules', null, {
        params: {
          doctor_id: selectedDoctorId,
          day_of_week: formData.day_of_week,
          start_time: formData.start_time,
          end_time: formData.end_time,
          slot_duration_minutes: formData.slot_duration_minutes
        }
      });
      showToast('Schedule slot created successfully', 'success');
      setIsModalOpen(false);
      fetchDoctorSchedules(selectedDoctorId);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to save schedule slot', 'error');
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!window.confirm('Delete this work schedule slot?')) return;
    try {
      await api.delete(`/hospital-admin/schedules/${scheduleId}`);
      showToast('Schedule slot removed', 'success');
      fetchDoctorSchedules(selectedDoctorId);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete schedule slot', 'error');
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <HospitalAdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Doctor Work Schedules</h1>
            <p className="text-xs text-slate-500">Configure weekly shift times and slot durations for hospital practitioners</p>
          </div>
          {doctors.length > 0 && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Add Shift Schedule</span>
            </button>
          )}
        </div>

        {loading ? (
          <div className="h-48 bg-white rounded-2xl border border-slate-200 animate-pulse"></div>
        ) : doctors.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4 max-w-md mx-auto my-8">
            <div className="w-16 h-16 bg-sky-50 text-sky-600 rounded-full flex items-center justify-center mx-auto">
              <Clock className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-900">No Doctors Available</h3>
              <p className="text-xs text-slate-500">Add doctors to your hospital before configuring weekly shift schedules.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Doctor Selector */}
            <div className="bg-white p-4 rounded-2xl border border-slate-200 flex items-center gap-4 max-w-md">
              <label className="text-xs font-bold text-slate-700 whitespace-nowrap">Select Doctor:</label>
              <select
                value={selectedDoctorId}
                onChange={(e) => setSelectedDoctorId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500/20"
              >
                {doctors.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.name} ({doc.specialization})
                  </option>
                ))}
              </select>
            </div>

            {/* Schedule List */}
            {schedules.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-3 max-w-md">
                <Calendar className="w-10 h-10 text-slate-300 mx-auto" />
                <p className="text-xs text-slate-500">No active work shift rules for this doctor.</p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-3.5 py-1.5 bg-sky-600 text-white rounded-xl text-xs font-semibold hover:bg-sky-700"
                >
                  Create Shift Slot
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      <th className="py-3.5 px-4">Day of Week</th>
                      <th className="py-3.5 px-4">Shift Hours</th>
                      <th className="py-3.5 px-4">Slot Duration</th>
                      <th className="py-3.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {schedules.map((sch) => (
                      <tr key={sch.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-slate-900">{sch.day_of_week}</td>
                        <td className="py-3.5 px-4 text-slate-700 font-semibold">{sch.start_time} - {sch.end_time}</td>
                        <td className="py-3.5 px-4 text-slate-600">{sch.slot_duration_minutes || 30} minutes</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => handleDeleteSchedule(sch.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-6 shadow-xl">
              <h2 className="text-lg font-bold text-slate-900">Add Shift Schedule Slot</h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Day of Week</label>
                  <select
                    value={formData.day_of_week}
                    onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                  >
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
                      <option key={day} value={day}>{day}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Start Time</label>
                    <input
                      type="text"
                      required
                      placeholder="09:00 AM"
                      value={formData.start_time}
                      onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">End Time</label>
                    <input
                      type="text"
                      required
                      placeholder="05:00 PM"
                      value={formData.end_time}
                      onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Slot Duration (Minutes)</label>
                  <input
                    type="number"
                    required
                    value={formData.slot_duration_minutes}
                    onChange={(e) => setFormData({ ...formData, slot_duration_minutes: parseInt(e.target.value) || 30 })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-semibold hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold hover:bg-sky-700"
                  >
                    Save Slot
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
