import React, { useState, useEffect } from 'react';
import { Doctor, TimeSlot } from '../types';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../services/api';
import { TimeSlotPicker } from './TimeSlotPicker';
import { X, Calendar, User as UserIcon, Phone, Mail, FileText, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface AppointmentModalProps {
  doctor: Doctor | null;
  hospitalName?: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const AppointmentModal: React.FC<AppointmentModalProps> = ({
  doctor,
  hospitalName,
  isOpen,
  onClose,
  onSuccess
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [date, setDate] = useState<string>(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });

  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [loadingSlots, setLoadingSlots] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Form fields
  const [patientName, setPatientName] = useState(user?.name || '');
  const [patientPhone, setPatientPhone] = useState(user?.phone || '');
  const [patientEmail, setPatientEmail] = useState(user?.email || '');
  const [notes, setNotes] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setPatientName(user.name || '');
      setPatientPhone(user.phone || '');
      setPatientEmail(user.email || '');
    }
  }, [user]);

  useEffect(() => {
    if (doctor && date && isOpen) {
      fetchSlots();
    }
  }, [doctor, date, isOpen]);

  const fetchSlots = async () => {
    if (!doctor) return;
    setLoadingSlots(true);
    setErrorMsg(null);
    setSelectedSlot(null);
    try {
      const res = await api.get(`/schedules/doctor/${doctor.id}?date=${date}`);
      setSlots(res.data.slots || []);
    } catch (err) {
      console.error('Failed to fetch doctor slots:', err);
      showToast('Could not load slots for selected date', 'error');
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doctor || !selectedSlot) {
      setErrorMsg('Please select an available appointment time slot.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const payload = {
        doctor_id: doctor.id,
        doctor_name: doctor.name,
        hospital_name: hospitalName || 'Sunrise Hospital',
        date: date,
        start_time: selectedSlot.start_time,
        end_time: selectedSlot.end_time,
        patient_name: patientName,
        patient_phone: patientPhone,
        patient_email: patientEmail,
        notes: notes
      };

      const res = await api.post('/appointments', payload);

      if (res.data.success) {
        showToast('Appointment confirmed successfully!', 'success');
        if (onSuccess) onSuccess();
        onClose();
      } else {
        // Double booking failure response from server
        setErrorMsg(res.data.message || 'This slot is no longer available.');
        showToast(res.data.message || 'This slot is no longer available.', 'error');
        fetchSlots(); // Refresh slot availability
      }
    } catch (err: any) {
      console.error('Booking error:', err);
      const msg = err.response?.data?.detail || 'Failed to book appointment. Please try again.';
      setErrorMsg(msg);
      showToast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen || !doctor) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="p-5 bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-800 text-white flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-tealmed-300 tracking-wider">Appointment Booking</span>
            <h3 className="text-lg font-bold">{doctor.name}</h3>
            <p className="text-xs text-slate-300">{doctor.specialization} • {hospitalName || 'Hospital Partner'}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4">
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Date Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-medical-600" />
              Select Appointment Date
            </label>
            <input
              type="date"
              value={date}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:ring-2 focus:ring-medical-500 focus:bg-white transition-all"
              required
            />
          </div>

          {/* Available Slots */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Available Time Slots</label>
            <TimeSlotPicker
              slots={slots}
              selectedSlot={selectedSlot}
              onSelectSlot={(s) => {
                setSelectedSlot(s);
                setErrorMsg(null);
              }}
              loading={loadingSlots}
            />
          </div>

          {/* Patient Details */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Patient Details</h4>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Full Name</label>
              <div className="relative">
                <input
                  type="text"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-medical-500 focus:bg-white"
                  required
                />
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Phone Number</label>
                <div className="relative">
                  <input
                    type="tel"
                    value={patientPhone}
                    onChange={(e) => setPatientPhone(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-medical-500 focus:bg-white"
                    placeholder="+91-9876543210"
                    required
                  />
                  <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Email Address</label>
                <div className="relative">
                  <input
                    type="email"
                    value={patientEmail}
                    onChange={(e) => setPatientEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-medical-500 focus:bg-white"
                    required
                  />
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Symptoms / Notes (Optional)</label>
              <div className="relative">
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-medical-500 focus:bg-white"
                  placeholder="Describe your health symptoms or special instructions..."
                ></textarea>
                <FileText className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>
          </div>

          {/* Modal Actions */}
          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !selectedSlot}
              className="px-5 py-2.5 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-semibold text-sm shadow-md shadow-medical-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? 'Confirming...' : 'Confirm Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
