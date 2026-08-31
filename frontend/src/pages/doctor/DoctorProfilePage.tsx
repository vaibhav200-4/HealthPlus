import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { Stethoscope, Mail, Award, DollarSign, Building, ShieldCheck, User as UserIcon, CheckCircle2 } from 'lucide-react';

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
  const initial = user?.name ? user.name.charAt(0).toUpperCase() : 'D';

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Reusable Doctor Portal Hero */}
      <DoctorPortalHero
        badgeText="Account & Medical Identity"
        badgeIcon={<UserIcon className="w-4 h-4 text-tealmed-700" />}
        title={`Doctor Profile — Dr. ${(doc?.name || user?.name || 'Practitioner').replace(/^Dr\.\s*/i, '')}`}
        subtitle="Manage clinical credentials, view fee structure, and verify hospital affiliations."
        metadata={[
          { icon: <ShieldCheck className="w-3.5 h-3.5 text-tealmed-600" />, label: `Verified Account (${user?.role || 'doctor'})` }
        ]}
      />

      {/* Profile Details Card */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-2xs space-y-6">
        <div className="flex items-center gap-5 pb-6 border-b border-slate-100">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-tealmed-600 to-tealmed-500 text-white flex items-center justify-center font-extrabold text-3xl border border-tealmed-400 shadow-md">
            {initial}
          </div>
          <div className="space-y-1">
            <h2 className="text-2xl font-extrabold text-slate-900">{doc?.name || user?.name}</h2>
            <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              {user?.email}
            </p>
            <div className="pt-1">
              <span className="inline-block px-3 py-1 rounded-full text-xs font-extrabold bg-tealmed-100 text-tealmed-900 border border-tealmed-200">
                Attending Specialist ({user?.role?.toUpperCase() || 'DOCTOR'})
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-xs font-extrabold text-slate-500 uppercase tracking-wider">Account & Doctor Identity Credentials</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-500 font-medium">User Profile ID (UUID)</span>
              <p className="font-mono text-slate-900 font-bold break-all">{user?.id}</p>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-500 font-medium">Doctor Record ID</span>
              <p className="font-mono text-tealmed-800 font-bold break-all">{doc?.id || 'N/A'}</p>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-500 font-medium">Medical Specialization</span>
              <p className="font-extrabold text-slate-900 text-sm">{doc?.specialization || 'General Medicine'}</p>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-500 font-medium">Qualifications / Degree</span>
              <p className="font-extrabold text-slate-900 text-sm">{doc?.degree || 'MBBS'}</p>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-500 font-medium">Consultation Fee</span>
              <p className="font-extrabold text-emerald-700 text-base">₹{doc?.consultation_fee || 500}</p>
            </div>

            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-500 font-medium">Hospital Node Affiliation</span>
              <p className="font-extrabold text-slate-900 text-sm">{doc?.hospital_id || 'H001'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
