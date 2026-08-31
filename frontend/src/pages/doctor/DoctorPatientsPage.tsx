import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { Users, Search, Mail, Phone, Calendar, ChevronRight, FileText, UserCheck } from 'lucide-react';

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
      {/* Reusable Doctor Portal Hero */}
      <DoctorPortalHero
        badgeText="Patient Roster Directory"
        badgeIcon={<Users className="w-4 h-4 text-tealmed-700" />}
        title="Associated Patients & Clinical Records"
        subtitle="Access patient profiles, review past consultations, and upload diagnostic files."
        metadata={[
          { icon: <UserCheck className="w-3.5 h-3.5 text-tealmed-600" />, label: `${patients.length} Unique Patients` }
        ]}
      />

      {/* Search Bar Toolbar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full max-w-md">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search patient by name, email, phone, or patient ID..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-tealmed-500 focus:bg-white transition-all"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>
        <span className="text-xs font-bold text-slate-600">Showing {filtered.length} of {patients.length} patients</span>
      </div>

      {/* Patients Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
          <div className="w-6 h-6 border-2 border-tealmed-500 border-t-transparent rounded-full animate-spin"></div>
          Loading patient directory...
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-slate-50/70 rounded-3xl border border-dashed border-slate-200 space-y-2">
          <Users className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <p className="text-sm font-semibold text-slate-700">No associated patients found.</p>
          <p className="text-xs text-slate-500">Patients with confirmed or past consultations will appear here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((p, idx) => {
            const targetId = p.patient_id || p.user_id;
            const initial = p.patient_name ? p.patient_name.charAt(0).toUpperCase() : 'P';
            return (
              <Link
                key={idx}
                to={`/doctor/patients/${targetId}`}
                className="group bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4 hover:shadow-md hover:border-tealmed-300 transition-all cursor-pointer block"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3.5">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-tealmed-100 to-emerald-100 text-tealmed-800 flex items-center justify-center font-extrabold text-lg border border-tealmed-200/80 group-hover:scale-105 transition-transform">
                      {initial}
                    </div>
                    <div>
                      <h3 className="font-extrabold text-base text-slate-900 group-hover:text-tealmed-700 transition-colors flex items-center gap-1.5">
                        {p.patient_name}
                      </h3>
                      <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200/60">
                        {p.patient_code || 'Patient'}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-tealmed-600 group-hover:translate-x-1 transition-all" />
                </div>

                <div className="space-y-2 text-xs text-slate-600 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    <span className="truncate">{p.patient_email || 'No email provided'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{p.patient_phone || 'No phone provided'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-tealmed-600" />
                    <span>Last visit: <strong className="text-slate-800">{p.last_appointment_date || 'N/A'}</strong></span>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs font-bold text-tealmed-800 bg-tealmed-50/70 p-3 rounded-2xl border border-tealmed-100/80 group-hover:bg-tealmed-100/60 transition-colors">
                  <span className="flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-tealmed-700" /> View Profile & Records
                  </span>
                  <span className="text-[10px] font-extrabold bg-white px-2 py-0.5 rounded-full text-tealmed-900 border border-tealmed-200/80">
                    {p.total_appointments || 1} Consult(s)
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
