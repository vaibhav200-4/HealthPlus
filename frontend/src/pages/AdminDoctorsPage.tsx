import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { AdminSidebar } from '../components/AdminSidebar';
import { Doctor } from '../types';
import { Stethoscope, Plus, Trash2, Edit2, Check, X } from 'lucide-react';

export const AdminDoctorsPage: React.FC = () => {
  const { showToast } = useToast();
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDoc, setEditingDoc] = useState<Doctor | null>(null);

  // Form fields
  const [id, setId] = useState('');
  const [hospitalId, setHospitalId] = useState('H001');
  const [name, setName] = useState('');
  const [degree, setDegree] = useState('');
  const [specialization, setSpecialization] = useState('Cardiology');
  const [experienceYears, setExperienceYears] = useState(5);
  const [designation, setDesignation] = useState('Consultant');
  const [fee, setFee] = useState(500);

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      const res = await api.get('/doctors');
      setDoctors(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setEditingDoc(null);
    setId(`D${Math.floor(100 + Math.random() * 900)}`);
    setName('');
    setDegree('MBBS, MD');
    setSpecialization('Cardiology');
    setExperienceYears(5);
    setDesignation('Senior Specialist');
    setFee(700);
    setModalOpen(true);
  };

  const handleOpenEdit = (doc: Doctor) => {
    setEditingDoc(doc);
    setId(doc.id);
    setHospitalId(doc.hospital_id);
    setName(doc.name);
    setDegree(doc.degree || '');
    setSpecialization(doc.specialization);
    setExperienceYears(doc.experience_years);
    setDesignation(doc.designation || '');
    setFee(doc.consultation_fee);
    setModalOpen(true);
  };

  const handleDelete = async (docId: string) => {
    if (!window.confirm(`Delete doctor ${docId}?`)) return;
    try {
      await api.delete(`/admin/doctors/${docId}`);
      showToast('Doctor deleted', 'info');
      fetchDoctors();
    } catch (err) {
      showToast('Failed to delete doctor', 'error');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      id,
      hospital_id: hospitalId,
      name,
      degree,
      specialization,
      experience_years: experienceYears,
      designation,
      languages: ['English', 'Hindi'],
      consultation_fee: fee,
      availability: 'Monday to Saturday, 10:00 AM - 2:00 PM',
      image_url: 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80'
    };

    try {
      if (editingDoc) {
        await api.put(`/admin/doctors/${id}`, payload);
        showToast('Doctor updated successfully', 'success');
      } else {
        await api.post('/admin/doctors', payload);
        showToast('Doctor created successfully', 'success');
      }
      setModalOpen(false);
      fetchDoctors();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Operation failed', 'error');
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <AdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">Doctor Directory CRUD</h1>
            <p className="text-xs text-slate-500">Add, update, or remove medical staff.</p>
          </div>
          <button
            onClick={handleOpenAdd}
            className="px-4 py-2 bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs rounded-xl shadow flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add New Doctor
          </button>
        </div>

        {/* Table */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-bold">
              <tr>
                <th className="p-4">Doctor ID</th>
                <th className="p-4">Name</th>
                <th className="p-4">Specialization</th>
                <th className="p-4">Experience</th>
                <th className="p-4">Fee</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {doctors.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50">
                  <td className="p-4 font-mono font-bold text-medical-700">{doc.id}</td>
                  <td className="p-4 font-bold text-slate-900">{doc.name}</td>
                  <td className="p-4 font-semibold text-slate-600">{doc.specialization}</td>
                  <td className="p-4">{doc.experience_years} Years</td>
                  <td className="p-4 font-bold text-slate-800">₹{doc.consultation_fee}</td>
                  <td className="p-4 text-right space-x-2">
                    <button
                      onClick={() => handleOpenEdit(doc)}
                      className="p-1.5 text-slate-600 hover:text-medical-600 rounded-lg hover:bg-medical-50"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-600 hover:text-rose-600 rounded-lg hover:bg-rose-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">{editingDoc ? 'Edit Doctor' : 'Add New Doctor'}</h3>
            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold mb-1">Doctor ID</label>
                <input
                  type="text"
                  value={id}
                  onChange={(e) => setId(e.target.value)}
                  disabled={!!editingDoc}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Specialization</label>
                <input
                  type="text"
                  value={specialization}
                  onChange={(e) => setSpecialization(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold mb-1">Experience (Years)</label>
                  <input
                    type="number"
                    value={experienceYears}
                    onChange={(e) => setExperienceYears(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold mb-1">Fee (₹)</label>
                  <input
                    type="number"
                    value={fee}
                    onChange={(e) => setFee(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-medical-600 text-white rounded-xl font-bold shadow"
                >
                  Save Doctor
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
