import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { AdminSidebar } from '../components/AdminSidebar';
import { Hospital } from '../types';
import { Building2, Plus, Edit2, Trash2 } from 'lucide-react';

export const AdminHospitalsPage: React.FC = () => {
  const { showToast } = useToast();
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <AdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">Hospital Nodes Directory</h1>
            <p className="text-xs text-slate-500">Manage registered healthcare facilities and departments.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {hospitals.map((h) => (
            <div key={h.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
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
                    {h.departments.map((dept, idx) => (
                      <span key={idx} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-semibold">
                        {dept}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};
