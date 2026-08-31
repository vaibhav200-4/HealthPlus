import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Prescription, PrescriptionItem } from '../../types';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { Pill, Plus, User, FileText, Calendar, X } from 'lucide-react';

export const DoctorPrescriptionsPage: React.FC = () => {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [patientId, setPatientId] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<PrescriptionItem[]>([
    { medicine_name: '', dosage: '', frequency: '', duration: '', instructions: '' }
  ]);

  const fetchPrescriptions = async () => {
    try {
      const res = await api.get('/prescriptions');
      setPrescriptions(res.data || []);
    } catch (err) {
      console.error('Failed to fetch prescriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, []);

  const handleAddItem = () => {
    setItems([...items, { medicine_name: '', dosage: '', frequency: '', duration: '', instructions: '' }]);
  };

  const handleItemChange = (index: number, field: keyof PrescriptionItem, val: string) => {
    const next = [...items];
    next[index][field] = val;
    setItems(next);
  };

  const handleCreatePrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/prescriptions', {
        patient_id: patientId,
        notes,
        items: items.filter(i => i.medicine_name.trim() !== '')
      });
      setShowModal(false);
      setPatientId('');
      setNotes('');
      setItems([{ medicine_name: '', dosage: '', frequency: '', duration: '', instructions: '' }]);
      fetchPrescriptions();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create prescription');
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Reusable Doctor Portal Hero */}
      <DoctorPortalHero
        badgeText="Rx Prescriptions"
        badgeIcon={<Pill className="w-4 h-4 text-tealmed-700" />}
        title="Digital Patient Prescriptions"
        subtitle="Issue e-prescriptions, manage medication dosages, and record clinical advice."
        actions={
          <button
            onClick={() => setShowModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-2xl font-bold text-xs flex items-center gap-2 shadow-md shadow-emerald-600/20 transition-all"
          >
            <Plus className="w-4 h-4" /> Issue Prescription
          </button>
        }
      />

      {/* Prescription Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
          <div className="w-6 h-6 border-2 border-tealmed-500 border-t-transparent rounded-full animate-spin"></div>
          Loading prescriptions...
        </div>
      ) : prescriptions.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center text-slate-400 border border-slate-200 space-y-3 shadow-2xs">
          <Pill className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="text-sm font-semibold text-slate-700">No prescriptions issued yet.</p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-800 font-bold text-xs rounded-2xl border border-emerald-200 hover:bg-emerald-100 transition-colors"
          >
            <Plus className="w-4 h-4" /> Issue First Prescription
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {prescriptions.map((p) => (
            <div key={p.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4 hover:shadow-md transition-all">
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <span className="text-xs font-mono font-bold px-3 py-1 bg-slate-100 text-slate-800 rounded-xl flex items-center gap-1.5 border border-slate-200/60">
                  <User className="w-3.5 h-3.5 text-tealmed-700" />
                  {p.patient_code || 'Patient'}
                </span>
                <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recent'}
                </span>
              </div>
              
              <div className="space-y-3">
                <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Prescribed Medications ({p.items?.length || 0})</p>
                <div className="divide-y divide-slate-100">
                  {p.items?.map((item, idx) => (
                    <div key={idx} className="py-2.5 flex justify-between items-start text-xs">
                      <div>
                        <p className="font-extrabold text-slate-900 text-sm">{item.medicine_name}</p>
                        <p className="text-slate-500 mt-0.5 font-medium">{item.dosage} • {item.frequency} • {item.duration}</p>
                      </div>
                      {item.instructions && (
                        <span className="text-[10px] font-bold bg-tealmed-50 text-tealmed-800 px-2.5 py-1 rounded-lg border border-tealmed-100">
                          {item.instructions}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {p.notes && (
                <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 space-y-1">
                  <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Doctor Advice / Notes</p>
                  <p className="text-slate-800 text-xs font-medium">{p.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* New Prescription Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-5 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-extrabold text-slate-900">New Digital Prescription</h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePrescription} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Patient Identifier (UUID or Profile ID) *</label>
                <input
                  type="text"
                  required
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Paste Patient Profile UUID"
                />
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Medications List</label>
                  <button
                    type="button"
                    onClick={handleAddItem}
                    className="text-xs font-bold text-tealmed-700 hover:underline"
                  >
                    + Add Medication
                  </button>
                </div>

                {items.map((item, idx) => (
                  <div key={idx} className="p-3.5 border border-slate-200 rounded-2xl bg-slate-50/60 space-y-2">
                    <input
                      type="text"
                      placeholder="Medicine Name (e.g. Paracetamol 500mg)"
                      required
                      value={item.medicine_name}
                      onChange={(e) => handleItemChange(idx, 'medicine_name', e.target.value)}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-medium bg-white"
                    />
                    <div className="grid grid-cols-3 gap-2">
                      <input
                        type="text"
                        placeholder="Dosage (1 tab)"
                        value={item.dosage}
                        onChange={(e) => handleItemChange(idx, 'dosage', e.target.value)}
                        className="px-2.5 py-1.5 border border-slate-200 rounded-xl text-xs font-medium bg-white"
                      />
                      <input
                        type="text"
                        placeholder="Frequency (Twice daily)"
                        value={item.frequency}
                        onChange={(e) => handleItemChange(idx, 'frequency', e.target.value)}
                        className="px-2.5 py-1.5 border border-slate-200 rounded-xl text-xs font-medium bg-white"
                      />
                      <input
                        type="text"
                        placeholder="Duration (5 days)"
                        value={item.duration}
                        onChange={(e) => handleItemChange(idx, 'duration', e.target.value)}
                        className="px-2.5 py-1.5 border border-slate-200 rounded-xl text-xs font-medium bg-white"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Additional Clinical Advice / Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={2}
                  placeholder="Take after meals, stay hydrated..."
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
                  Issue Prescription
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
