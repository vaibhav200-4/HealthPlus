import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Prescription } from '../types';
import { Pill, User, Calendar, FileText, Activity } from 'lucide-react';

export const MyPrescriptionsPage: React.FC = () => {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrescriptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/prescriptions');
      setPrescriptions(res.data || []);
    } catch (err: any) {
      console.error('Failed to fetch patient prescriptions:', err);
      setError('Unable to load your prescriptions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-16">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-tealmed-700 via-medical-700 to-medical-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-10 -translate-y-10 w-72 h-72 bg-white/10 rounded-full blur-2xl pointer-events-none" />
        <div className="relative z-10 space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/15 backdrop-blur-md rounded-full text-xs font-bold tracking-wide">
            <Pill className="w-4 h-4 text-tealmed-300" /> My Prescriptions
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Your Digital Rx Prescriptions</h1>
          <p className="text-xs sm:text-sm text-slate-200 font-medium">
            Access prescribed medications, dosage instructions, and doctor advice anytime.
          </p>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="p-16 text-center text-xs text-slate-500 flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-tealmed-500 border-t-transparent rounded-full animate-spin" />
          <p className="font-semibold text-slate-600">Loading your medical prescriptions...</p>
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-3xl p-8 text-center space-y-3">
          <p className="font-bold text-sm">{error}</p>
          <button
            onClick={fetchPrescriptions}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors"
          >
            Retry Loading
          </button>
        </div>
      ) : prescriptions.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center text-slate-400 border border-slate-200 space-y-3 shadow-2xs">
          <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto text-slate-400">
            <Pill className="w-7 h-7" />
          </div>
          <p className="text-base font-bold text-slate-800">No Prescriptions Found</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            You don't have any active digital prescriptions issued by your attending doctors yet. When a doctor issues a prescription, it will appear here.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {prescriptions.map((p) => (
            <div
              key={p.id}
              className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs hover:shadow-md transition-all space-y-5 flex flex-col justify-between"
            >
              <div className="space-y-4">
                {/* Header info */}
                <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-tealmed-50 text-tealmed-700 flex items-center justify-center font-bold">
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-extrabold text-slate-900">{p.doctor_name || 'Attending Doctor'}</p>
                      <p className="text-[10px] text-slate-400 font-medium">Prescribing Physician</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5 bg-slate-50 px-3 py-1 rounded-xl border border-slate-200/60">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recent'}
                  </span>
                </div>

                {/* Prescribed Medications */}
                <div className="space-y-3">
                  <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-tealmed-600" />
                    Prescribed Medications ({p.items?.length || 0})
                  </p>
                  <div className="divide-y divide-slate-100 bg-slate-50/50 rounded-2xl p-3 border border-slate-100">
                    {p.items?.map((item, idx) => (
                      <div key={idx} className="py-2.5 first:pt-0 last:pb-0 flex justify-between items-start text-xs">
                        <div className="space-y-0.5">
                          <p className="font-extrabold text-slate-900 text-sm">{item.medicine_name}</p>
                          <p className="text-slate-600 font-medium text-xs">
                            {[item.dosage, item.frequency, item.duration].filter(Boolean).join(' • ')}
                          </p>
                        </div>
                        {item.instructions && (
                          <span className="text-[10px] font-bold bg-tealmed-100/80 text-tealmed-800 px-2.5 py-1 rounded-lg border border-tealmed-200/60 shrink-0 ml-2">
                            {item.instructions}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Doctor Advice / Notes */}
                {p.notes && (
                  <div className="bg-emerald-50/60 p-3.5 rounded-2xl border border-emerald-100 space-y-1">
                    <p className="text-[10px] font-extrabold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                      <FileText className="w-3 h-3 text-emerald-700" /> Doctor Advice & Instructions
                    </p>
                    <p className="text-slate-700 text-xs font-medium leading-relaxed">{p.notes}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
