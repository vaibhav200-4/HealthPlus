/**
 * MOCK PAYMENT FLOW (UI SHOWCASE ONLY)
 * ------------------------------------
 * This component provides a simulated payment method selection & card entry screen
 * for demonstration purposes. 
 * NOTE: No real payment gateway, card storage, or backend payment API calls are used.
 */

import React, { useState, useEffect } from 'react';
import { Doctor, MockPaymentCard } from '../types';
import { 
  CreditCard, 
  Plus, 
  Check, 
  Lock, 
  ShieldCheck, 
  Info, 
  User, 
  Calendar
} from 'lucide-react';

export const INITIAL_MOCK_CARDS: MockPaymentCard[] = [
  {
    id: 'card-1',
    type: 'visa',
    cardNumberLast4: '4242',
    holderName: 'Alex Johnson',
    expiryMonth: '12',
    expiryYear: '28',
    isDefault: true
  },
  {
    id: 'card-2',
    type: 'mastercard',
    cardNumberLast4: '8888',
    holderName: 'Alex Johnson',
    expiryMonth: '09',
    expiryYear: '27'
  },
  {
    id: 'card-3',
    type: 'healthpulse',
    cardNumberLast4: '1092',
    holderName: 'Alex Johnson',
    expiryMonth: '05',
    expiryYear: '29'
  }
];

interface PaymentMethodStepProps {
  doctor: Doctor | null;
  selectedCardId: string;
  onSelectCardId: (id: string) => void;
  onValidationChange: (isValid: boolean) => void;
}

