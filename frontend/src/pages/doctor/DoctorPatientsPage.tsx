import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { Users, Search, Mail, Phone, Calendar, ChevronRight, FileText } from 'lucide-react';

export const DoctorPatientsPage: React.FC = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const res = await api.get('/doctors/me/patients');
      setPatients(res.data || []);
    } catch (err) {
      console.error('Failed to fetch doctor patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = patients.filter((p) => {
    if (!searchTerm) return true;
    const s = searchTerm.toLowerCase();
    return (
      (p.patient_name || '').toLowerCase().includes(s) ||
      (p.patient_email || '').toLowerCase().includes(s) ||
      (p.patient_phone || '').toLowerCase().includes(s) ||
      (p.patient_code || '').toLowerCase().includes(s)
    );
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-tealmed-900 to-medical-900 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Your Associated Patients</h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Click any patient card to view their profile, consultation history, and medical records.
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search patient by name, email, phone, or code..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-tealmed-500"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>
        <span className="text-xs font-bold text-slate-500">Total Unique: {patients.length}</span>
      </div>

      {/* Patients Grid */}
      {loading ? (
        <div className="p-8 text-center text-xs text-slate-500">Loading patient list...</div>
      ) : filtered.length === 0 ? (
        <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
          <Users className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-700">No patients found for your doctor account.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((p, idx) => {
            const targetId = p.patient_id || p.user_id;
            return (
              <Link
                key={idx}
                to={`/doctor/patients/${targetId}`}
                className="group bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4 hover:shadow-lg hover:border-tealmed-300 transition-all cursor-pointer block"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3.5">
                    <div className="w-12 h-12 rounded-2xl bg-tealmed-100 text-tealmed-800 flex items-center justify-center font-extrabold text-lg border border-tealmed-200 group-hover:scale-105 transition-transform">
                      {p.patient_name ? p.patient_name.charAt(0).toUpperCase() : 'P'}
                    </div>
                    <div>
                      <h3 className="font-extrabold text-base text-slate-900 group-hover:text-tealmed-700 transition-colors flex items-center gap-1.5">
                        {p.patient_name}
                      </h3>
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">
                        {p.patient_code || 'Patient'}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-tealmed-600 group-hover:translate-x-1 transition-all" />
                </div>

                <div className="space-y-2 text-xs text-slate-600 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    <span>{p.patient_email || 'No email provided'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{p.patient_phone || 'No phone provided'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-tealmed-600" />
                    <span>Last appointment: <strong className="text-slate-800">{p.last_appointment_date}</strong></span>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs font-semibold text-tealmed-700 bg-tealmed-50/50 p-2.5 rounded-xl border border-tealmed-100 group-hover:bg-tealmed-100/50 transition-colors">
                  <span className="flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-tealmed-600" /> View Profile & Records
                  </span>
                  <span className="text-[10px] font-bold bg-white px-2 py-0.5 rounded text-tealmed-800 shadow-xs">
                    {p.total_appointments} Consultation(s)
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};
