import React, { useState, useEffect } from 'react';
import { Doctor, TimeSlot } from '../types';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../services/api';
import { TimeSlotPicker } from './TimeSlotPicker';
import { PaymentMethodStep } from './PaymentMethodStep';
import { 
  X, 
  Calendar, 
  User as UserIcon, 
  Phone, 
  Mail, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowLeft, 
  CreditCard, 
  Check, 
  Sparkles 
} from 'lucide-react';

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

  // Wizard Step State: 1 = Details, 2 = Payment Method, 3 = Confirmation Success
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

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

  // Payment Step State (Frontend Mock UI only)
  const [selectedCardId, setSelectedCardId] = useState<string>('card-1');
  const [isPaymentValid, setIsPaymentValid] = useState<boolean>(true);
  const [mockTxnId, setMockTxnId] = useState<string>('');

  useEffect(() => {
    if (user) {
      setPatientName(user.name || '');
      setPatientPhone(user.phone || '');
      setPatientEmail(user.email || '');
    }
  }, [user]);

  useEffect(() => {
    if (isOpen) {
      // Reset step and error when modal opens
      setCurrentStep(1);
      setErrorMsg(null);
    }
  }, [isOpen]);

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

  // Move from Step 1 to Step 2 (Validation)
  const handleProceedToPayment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!doctor || !selectedSlot) {
      setErrorMsg('Please select an available appointment time slot.');
      return;
    }
    if (!patientName.trim()) {
      setErrorMsg('Please enter patient full name.');
      return;
    }
    if (!patientPhone.trim()) {
      setErrorMsg('Please enter patient phone number.');
      return;
    }
    if (!patientEmail.trim()) {
      setErrorMsg('Please enter patient email address.');
      return;
    }

    setErrorMsg(null);
    setCurrentStep(2);
  };

  // Submit appointment & simulate payment completion (Step 2 -> Step 3)
  const handleConfirmAndPay = async () => {
    if (!doctor || !selectedSlot) return;

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

      // Simulate a brief payment processing delay for realistic UX
      await new Promise((resolve) => setTimeout(resolve, 800));

      const res = await api.post('/appointments', payload);

      if (res.data.success) {
        // Generate mock transaction ID for showcase UI
        const txn = 'PAY-' + Math.random().toString(36).substring(2, 8).toUpperCase();
        setMockTxnId(txn);
        showToast('Payment successful & appointment confirmed!', 'success');
        if (onSuccess) onSuccess();
        setCurrentStep(3);
      } else {
        setErrorMsg(res.data.message || 'This slot is no longer available.');
        showToast(res.data.message || 'This slot is no longer available.', 'error');
        setCurrentStep(1); // Return to step 1 to re-select
        fetchSlots();
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
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden max-h-[92vh] flex flex-col">
        
        {/* Modal Header */}
        <div className="p-5 bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-800 text-white flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-tealmed-300 tracking-wider">
              Appointment Booking
            </span>
            <h3 className="text-lg font-bold">{doctor.name}</h3>
            <p className="text-xs text-slate-300">
              {doctor.specialization} • {hospitalName || 'Hospital Partner'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Navigation Indicator Bar */}
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-200/80 flex items-center justify-between text-xs">
          {/* Step 1: Details */}
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] ${
              currentStep === 1 
                ? 'bg-medical-600 text-white' 
                : currentStep > 1 
                ? 'bg-tealmed-600 text-white' 
                : 'bg-slate-200 text-slate-600'
            }`}>
              {currentStep > 1 ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : '1'}
            </div>
            <span className={`font-semibold ${currentStep === 1 ? 'text-medical-900 font-bold' : 'text-slate-600'}`}>
              Details
            </span>
          </div>

          <div className="flex-1 h-[2px] mx-3 bg-slate-200">
            <div className={`h-full bg-tealmed-500 transition-all duration-300 ${
              currentStep === 1 ? 'w-0' : currentStep === 2 ? 'w-1/2' : 'w-full'
            }`} />
          </div>

          {/* Step 2: Payment */}
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] ${
              currentStep === 2 
                ? 'bg-medical-600 text-white' 
                : currentStep > 2 
                ? 'bg-tealmed-600 text-white' 
                : 'bg-slate-200 text-slate-600'
            }`}>
              {currentStep > 2 ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : '2'}
            </div>
            <span className={`font-semibold ${currentStep === 2 ? 'text-medical-900 font-bold' : 'text-slate-600'}`}>
              Payment
            </span>
          </div>

          <div className="flex-1 h-[2px] mx-3 bg-slate-200">
            <div className={`h-full bg-tealmed-500 transition-all duration-300 ${
              currentStep === 3 ? 'w-full' : 'w-0'
            }`} />
          </div>

          {/* Step 3: Confirmation */}
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] ${
              currentStep === 3 
                ? 'bg-tealmed-600 text-white' 
                : 'bg-slate-200 text-slate-600'
            }`}>
              3
            </div>
            <span className={`font-semibold ${currentStep === 3 ? 'text-medical-900 font-bold' : 'text-slate-600'}`}>
              Confirmation
            </span>
          </div>
        </div>

        {/* Modal Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* STEP 1: Details & Slot Selection */}
          {currentStep === 1 && (
            <form onSubmit={handleProceedToPayment} className="space-y-4">
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

              {/* Step 1 Actions */}
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
                  disabled={!selectedSlot}
                  className="px-5 py-2.5 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-semibold text-sm shadow-md shadow-medical-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <span>Proceed to Payment</span>
                  <CreditCard className="w-4 h-4" />
                </button>
              </div>
            </form>
          )}

          {/* STEP 2: Payment Method Selection / Form */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <PaymentMethodStep
                doctor={doctor}
                selectedCardId={selectedCardId}
                onSelectCardId={(id) => setSelectedCardId(id)}
                onValidationChange={(isValid) => setIsPaymentValid(isValid)}
              />

              {/* Step 2 Actions */}
              <div className="pt-4 flex items-center justify-between border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  disabled={submitting}
                  className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 flex items-center gap-1.5"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Details</span>
                </button>
                
                <button
                  type="button"
                  onClick={handleConfirmAndPay}
                  disabled={submitting || !isPaymentValid}
                  className="px-5 py-2.5 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-semibold text-sm shadow-md shadow-medical-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Processing Payment...</span>
                    </>
                  ) : (
                    <>
                      <span>Pay & Confirm Booking</span>
                      <Sparkles className="w-4 h-4 text-amber-300" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Success Confirmation Screen */}
          {currentStep === 3 && (
            <div className="py-4 text-center space-y-4 animate-in fade-in zoom-in-95 duration-300">
              <div className="w-16 h-16 bg-tealmed-100 rounded-full flex items-center justify-center mx-auto text-tealmed-600 shadow-md">
                <CheckCircle2 className="w-10 h-10 stroke-[2.5]" />
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-tealmed-600 tracking-wider">
                  Payment Successful (Simulated)
                </span>
                <h4 className="text-xl font-bold text-slate-900 mt-0.5">
                  Appointment Confirmed!
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Your slot has been reserved. A confirmation copy has been sent to your email.
                </p>
              </div>

              {/* Summary Card */}
              <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl text-left space-y-2.5">
                <div className="flex justify-between items-start pb-2 border-b border-slate-200">
                  <div>
                    <h5 className="text-sm font-bold text-slate-900">{doctor.name}</h5>
                    <p className="text-xs text-slate-500">{doctor.specialization}</p>
                  </div>
                  <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded-md uppercase">
                    Paid • ₹{doctor.consultation_fee || 500}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Date</span>
                    <span className="font-semibold text-slate-800">{date}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Time Slot</span>
                    <span className="font-semibold text-slate-800">{selectedSlot?.start_time} - {selectedSlot?.end_time}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Patient</span>
                    <span className="font-semibold text-slate-800">{patientName}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Txn Reference</span>
                    <span className="font-mono text-[11px] font-semibold text-slate-800">{mockTxnId}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                  }}
                  className="w-full py-3 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-sm shadow-md shadow-medical-500/20 transition-all"
                >
                  Done & Close
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
