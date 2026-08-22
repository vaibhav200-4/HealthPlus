import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Session } from '../../types';
import { Stethoscope, Plus, CheckCircle, Clock } from 'lucide-react';

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
      setSessions(res.data);
    } catch (err) {
      console.error(err);
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
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-emerald-600" />
            Clinical Sessions
          </h1>
          <p className="text-slate-500 text-sm">Manage ongoing and completed patient consultations</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition"
        >
          <Plus className="w-4 h-4" /> Start New Session
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading sessions...</div>
      ) : sessions.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center text-slate-400 border border-slate-200">
          No clinical sessions recorded yet.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sessions.map((s) => (
            <div key={s.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow transition space-y-3">
              <div className="flex justify-between items-start">
                <span className="text-xs font-mono font-semibold px-2 py-1 rounded bg-slate-100 text-slate-700">
                  {s.patient_code || 'Patient'}
                </span>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1 ${
                  s.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                }`}>
                  {s.status === 'completed' ? <CheckCircle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                  {s.status}
                </span>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Diagnosis</p>
                <p className="text-slate-800 font-medium">{s.diagnosis || 'Pending'}</p>
              </div>
              {s.symptoms && (
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase">Symptoms</p>
                  <p className="text-slate-600 text-sm">{s.symptoms}</p>
                </div>
              )}
              {s.doctor_notes && (
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Doctor Notes (Private)</p>
                  <p className="text-slate-700 text-xs italic">{s.doctor_notes}</p>
                </div>
              )}
              {s.status === 'in_progress' && (
                <button
                  onClick={() => handleCompleteSession(s.id)}
                  className="w-full mt-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 py-1.5 rounded-lg font-medium text-sm transition"
                >
                  Mark Completed
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-slate-800">Start Clinical Session</h3>
            <form onSubmit={handleCreateSession} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Appointment ID</label>
                <input
                  type="text"
                  required
                  value={appointmentId}
                  onChange={(e) => setAppointmentId(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Paste appointment UUID"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Symptoms</label>
                <textarea
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={2}
                  placeholder="Fever, cough, fatigue..."
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Diagnosis</label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Clinical diagnosis"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Private Doctor Notes (Hidden from Patient)</label>
                <textarea
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={3}
                  placeholder="Confidential observations..."
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
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
