import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { AdminSidebar } from '../components/AdminSidebar';
import { Hospital } from '../types';
import { Building2, Plus, Edit2, Trash2, Key, UserCheck, X, ShieldCheck } from 'lucide-react';

export const AdminHospitalsPage: React.FC = () => {
  const { showToast } = useToast();
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);

  // Admin Credentials Modal State
  const [selectedHospital, setSelectedHospital] = useState<Hospital | null>(null);
  const [isCredentialModalOpen, setIsCredentialModalOpen] = useState(false);
  const [fetchingAdminInfo, setFetchingAdminInfo] = useState(false);
  const [existingAdmin, setExistingAdmin] = useState<any>(null);

  const [credentialForm, setCredentialForm] = useState({
    email: '',
    password: '',
    name: ''
  });

  useEffect(() => {
    fetchHospitals();
  }, []);

  const fetchHospitals = async () => {
    try {
      const res = await api.get('/hospitals');
      setHospitals(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCredentialsModal = async (hospital: Hospital) => {
    setSelectedHospital(hospital);
    setIsCredentialModalOpen(true);
    setFetchingAdminInfo(true);
    setExistingAdmin(null);
    setCredentialForm({ email: '', password: '', name: '' });

    try {
      const res = await api.get(`/admin/hospitals/${hospital.id}/admin-credentials`);
      if (res.data && res.data.has_admin && res.data.admin_user) {
        setExistingAdmin(res.data.admin_user);
        setCredentialForm({
          email: res.data.admin_user.email || '',
          password: '',
          name: res.data.admin_user.name || ''
        });
      }
    } catch (err) {
      console.error('Failed to fetch hospital admin credentials:', err);
    } finally {
      setFetchingAdminInfo(false);
    }
  };

  const handleSaveAdminCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedHospital) return;
    try {
      await api.post(`/admin/hospitals/${selectedHospital.id}/admin-credentials`, credentialForm);
      showToast('Hospital Admin credentials saved successfully!', 'success');
      setIsCredentialModalOpen(false);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to save admin credentials', 'error');
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <AdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">Hospital Nodes Directory</h1>
            <p className="text-xs text-slate-500">Manage registered healthcare facilities and assign Hospital Admin login accounts.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {hospitals.map((h) => (
            <div key={h.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono font-bold text-medical-700 bg-medical-50 px-2 py-0.5 rounded">{h.id}</span>
                    <h3 className="text-lg font-bold text-slate-900">{h.hospital_name}</h3>
                    <p className="text-xs text-slate-500">{h.street}, {h.area}, {h.city}</p>
                  </div>
                  <Building2 className="w-6 h-6 text-medical-600" />
                </div>

                <div className="pt-2 border-t border-slate-100 space-y-2 text-xs">
                  <div className="flex justify-between text-slate-600">
                    <span>Phone:</span>
                    <span className="font-semibold">{h.phone}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Email:</span>
                    <span className="font-semibold">{h.email}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-medium block mb-1">Departments:</span>
                    <div className="flex flex-wrap gap-1">
                      {(h.departments || []).map((dept, idx) => (
                        <span key={idx} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-semibold">
                          {dept}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex justify-end">
                <button
                  onClick={() => handleOpenCredentialsModal(h)}
                  className="flex items-center gap-2 px-3.5 py-2 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-xl text-xs font-semibold border border-teal-200 transition-colors"
                >
                  <Key className="w-3.5 h-3.5" />
                  <span>Manage Admin Account</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Credentials Modal */}
        {isCredentialModalOpen && selectedHospital && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-teal-600" />
                  <h2 className="text-base font-bold text-slate-900">Hospital Admin Credentials</h2>
                </div>
                <button onClick={() => setIsCredentialModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80 text-xs">
                <div className="font-bold text-slate-800">{selectedHospital.hospital_name}</div>
                <div className="text-slate-500 font-mono text-[11px]">ID: {selectedHospital.id}</div>
              </div>

              {fetchingAdminInfo ? (
                <div className="py-6 text-center text-xs text-slate-500 animate-pulse">
                  Checking existing admin account...
                </div>
              ) : (
                <form onSubmit={handleSaveAdminCredentials} className="space-y-4">
                  {existingAdmin ? (
                    <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-xs text-teal-800 flex items-center gap-2">
                      <UserCheck className="w-4 h-4 text-teal-600 shrink-0" />
                      <div>
                        <span className="font-bold">Active Admin:</span> {existingAdmin.email}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
                      No Hospital Admin account assigned yet. Fill below to create login credentials.
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Admin Display Name</label>
                    <input
                      type="text"
                      placeholder={`Admin (${selectedHospital.hospital_name})`}
                      value={credentialForm.name}
                      onChange={(e) => setCredentialForm({ ...credentialForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Admin Login Email</label>
                    <input
                      type="email"
                      required
                      placeholder="admin@hospital.com"
                      value={credentialForm.email}
                      onChange={(e) => setCredentialForm({ ...credentialForm, email: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      {existingAdmin ? 'New Password (Leave blank to keep existing)' : 'Password'}
                    </label>
                    <input
                      type="password"
                      required={!existingAdmin}
                      placeholder="••••••••"
                      value={credentialForm.password}
                      onChange={(e) => setCredentialForm({ ...credentialForm, password: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setIsCredentialModalOpen(false)}
                      className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-semibold hover:bg-slate-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-semibold hover:bg-teal-700"
                    >
                      {existingAdmin ? 'Update Credentials' : 'Create Admin Account'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
