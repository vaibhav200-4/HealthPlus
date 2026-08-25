import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MedicalRecord, Appointment } from '../../types';
import {
  ArrowLeft,
  User as UserIcon,
  Mail,
  Phone,
  Calendar,
  FileText,
  Plus,
  ExternalLink,
  ShieldCheck,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileUp,
  X
} from 'lucide-react';

export const DoctorPatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'overview' | 'records'>('overview');
  const [patientProfile, setPatientProfile] = useState<any>(null);
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal State
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [title, setTitle] = useState<string>('');
  const [recordType, setRecordType] = useState<string>('diagnosis');
  const [description, setDescription] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string>('');

  useEffect(() => {
    if (patientId) {
      fetchPatientData();
    }
  }, [patientId]);

  const fetchPatientData = async () => {
    setLoading(true);
    try {
      const [profileRes, recordsRes] = await Promise.all([
        api.get(`/doctors/patients/${patientId}/profile`).catch(() =>
          api.get(`/doctors/me/patients/${patientId}`).catch(() => null)
        ),
        api.get(`/medical-records/patient/${patientId}`).catch(() => ({ data: [] }))
      ]);

      if (profileRes && profileRes.data) {
        setPatientProfile(profileRes.data);
      }
      setRecords(recordsRes.data || []);
    } catch (err) {
      console.error('Failed to load patient detail data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a file to upload (PDF, JPG, PNG, WEBP, max 15MB)');
      return;
    }

    setUploading(true);
    setUploadError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('patient_identifier', patientId || '');
      formData.append('uploaded_by', 'doctor');
      formData.append('title', title);
      formData.append('record_type', recordType);
      if (description) formData.append('description', description);

      await api.post('/medical-records/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setShowUploadModal(false);
      setTitle('');
      setDescription('');
      setSelectedFile(null);
      setRecordType('diagnosis');
      
      // Refresh medical records list
      const recordsRes = await api.get(`/medical-records/patient/${patientId}`);
      setRecords(recordsRes.data || []);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload medical record');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <div className="animate-spin w-8 h-8 border-4 border-tealmed-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        Loading patient details...
      </div>
    );
  }

  const pName = patientProfile?.name || 'Patient Profile';
  const pCode = patientProfile?.patient_code || 'PT-REF';
  const pEmail = patientProfile?.email || 'No email provided';
  const pPhone = patientProfile?.phone || 'No phone provided';
  const appointments: Appointment[] = patientProfile?.appointments || [];

  return (
    <div className="space-y-8 pb-16">
      {/* Back Button & Header */}
      <div>
        <button
          onClick={() => navigate('/doctor/patients')}
          className="inline-flex items-center gap-2 text-xs font-bold text-tealmed-700 hover:text-tealmed-900 bg-tealmed-50 px-3.5 py-2 rounded-xl border border-tealmed-200 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Patients List
        </button>

        <div className="bg-gradient-to-r from-tealmed-900 via-tealmed-800 to-medical-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-white/10 text-white flex items-center justify-center font-extrabold text-2xl border border-white/20">
              {pName.charAt(0).toUpperCase()}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">{pName}</h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-tealmed-500/30 text-tealmed-200 border border-tealmed-400/30">
                  {pCode}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                <span className="flex items-center gap-1.5"><Mail className="w-3.5 h-3.5" /> {pEmail}</span>
                <span className="flex items-center gap-1.5"><Phone className="w-3.5 h-3.5" /> {pPhone}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setActiveTab('records');
                setShowUploadModal(true);
              }}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2.5 rounded-2xl font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all"
            >
              <Plus className="w-4 h-4" /> Add Medical Record
            </button>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-slate-200 flex items-center gap-8">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-4 text-sm font-extrabold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'border-tealmed-600 text-tealmed-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <UserIcon className="w-4 h-4" />
          Overview & Appointments ({appointments.length})
        </button>
        <button
          onClick={() => setActiveTab('records')}
          className={`pb-4 text-sm font-extrabold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'records'
              ? 'border-tealmed-600 text-tealmed-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          Medical Records ({records.length})
        </button>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Patient Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-slate-400 text-xs font-semibold">Gender</span>
              <p className="text-sm font-bold text-slate-800">{patientProfile?.gender || 'Not specified'}</p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-slate-400 text-xs font-semibold">Blood Group</span>
              <p className="text-sm font-bold text-rose-600">{patientProfile?.blood_group || 'Not specified'}</p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-slate-400 text-xs font-semibold">Date of Birth</span>
              <p className="text-sm font-bold text-slate-800">{patientProfile?.date_of_birth || 'Not recorded'}</p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-slate-400 text-xs font-semibold">Total Consultations</span>
              <p className="text-sm font-bold text-tealmed-700">{patientProfile?.consultation_count || appointments.length}</p>
            </div>
          </div>

          {/* Address & Emergency Contact */}
          {(patientProfile?.address || patientProfile?.emergency_contact) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {patientProfile?.address && (
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                  <span className="text-slate-400 text-xs font-semibold">Address</span>
                  <p className="text-xs font-medium text-slate-700">{patientProfile.address}</p>
                </div>
              )}
              {patientProfile?.emergency_contact && (
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                  <span className="text-slate-400 text-xs font-semibold">Emergency Contact</span>
                  <p className="text-xs font-medium text-slate-700">{patientProfile.emergency_contact}</p>
                </div>
              )}
            </div>
          )}

          {/* Appointment History */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-tealmed-600" /> Appointment History
            </h3>

            {appointments.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-xs text-slate-500">
                No appointments found for this patient.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {appointments.map((app) => (
                  <div key={app.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900">{app.hospital_name}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                          app.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                          app.status === 'confirmed' ? 'bg-sky-100 text-sky-800' : 'bg-slate-100 text-slate-600'
                        }`}>
                          {app.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">{app.notes || 'Routine consultation'}</p>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-600 font-medium">
                      <span className="flex items-center gap-1 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                        <Calendar className="w-3.5 h-3.5 text-tealmed-600" /> {app.date}
                      </span>
                      <span className="flex items-center gap-1 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                        <Clock className="w-3.5 h-3.5 text-tealmed-600" /> {app.start_time} - {app.end_time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Medical Records */}
      {activeTab === 'records' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <div>
              <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-600" /> Scoped Medical Records
              </h2>
              <p className="text-xs text-slate-500">
                Medical files, lab reports, and diagnostic scans attached to {pName}.
              </p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 transition"
            >
              <Plus className="w-4 h-4" /> Add Record
            </button>
          </div>

          {records.length === 0 ? (
            <div className="bg-white rounded-3xl p-12 text-center text-slate-400 border border-slate-200 space-y-3">
              <FileUp className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="text-sm font-medium text-slate-600">No medical records uploaded for this patient yet.</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-xl border border-emerald-200 hover:bg-emerald-100 transition-colors"
              >
                <Plus className="w-4 h-4" /> Upload First Record
              </button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {records.map((r) => (
                <div key={r.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <span className="text-[10px] font-extrabold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full uppercase tracking-wider border border-emerald-100">
                      {r.record_type.replace('_', ' ')}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      r.uploaded_by === 'doctor' ? 'bg-purple-100 text-purple-800' : 'bg-sky-100 text-sky-800'
                    }`}>
                      Uploaded by {r.uploaded_by || 'patient'}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-extrabold text-slate-900 text-base">{r.title}</h4>
                    {r.description && <p className="text-slate-600 text-xs mt-1 leading-relaxed">{r.description}</p>}
                  </div>

                  <div className="space-y-2 pt-3 border-t border-slate-100 text-xs">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Date: {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'}</span>
                      {r.file_size_bytes && (
                        <span>{(r.file_size_bytes / 1024).toFixed(0)} KB</span>
                      )}
                    </div>

                    {r.signed_file_url ? (
                      <a
                        href={r.signed_file_url}
                        target="_blank"
                        rel="noreferrer"
                        className="w-full py-2 px-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold rounded-xl flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <ShieldCheck className="w-4 h-4 text-emerald-600" /> View / Download File <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-400 text-xs italic block text-center py-1">No attached document URL</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Upload Medical Record Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl relative border border-slate-100">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-extrabold text-slate-900">Add Medical Record</h3>
                <p className="text-xs text-slate-500">Attached to patient {pName} ({pCode})</p>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {uploadError && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadRecord} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Record Title *</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Chest X-Ray Report, Blood Test Panel"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Record Type</label>
                <select
                  value={recordType}
                  onChange={(e) => setRecordType(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
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
                <label className="block text-xs font-bold text-slate-700 mb-1">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Clinical notes, findings, or lab observations..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Upload File (PDF, JPG, PNG, WEBP — max 15MB) *</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.jpg,.jpeg,.png,.webp"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2.5 rounded-xl text-slate-600 font-bold text-xs hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
