import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { HospitalAdminSidebar } from '../../components/HospitalAdminSidebar';
import { Doctor, Department } from '../../types';
import { 
  Stethoscope, 
  Plus, 
  Trash2, 
  Edit3, 
  Search, 
  X,
  UserCheck,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';

export const HospitalAdminDoctorsPage: React.FC = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null);

  const { showToast } = useToast();

  const [formData, setFormData] = useState({
    id: '',
    name: '',
    specialization: '',
    degree: 'MBBS',
    experience_years: 5,
    consultation_fee: 500,
    availability: 'Mon - Fri (09:00 AM - 05:00 PM)',
    department_id: '',
    image_url: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [docRes, deptRes] = await Promise.all([
        api.get('/hospital-admin/doctors'),
        api.get('/hospital-admin/departments')
      ]);
      setDoctors(docRes.data || []);
      setDepartments(deptRes.data || []);
    } catch (err) {
      console.error('Failed to fetch doctors:', err);
      showToast('Failed to load doctors', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreateModal = () => {
    setEditingDoctor(null);
    setFormData({
      id: `DOC_${Date.now()}`,
      name: '',
      specialization: '',
      degree: 'MBBS',
      experience_years: 5,
      consultation_fee: 500,
      availability: 'Mon - Fri (09:00 AM - 05:00 PM)',
      department_id: departments[0]?.id || '',
      image_url: 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80'
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (doctor: Doctor) => {
    setEditingDoctor(doctor);
    setFormData({
      id: doctor.id,
      name: doctor.name || '',
      specialization: doctor.specialization || '',
      degree: doctor.degree || 'MBBS',
      experience_years: doctor.experience_years || 0,
      consultation_fee: doctor.consultation_fee || 0,
      availability: doctor.availability || '',
      department_id: doctor.department_id || '',
      image_url: doctor.image_url || ''
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingDoctor) {
        await api.put(`/hospital-admin/doctors/${editingDoctor.id}`, formData);
        showToast('Doctor profile updated successfully', 'success');
      } else {
        await api.post('/hospital-admin/doctors', formData);
        showToast('Doctor registered successfully', 'success');
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to save doctor';
      showToast(msg, 'error');
    }
  };

  const handleDelete = async (doctorId: string) => {
    if (!window.confirm('Are you sure you want to remove this doctor from your hospital?')) return;
    try {
      await api.delete(`/hospital-admin/doctors/${doctorId}`);
      showToast('Doctor removed successfully', 'success');
      fetchData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete doctor', 'error');
    }
  };

  const filteredDoctors = doctors.filter((doc) =>
    (doc.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (doc.specialization || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <HospitalAdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Hospital Doctors</h1>
            <p className="text-xs text-slate-500">Manage registered doctors for your medical facility</p>
          </div>
          <button
            onClick={handleOpenCreateModal}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Doctor</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-md">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search doctor name or specialization..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        {/* List Content */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white p-5 rounded-2xl border border-slate-200 animate-pulse space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-200 rounded-full"></div>
                  <div className="space-y-2 flex-1">
                    <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                    <div className="h-3 bg-slate-200 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredDoctors.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4 max-w-md mx-auto my-8">
            <div className="w-16 h-16 bg-teal-50 text-teal-600 rounded-full flex items-center justify-center mx-auto">
              <Stethoscope className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-900">No Doctors Registered</h3>
              <p className="text-xs text-slate-500">Add practitioners to start scheduling consultations at your hospital.</p>
            </div>
            <button
              onClick={handleOpenCreateModal}
              className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-semibold hover:bg-teal-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Register First Doctor</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDoctors.map((doc) => (
              <div key={doc.id} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4 hover:border-slate-300 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <img
                      src={doc.image_url || 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80'}
                      alt={doc.name}
                      className="w-12 h-12 rounded-full object-cover border border-slate-100"
                    />
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{doc.name}</h3>
                      <span className="text-xs text-teal-600 font-semibold">{doc.specialization}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
                    Active
                  </span>
                </div>

                <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-3 rounded-xl">
                  <div><span className="font-semibold text-slate-700">Degree:</span> {doc.degree || 'MBBS'}</div>
                  <div><span className="font-semibold text-slate-700">Experience:</span> {doc.experience_years || 0} years</div>
                  <div><span className="font-semibold text-slate-700">Fee:</span> ₹{doc.consultation_fee || 0}</div>
                  <div><span className="font-semibold text-slate-700">Timing:</span> {doc.availability || 'N/A'}</div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => handleOpenEditModal(doc)}
                    className="p-2 text-slate-600 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal for Add / Edit Doctor */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-lg w-full p-6 space-y-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <h2 className="text-lg font-bold text-slate-900">
                  {editingDoctor ? 'Edit Doctor Profile' : 'Register New Doctor'}
                </h2>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Doctor ID</label>
                    <input
                      type="text"
                      required
                      disabled={!!editingDoctor}
                      value={formData.id}
                      onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      placeholder="Dr. John Doe"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Specialization</label>
                    <input
                      type="text"
                      required
                      placeholder="Cardiology"
                      value={formData.specialization}
                      onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Degree</label>
                    <input
                      type="text"
                      placeholder="MBBS, MD"
                      value={formData.degree}
                      onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Experience (Years)</label>
                    <input
                      type="number"
                      required
                      value={formData.experience_years}
                      onChange={(e) => setFormData({ ...formData, experience_years: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Consultation Fee (₹)</label>
                    <input
                      type="number"
                      required
                      value={formData.consultation_fee}
                      onChange={(e) => setFormData({ ...formData, consultation_fee: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Working Hours / Availability</label>
                  <input
                    type="text"
                    value={formData.availability}
                    onChange={(e) => setFormData({ ...formData, availability: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
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
                    className="px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-semibold hover:bg-teal-700"
                  >
                    Save Doctor
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
