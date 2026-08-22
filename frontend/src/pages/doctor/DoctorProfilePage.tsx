import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Stethoscope, Mail, Award, DollarSign, Building, ShieldCheck } from 'lucide-react';

export const DoctorProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [doctorInfo, setDoctorInfo] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/doctors/me');
      setDoctorInfo(res.data);
    } catch (err) {
      console.error('Failed to fetch doctor profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const doc = doctorInfo?.doctor;

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-16">
      <div className="bg-gradient-to-r from-tealmed-900 to-medical-900 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Doctor Profile & Medical Identity</h1>
        <p className="text-xs sm:text-sm text-slate-300">Your account identity and associated doctor credentials.</p>
      </div>

      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
          <div className="w-16 h-16 rounded-full bg-tealmed-100 text-tealmed-800 flex items-center justify-center font-extrabold text-2xl border-2 border-tealmed-200">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'D'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{doc?.name || user?.name}</h2>
            <p className="text-xs text-slate-500">{user?.email}</p>
            <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-tealmed-50 text-tealmed-700 uppercase">
              Attending Specialist Account ({user?.role})
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Account & Doctor Identity Details</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">User Profile ID (UUID)</span>
              <p className="font-mono text-slate-800 font-bold break-all">{user?.id}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Doctor Record ID</span>
              <p className="font-mono text-tealmed-800 font-bold break-all">{doc?.id || 'N/A'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Medical Specialization</span>
              <p className="font-semibold text-slate-800">{doc?.specialization || 'General'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Qualifications / Degree</span>
              <p className="font-semibold text-slate-800">{doc?.degree || 'MBBS'}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Consultation Fee</span>
              <p className="font-extrabold text-emerald-700">₹{doc?.consultation_fee || 500}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Hospital Node ID</span>
              <p className="font-semibold text-slate-800">{doc?.hospital_id || 'H001'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
