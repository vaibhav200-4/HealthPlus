import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { MedicalRecord } from '../../types';
import { FileText, Plus, ExternalLink, ShieldCheck } from 'lucide-react';

export const DoctorMedicalRecordsPage: React.FC = () => {
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [patientId, setPatientId] = useState('');
  const [recordType, setRecordType] = useState('diagnosis');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [fileUrl, setFileUrl] = useState('');

  const fetchRecords = async () => {
    try {
      const res = await api.get('/medical-records');
      setRecords(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const handleCreateRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/medical-records', {
        patient_id: patientId,
        record_type: recordType,
        title,
        description,
        file_url: fileUrl
      });
      setShowModal(false);
      setPatientId('');
      setTitle('');
      setDescription('');
      setFileUrl('');
      fetchRecords();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to upload medical record');
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FileText className="w-6 h-6 text-emerald-600" />
            Medical Records & Reports
          </h1>
          <p className="text-slate-500 text-sm">Secure storage and signed URL retrieval for patient reports</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition"
        >
          <Plus className="w-4 h-4" /> Add Medical Record
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading medical records...</div>
      ) : records.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center text-slate-400 border border-slate-200">
          No medical records uploaded yet.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {records.map((r) => (
            <div key={r.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold px-2 py-1 bg-emerald-50 text-emerald-700 rounded uppercase tracking-wider">
                  {r.record_type}
                </span>
                <span className="text-xs font-mono text-slate-500">{r.patient_code || 'Patient'}</span>
              </div>
              <div>
                <h4 className="font-bold text-slate-800">{r.title}</h4>
                {r.description && <p className="text-slate-600 text-xs mt-1">{r.description}</p>}
              </div>
              {r.signed_file_url && (
                <div className="pt-2 border-t flex justify-between items-center text-xs">
                  <span className="text-slate-400 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Signed URL Access
                  </span>
                  <a
                    href={r.signed_file_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-600 hover:text-emerald-700 font-semibold flex items-center gap-1"
                  >
                    View File <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-slate-800">Add Patient Medical Record</h3>
            <form onSubmit={handleCreateRecord} className="space-y-3">
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
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Record Type</label>
                <select
                  value={recordType}
                  onChange={(e) => setRecordType(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                >
                  <option value="diagnosis">Diagnosis Summary</option>
                  <option value="lab_report">Lab Report</option>
                  <option value="xray">X-Ray</option>
                  <option value="mri">MRI Scan</option>
                  <option value="blood_test">Blood Test</option>
                  <option value="discharge_summary">Discharge Summary</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Chest X-Ray AP View"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  rows={2}
                  placeholder="Notes or clinical findings..."
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Storage Path / File URL</label>
                <input
                  type="text"
                  value={fileUrl}
                  onChange={(e) => setFileUrl(e.target.value)}
                  className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="medical-records/patient_x/xray.pdf"
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
                  Upload Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
