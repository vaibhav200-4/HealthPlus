import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Prescription, PrescriptionItem } from '../../types';
import { Pill, Plus, User } from 'lucide-react';

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
      setPrescriptions(res.data);
    } catch (err) {
      console.error(err);
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
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Pill className="w-6 h-6 text-emerald-600" />
            Patient Prescriptions
          </h1>
          <p className="text-slate-500 text-sm">Issue and manage digital prescriptions</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition"
        >
          <Plus className="w-4 h-4" /> Create Prescription
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading prescriptions...</div>
      ) : prescriptions.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center text-slate-400 border border-slate-200">
          No prescriptions issued yet.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {prescriptions.map((p) => (
            <div key={p.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex justify-between items-center border-b pb-3">
                <span className="text-xs font-mono font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" />
                  {p.patient_code || 'Patient'}
                </span>
                <span className="text-xs text-slate-400">
                  {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                </span>
              </div>
              
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-400 uppercase">Prescribed Medicines</p>
                <div className="divide-y divide-slate-100">
                  {p.items.map((item, idx) => (
                    <div key={idx} className="py-2 flex justify-between items-start text-sm">
                      <div>
                        <p className="font-semibold text-slate-800">{item.medicine_name}</p>
                        <p className="text-xs text-slate-500">{item.dosage} • {item.frequency} • {item.duration}</p>
                      </div>
                      {item.instructions && (
                        <span className="text-xs italic bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded">
                          {item.instructions}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {p.notes && (
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Doctor Notes</p>
                  <p className="text-slate-700 text-xs">{p.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-800">New Digital Prescription</h3>
            <form onSubmit={handleCreatePrescription} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Patient Identifier (UUID or Profile ID)</label>
                <input
                  type="text"
                  required
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Patient ID"
                />
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-slate-600 uppercase">Medications</label>
                  <button
                    type="button"
                    onClick={handleAddItem}
                    className="text-xs font-medium text-emerald-600 hover:text-emerald-700"
                  >
                    + Add Medication
                  </button>
                </div>

                {items.map((item, idx) => (
                  <div key={idx} className="p-3 border rounded-lg bg-slate-50 space-y-2">
                    <input
                      type="text"
                      placeholder="Medicine Name (e.g. Paracetamol 500mg)"
                      required
                      value={item.medicine_name}
                      onChange={(e) => handleItemChange(idx, 'medicine_name', e.target.value)}
                      className="w-full border rounded p-1.5 text-xs bg-white"
                    />
                    <div className="grid grid-cols-3 gap-2">
                      <input
                        type="text"
                        placeholder="Dosage (1 tab)"
                        value={item.dosage}
                        onChange={(e) => handleItemChange(idx, 'dosage', e.target.value)}
                        className="border rounded p-1.5 text-xs bg-white"
                      />
                      <input
                        type="text"
                        placeholder="Frequency (Twice daily)"
                        value={item.frequency}
                        onChange={(e) => handleItemChange(idx, 'frequency', e.target.value)}
                        className="border rounded p-1.5 text-xs bg-white"
                      />
                      <input
                        type="text"
                        placeholder="Duration (5 days)"
                        value={item.duration}
                        onChange={(e) => handleItemChange(idx, 'duration', e.target.value)}
                        className="border rounded p-1.5 text-xs bg-white"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Additional Advice / Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={2}
                  placeholder="Take after meals..."
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
