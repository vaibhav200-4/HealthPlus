import React from 'react';
import { TimeSlot } from '../types';
import { Clock, Check } from 'lucide-react';

interface TimeSlotPickerProps {
  slots: TimeSlot[];
  selectedSlot: TimeSlot | null;
  onSelectSlot: (slot: TimeSlot) => void;
  loading: boolean;
}

export const TimeSlotPicker: React.FC<TimeSlotPickerProps> = ({
  slots,
  selectedSlot,
  onSelectSlot,
  loading
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 my-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-10 bg-slate-100 rounded-xl animate-pulse"></div>
        ))}
      </div>
    );
  }

  if (slots.length === 0) {
    return (
      <div className="text-center py-6 bg-slate-50 rounded-2xl border border-dashed border-slate-200 my-4 text-slate-500 text-xs">
        <Clock className="w-6 h-6 mx-auto text-slate-400 mb-1" />
        No slots available for this date. Please select another date.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 my-4">
      {slots.map((slot, idx) => {
        const isSelected = selectedSlot?.start_time === slot.start_time;
        const isDisabled = !slot.available;

        return (
          <button
            key={idx}
            type="button"
            disabled={isDisabled}
            onClick={() => onSelectSlot(slot)}
            className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-between transition-all duration-200 ${
              isSelected
                ? 'bg-medical-600 border-medical-600 text-white shadow-md shadow-medical-500/20 scale-[1.02]'
                : isDisabled
                ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed line-through opacity-70'
                : 'bg-white border-slate-200 text-slate-700 hover:border-medical-400 hover:bg-medical-50/50'
            }`}
          >
            <span>{slot.start_time}</span>
            {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
          </button>
        );
      })}
    </div>
  );
};
