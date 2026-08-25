import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../services/api';
import { MedicalRecord } from '../types';
import {
  User as UserIcon,
  Mail,
  Phone,
  Smartphone,
  Shield,
  CheckCircle2,
  FileText,
  Plus,
  ExternalLink,
  ShieldCheck,
  FileUp,
  AlertCircle,
  X
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, linkTelegram } = useAuth();
  const { showToast } = useToast();

  const [telegramId, setTelegramId] = useState(user?.telegram_id || '');
  const [saving, setSaving] = useState(false);

  // Medical History State
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loadingRecords, setLoadingRecords] = useState<boolean>(true);
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [title, setTitle] = useState<string>('');
  const [recordType, setRecordType] = useState<string>('diagnosis');
  const [description, setDescription] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string>('');

  useEffect(() => {
    if (user?.id) {
      fetchMyRecords();
    }
  }, [user?.id]);

  const fetchMyRecords = async () => {
    setLoadingRecords(true);
    try {
      const res = await api.get(`/medical-records/patient/${user?.id}`);
      setRecords(res.data || []);
    } catch (err) {
      console.error('Failed to fetch patient medical records:', err);
    } finally {
      setLoadingRecords(false);
    }
  };

  const handleSaveTelegram = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const success = await linkTelegram(telegramId);
    if (success) {
      showToast('Telegram account linked successfully!', 'success');
    } else {
      showToast('Failed to link Telegram account', 'error');
    }
    setSaving(false);
  };

  const handleUploadRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a file (PDF, JPG, PNG, WEBP, max 15MB)');
      return;
    }

    setUploading(true);
    setUploadError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('patient_identifier', user?.id || '');
      formData.append('uploaded_by', 'patient');
      formData.append('title', title);
      formData.append('record_type', recordType);
      if (description) formData.append('description', description);

      await api.post('/medical-records/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      showToast('Medical record uploaded successfully!', 'success');
      setShowUploadModal(false);
      setTitle('');
      setDescription('');
      setSelectedFile(null);
      setRecordType('diagnosis');
      fetchMyRecords();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload medical record');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-medical-900 to-tealmed-800 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Patient Profile & Identity</h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Manage your identity details, Telegram integration, and medical history.
        </p>
      </div>

      {/* Account Info Card */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
          <div className="w-16 h-16 rounded-full bg-medical-100 text-medical-700 flex items-center justify-center font-extrabold text-2xl border-2 border-medical-200">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{user?.name}</h2>
            <p className="text-xs text-slate-500">{user?.email}</p>
            <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-medical-50 text-medical-700 uppercase">
              {user?.role} Account
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Account Identity Details</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Internal User ID (UUID)</span>
              <p className="font-mono text-slate-800 font-bold break-all">{user?.id}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Email Address</span>
              <p className="font-semibold text-slate-800">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Telegram Mapping Section */}
        <form onSubmit={handleSaveTelegram} className="pt-4 border-t border-slate-100 space-y-3">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-sky-500" />
            Link Telegram Identity
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Connecting your Telegram User ID associates Telegram bot messages with this primary application user account.
          </p>

          <div className="flex gap-2 max-w-md">
            <input
              type="text"
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              placeholder="e.g. 98765432"
              className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-sky-500"
            />
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow transition-all"
            >
              {saving ? 'Saving...' : 'Save Telegram ID'}
            </button>
          </div>
        </form>
      </div>

      {/* My Medical History & Reports Section */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" /> My Medical History & Records
            </h3>
            <p className="text-xs text-slate-500">
              Access reports uploaded by your doctors or upload your own lab documents.
            </p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" /> Upload Medical Record
          </button>
        </div>

        {loadingRecords ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading medical history...</div>
        ) : records.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200 space-y-2">
            <FileUp className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-sm font-medium text-slate-700">No medical records uploaded yet.</p>
            <p className="text-xs text-slate-500">Upload lab reports, prescriptions, or imaging scans to keep them synced.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {records.map((r) => (
              <div key={r.id} className="p-5 bg-slate-50/70 border border-slate-200 rounded-2xl space-y-3 hover:bg-white hover:shadow-md transition-all">
                <div className="flex justify-between items-start">
                  <span className="text-[10px] font-extrabold px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-full uppercase">
                    {r.record_type.replace('_', ' ')}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    r.uploaded_by === 'doctor' ? 'bg-purple-100 text-purple-800' : 'bg-sky-100 text-sky-800'
                  }`}>
                    {r.uploaded_by === 'doctor' ? 'Doctor Upload' : 'My Upload'}
                  </span>
                </div>

                <div>
                  <h4 className="font-extrabold text-slate-900 text-sm">{r.title}</h4>
                  {r.description && <p className="text-slate-600 text-xs mt-1">{r.description}</p>}
                </div>

                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'}
                  </span>
                  {r.signed_file_url && (
                    <a
                      href={r.signed_file_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-700 hover:text-emerald-900 font-bold flex items-center gap-1"
                    >
                      View File <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Patient Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl relative border border-slate-100">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-extrabold text-slate-900">Upload Medical Record</h3>
                <p className="text-xs text-slate-500">Upload reports to sync with your medical profile</p>
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
                  placeholder="e.g. My Blood Report Aug 2026"
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
                  <option value="lab_report">Lab Report</option>
                  <option value="blood_test">Blood Test</option>
                  <option value="xray">X-Ray</option>
                  <option value="mri">MRI Scan</option>
                  <option value="diagnosis">Diagnosis</option>
                  <option value="discharge_summary">Discharge Summary</option>
                  <option value="other">Other Document</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Notes about this document..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Select File (PDF, JPG, PNG, WEBP — max 15MB) *</label>
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
