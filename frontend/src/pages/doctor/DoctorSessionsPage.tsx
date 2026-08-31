import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Session } from '../../types';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { StatusBadge } from '../../components/doctor/StatusBadge';
import { Stethoscope, Plus, CheckCircle, Clock, FileText, User, X } from 'lucide-react';

export const DoctorSessionsPage: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [appointmentId, setAppointmentId] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [doctorNotes, setDoctorNotes] = useState('');

  const fetchSessions = async () => {
    try {
      const res = await api.get('/sessions');
      setSessions(res.data || []);
    } catch (err) {
      console.error('Failed to fetch clinical sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/sessions', {
        appointment_id: appointmentId,
        symptoms,
        diagnosis,
        doctor_notes: doctorNotes
      });
      setShowModal(false);
      setAppointmentId('');
      setSymptoms('');
      setDiagnosis('');
      setDoctorNotes('');
      fetchSessions();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create session');
    }
  };

  const handleCompleteSession = async (id: string) => {
    try {
      await api.patch(`/sessions/${id}/complete`, { status: 'completed' });
      fetchSessions();
    } catch (err: any) {
      alert('Failed to complete session');
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Reusable Doctor Portal Hero */}
      <DoctorPortalHero
        badgeText="Clinical Consultation Sessions"
        badgeIcon={<Stethoscope className="w-4 h-4 text-tealmed-700" />}
        title="Patient Clinical Sessions"
        subtitle="Track live diagnostic consultations, record symptoms, and maintain confidential clinical notes."
        actions={
          <button
            onClick={() => setShowModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-2xl font-bold text-xs flex items-center gap-2 shadow-md shadow-emerald-600/20 transition-all"
          >
            <Plus className="w-4 h-4" /> Start New Session
          </button>
        }
      />

      {/* Sessions Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
          <div className="w-6 h-6 border-2 border-tealmed-500 border-t-transparent rounded-full animate-spin"></div>
          Loading clinical sessions...
        </div>
      ) : sessions.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center text-slate-400 border border-slate-200 space-y-3 shadow-2xs">
          <Stethoscope className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="text-sm font-semibold text-slate-700">No clinical sessions recorded yet.</p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-800 font-bold text-xs rounded-2xl border border-emerald-200 hover:bg-emerald-100 transition-colors"
          >
            <Plus className="w-4 h-4" /> Start First Session
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sessions.map((s) => (
            <div key={s.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4 hover:shadow-md transition-all">
              <div className="flex justify-between items-center">
                <span className="text-xs font-mono font-bold px-3 py-1 bg-slate-100 text-slate-800 rounded-xl border border-slate-200/60 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-tealmed-700" />
                  {s.patient_code || 'Patient'}
                </span>
                <StatusBadge status={s.status} />
              </div>

              <div>
                <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Diagnosis</p>
                <p className="text-slate-900 font-extrabold text-base">{s.diagnosis || 'Pending Diagnosis'}</p>
              </div>

              {s.symptoms && (
                <div>
                  <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Symptoms</p>
                  <p className="text-slate-700 text-xs font-medium mt-0.5">{s.symptoms}</p>
                </div>
              )}

              {s.doctor_notes && (
                <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 space-y-1">
                  <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Private Doctor Notes</p>
                  <p className="text-slate-800 text-xs italic font-medium">{s.doctor_notes}</p>
                </div>
              )}

              {s.status === 'in_progress' && (
                <button
                  onClick={() => handleCompleteSession(s.id)}
                  className="w-full mt-2 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200/80 py-2 rounded-2xl font-bold text-xs transition-colors"
                >
                  Mark Completed
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Start Session Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 space-y-5 shadow-2xl border border-slate-100">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-extrabold text-slate-900">Start Clinical Session</h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSession} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Appointment UUID *</label>
                <input
                  type="text"
                  required
                  value={appointmentId}
                  onChange={(e) => setAppointmentId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Paste appointment UUID"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Symptoms</label>
                <textarea
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={2}
                  placeholder="Fever, cough, joint pain..."
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Diagnosis</label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Clinical diagnosis"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Private Doctor Notes (Hidden from Patient)</label>
                <textarea
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={3}
                  placeholder="Confidential observations..."
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2.5 rounded-2xl text-slate-600 font-bold text-xs hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-2xl shadow-md shadow-emerald-600/20 transition-all"
                >
                  Save Session
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
