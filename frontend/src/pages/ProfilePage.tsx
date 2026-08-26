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
  X,
  Edit3,
  Save,
  Calendar,
  Heart,
  Activity,
  MapPin,
  AlertTriangle
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, linkTelegram, updateProfile } = useAuth();
  const { showToast } = useToast();

  const [telegramId, setTelegramId] = useState(user?.telegram_id || '');
  const [saving, setSaving] = useState(false);

  // Health Information Editing State
  const [isEditingHealthInfo, setIsEditingHealthInfo] = useState(false);
  const [dobInput, setDobInput] = useState(user?.date_of_birth || '');
  const [genderInput, setGenderInput] = useState(user?.gender || '');
  const [bloodGroupInput, setBloodGroupInput] = useState(user?.blood_group || '');
  const [phoneInput, setPhoneInput] = useState(user?.phone || '');
  const [addressInput, setAddressInput] = useState(user?.address || '');
  const [emergencyContactInput, setEmergencyContactInput] = useState(user?.emergency_contact || '');
  const [savingHealthInfo, setSavingHealthInfo] = useState(false);

  // Sync inputs if user changes externally
  useEffect(() => {
    if (user) {
      setDobInput(user.date_of_birth || '');
      setGenderInput(user.gender || '');
      setBloodGroupInput(user.blood_group || '');
      setPhoneInput(user.phone || '');
      setAddressInput(user.address || '');
      setEmergencyContactInput(user.emergency_contact || '');
    }
  }, [user]);

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

  const handleSaveHealthInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingHealthInfo(true);
    const success = await updateProfile({
      date_of_birth: dobInput,
      gender: genderInput,
      blood_group: bloodGroupInput,
      phone: phoneInput,
      address: addressInput,
      emergency_contact: emergencyContactInput
    });

    if (success) {
      showToast('Personal & health information updated successfully!', 'success');
      setIsEditingHealthInfo(false);
    } else {
      showToast('Failed to update personal information', 'error');
    }
    setSavingHealthInfo(false);
  };

  const handleCancelHealthInfo = () => {
    if (user) {
      setDobInput(user.date_of_birth || '');
      setGenderInput(user.gender || '');
      setBloodGroupInput(user.blood_group || '');
      setPhoneInput(user.phone || '');
      setAddressInput(user.address || '');
      setEmergencyContactInput(user.emergency_contact || '');
    }
    setIsEditingHealthInfo(false);
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
        <h1 className="text-3xl font-extrabold tracking-tight">Patient Profile & Health Details</h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Manage your personal health information, Telegram integration, and medical records.
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
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Account Information</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Patient Code</span>
              <p className="font-mono text-medical-700 font-bold">{user?.patient_code || 'PT-PENDING'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Patient ID</span>
              <p className="font-mono text-slate-800 font-bold break-all">{user?.id}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Email Address</span>
              <p className="font-semibold text-slate-800">{user?.email}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Personal & Health Information Section */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-medical-600" /> Personal & Health Information
            </h3>
            <p className="text-xs text-slate-500">
              Keep your health profile updated for accurate doctor consultations.
            </p>
          </div>

          {!isEditingHealthInfo && (
            <button
              onClick={() => setIsEditingHealthInfo(true)}
              className="px-4 py-2 bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs rounded-xl shadow flex items-center gap-2 transition-all self-start sm:self-auto"
            >
              <Edit3 className="w-4 h-4" /> Edit Information
            </button>
          )}
        </div>

        {isEditingHealthInfo ? (
          <form onSubmit={handleSaveHealthInfo} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dobInput}
                  onChange={(e) => setDobInput(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-medical-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Gender</label>
                <select
                  value={genderInput}
                  onChange={(e) => setGenderInput(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-medical-500 outline-none"
                >
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                  <option value="Prefer not to say">Prefer not to say</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Blood Group</label>
                <select
                  value={bloodGroupInput}
                  onChange={(e) => setBloodGroupInput(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-medical-500 outline-none"
                >
                  <option value="">Select Blood Group</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={phoneInput}
                  onChange={(e) => setPhoneInput(e.target.value)}
                  placeholder="e.g. +91 98765 43210"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-medical-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Address</label>
                <input
                  type="text"
                  value={addressInput}
                  onChange={(e) => setAddressInput(e.target.value)}
                  placeholder="e.g. Indore, Madhya Pradesh"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-medical-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Emergency Contact</label>
                <input
                  type="text"
                  value={emergencyContactInput}
                  onChange={(e) => setEmergencyContactInput(e.target.value)}
                  placeholder="e.g. Spouse (+91 9876543210)"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-medical-500 outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={handleCancelHealthInfo}
                className="px-4 py-2 rounded-xl text-slate-600 font-bold text-xs hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingHealthInfo}
                className="px-5 py-2 bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs rounded-xl shadow flex items-center gap-1.5 transition-all disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {savingHealthInfo ? 'Saving Changes...' : 'Save Changes'}
              </button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Date of Birth</span>
              <p className="font-bold text-slate-800">{user?.date_of_birth || 'Not specified'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Gender</span>
              <p className="font-bold text-slate-800">{user?.gender || 'Not specified'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Blood Group</span>
              <p className="font-bold text-rose-600">{user?.blood_group || 'Not specified'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Phone Number</span>
              <p className="font-bold text-slate-800">{user?.phone || 'Not specified'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Address</span>
              <p className="font-bold text-slate-800">{user?.address || 'Not specified'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Emergency Contact</span>
              <p className="font-bold text-slate-800">{user?.emergency_contact || 'Not specified'}</p>
            </div>
          </div>
        )}
      </div>

      {/* Account Connections / Telegram Section */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleSaveTelegram} className="space-y-3">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-sky-500" />
            Telegram Account Connection
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Connecting your Telegram User ID associates Telegram bot consultations with your patient record.
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
              <FileText className="w-5 h-5 text-emerald-600" /> Medical Documents & Health Records
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