export const PaymentMethodStep: React.FC<PaymentMethodStepProps> = ({
  doctor,
  selectedCardId,
  onSelectCardId,
  onValidationChange
}) => {
  const [cards] = useState<MockPaymentCard[]>(INITIAL_MOCK_CARDS);
  const [isAddingNewCard, setIsAddingNewCard] = useState<boolean>(selectedCardId === 'new_card');

  // Add Card form state
  const [cardNumber, setCardNumber] = useState('');
  const [cardHolder, setCardHolder] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [saveForFuture, setSaveForFuture] = useState(true);

  // Form errors
  const [errors, setErrors] = useState<{
    cardNumber?: string;
    cardHolder?: string;
    expiry?: string;
    cvv?: string;
  }>({});

  // Auto-detect card brand
  const getCardBrand = (num: string) => {
    const cleaned = num.replace(/\s+/g, '');
    if (cleaned.startsWith('4')) return 'Visa';
    if (/^5[1-5]/.test(cleaned) || /^2[2-7]/.test(cleaned)) return 'Mastercard';
    if (/^3[47]/.test(cleaned)) return 'Amex';
    return 'Card';
  };

  // Format card number with spaces every 4 digits
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 16);
    const formatted = value.replace(/(.{4})/g, '$1 ').trim();
    setCardNumber(formatted);
  };

  // Format expiry MM/YY
  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '').slice(0, 4);
    if (value.length >= 3) {
      value = `${value.slice(0, 2)}/${value.slice(2)}`;
    }
    setExpiry(value);
  };

  // Handle CVV input (numbers only)
  const handleCvvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 4);
    setCvv(value);
  };

  // Validation logic
  useEffect(() => {
    if (!isAddingNewCard) {
      // Selecting a saved card is always valid
      onValidationChange(!!selectedCardId && selectedCardId !== 'new_card');
      setErrors({});
      return;
    }

    const rawNumber = cardNumber.replace(/\s+/g, '');
    const newErrors: typeof errors = {};

    if (!rawNumber) {
      newErrors.cardNumber = 'Card number is required';
    } else if (rawNumber.length < 15) {
      newErrors.cardNumber = 'Card number must be at least 15 digits';
    }

    if (!cardHolder.trim()) {
      newErrors.cardHolder = 'Name on card is required';
    }

    if (!expiry) {
      newErrors.expiry = 'Expiry required';
    } else if (!/^(0[1-9]|1[0-2])\/?([0-9]{2})$/.test(expiry)) {
      newErrors.expiry = 'Use MM/YY format';
    }

    if (!cvv) {
      newErrors.cvv = 'CVV required';
    } else if (cvv.length < 3) {
      newErrors.cvv = '3-4 digits';
    }

    setErrors(newErrors);
    const isValid = Object.keys(newErrors).length === 0;
    onValidationChange(isValid);
  }, [isAddingNewCard, selectedCardId, cardNumber, cardHolder, expiry, cvv, onValidationChange]);

  const handleSelectCard = (id: string) => {
    setIsAddingNewCard(id === 'new_card');
    onSelectCardId(id);
  };

  const consultationFee = doctor?.consultation_fee || 500;
  const platformFee = 0;
  const totalAmount = consultationFee + platformFee;

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* UI Showcase Notice Banner */}
      <div className="p-3 bg-amber-50 border border-amber-200/80 rounded-2xl flex items-start gap-2.5 text-xs text-amber-900 shadow-sm">
        <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold block text-amber-950">UI Showcase Payment Demo</span>
          <p className="text-amber-800 text-[11px] leading-relaxed">
            This is a mock payment flow for presentation purposes. No actual card charges or payment gateway processing will occur.
          </p>
        </div>
      </div>

      {/* Payment Method Selector Cards */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
          Select Payment Method
        </label>
        
        <div className="grid grid-cols-1 gap-2.5">
          {cards.map((card) => {
            const isSelected = selectedCardId === card.id && !isAddingNewCard;
            return (
              <div
                key={card.id}
                onClick={() => handleSelectCard(card.id)}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                  isSelected
                    ? 'border-medical-600 bg-medical-50/40 shadow-sm ring-1 ring-medical-500'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/80'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-7 rounded-lg flex items-center justify-center font-bold text-[11px] tracking-tighter ${
                    card.type === 'visa' 
                      ? 'bg-blue-950 text-white' 
                      : card.type === 'mastercard' 
                      ? 'bg-gradient-to-r from-red-600 to-amber-500 text-white' 
                      : 'bg-tealmed-700 text-white'
                  }`}>
                    {card.type === 'visa' && 'VISA'}
                    {card.type === 'mastercard' && 'MC'}
                    {card.type === 'healthpulse' && 'PULSE'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-800">
                        •••• •••• •••• {card.cardNumberLast4}
                      </span>
                      {card.isDefault && (
                        <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px] font-semibold">
                          Default
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500">
                      {card.holderName} • Exp {card.expiryMonth}/{card.expiryYear}
                    </p>
                  </div>
                </div>

                <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
                  isSelected ? 'border-medical-600 bg-medical-600 text-white' : 'border-slate-300 bg-white'
                }`}>
                  {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
              </div>
            );
          })}

          {/* Add New Card Button / Option */}
          <div
            onClick={() => handleSelectCard('new_card')}
            className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
              isAddingNewCard
                ? 'border-medical-600 bg-medical-50/40 shadow-sm ring-1 ring-medical-500'
                : 'border-dashed border-slate-300 bg-slate-50/50 hover:border-slate-400 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-7 rounded-lg border border-slate-200 bg-white flex items-center justify-center text-slate-500">
                <Plus className="w-4 h-4 text-medical-600" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-800 block">Add New Payment Card</span>
                <span className="text-[11px] text-slate-500">Credit or Debit card</span>
              </div>
            </div>

            <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
              isAddingNewCard ? 'border-medical-600 bg-medical-600 text-white' : 'border-slate-300 bg-white'
            }`}>
              {isAddingNewCard && <Check className="w-3 h-3 stroke-[3]" />}
            </div>
          </div>
        </div>
      </div>

      {/* Add New Card Form (Collapsible/Conditional) */}
      {isAddingNewCard && (
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between pb-1 border-b border-slate-200/80">
            <h5 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <CreditCard className="w-4 h-4 text-medical-600" />
              Card Details
            </h5>
            <span className="text-[10px] font-medium text-slate-500 bg-white px-2 py-0.5 rounded-md border border-slate-200">
              {getCardBrand(cardNumber)}
            </span>
          </div>

          {/* Card Number */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 mb-1">
              Card Number
            </label>
            <div className="relative">
              <input
                type="text"
                value={cardNumber}
                onChange={handleCardNumberChange}
                placeholder="4242 4242 4242 4242"
                className={`w-full pl-9 pr-3 py-2 bg-white border rounded-xl text-xs font-mono text-slate-800 focus:ring-2 focus:ring-medical-500 transition-all ${
                  errors.cardNumber ? 'border-rose-400 bg-rose-50/30' : 'border-slate-200'
                }`}
              />
              <CreditCard className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
            {errors.cardNumber && (
              <p className="text-[10px] text-rose-600 mt-1 font-medium">{errors.cardNumber}</p>
            )}
          </div>

          {/* Name on Card */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 mb-1">
              Name on Card
            </label>
            <div className="relative">
              <input
                type="text"
                value={cardHolder}
                onChange={(e) => setCardHolder(e.target.value)}
                placeholder="e.g. Alex Johnson"
                className={`w-full pl-9 pr-3 py-2 bg-white border rounded-xl text-xs text-slate-800 focus:ring-2 focus:ring-medical-500 transition-all ${
                  errors.cardHolder ? 'border-rose-400 bg-rose-50/30' : 'border-slate-200'
                }`}
              />
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
            {errors.cardHolder && (
              <p className="text-[10px] text-rose-600 mt-1 font-medium">{errors.cardHolder}</p>
            )}
          </div>

          {/* Expiry & CVV */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Expiry Date
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={expiry}
                  onChange={handleExpiryChange}
                  placeholder="MM/YY"
                  className={`w-full pl-9 pr-3 py-2 bg-white border rounded-xl text-xs font-mono text-slate-800 focus:ring-2 focus:ring-medical-500 transition-all ${
                    errors.expiry ? 'border-rose-400 bg-rose-50/30' : 'border-slate-200'
                  }`}
                />
                <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
              {errors.expiry && (
                <p className="text-[10px] text-rose-600 mt-1 font-medium">{errors.expiry}</p>
              )}
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                CVV / CVC
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={cvv}
                  onChange={handleCvvChange}
                  placeholder="123"
                  maxLength={4}
                  className={`w-full pl-9 pr-3 py-2 bg-white border rounded-xl text-xs font-mono text-slate-800 focus:ring-2 focus:ring-medical-500 transition-all ${
                    errors.cvv ? 'border-rose-400 bg-rose-50/30' : 'border-slate-200'
                  }`}
                />
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
              {errors.cvv && (
                <p className="text-[10px] text-rose-600 mt-1 font-medium">{errors.cvv}</p>
              )}
            </div>
          </div>

          {/* Save for future bookings toggle */}
          <div className="pt-2 flex items-center justify-between">
            <span className="text-xs font-medium text-slate-700">Save card for future bookings</span>
            <button
              type="button"
              onClick={() => setSaveForFuture(!saveForFuture)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                saveForFuture ? 'bg-medical-600' : 'bg-slate-300'
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                  saveForFuture ? 'translate-x-4 stroke-2' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
        </div>
      )}

      {/* Payment Summary Box */}
      <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
        <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-600">
          Payment Breakdown
        </h5>
        
        <div className="space-y-1.5 text-xs text-slate-600">
          <div className="flex justify-between">
            <span>Doctor Consultation Fee</span>
            <span className="font-semibold text-slate-800">₹{consultationFee}</span>
          </div>
          <div className="flex justify-between">
            <span>Booking & Convenience Fee</span>
            <span className="font-semibold text-tealmed-700 bg-tealmed-50 px-1.5 py-0.5 rounded text-[10px]">
              FREE
            </span>
          </div>
          <div className="pt-1.5 border-t border-slate-200 flex justify-between font-bold text-sm text-slate-900">
            <span>Total Payable</span>
            <span className="text-medical-700">₹{totalAmount}</span>
          </div>
        </div>

        <div className="pt-1.5 flex items-center gap-1.5 text-[10px] text-slate-500 font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-tealmed-600" />
          <span>Simulated 256-bit Encrypted Demonstration Checkout</span>
        </div>
      </div>
    </div>
  );
};
