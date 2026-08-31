import React from 'react';

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  description: string;
  iconBgColor?: string;
  iconTextColor?: string;
  accentBorderColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  label,
  value,
  description,
  iconBgColor = 'bg-tealmed-50',
  iconTextColor = 'text-tealmed-700',
  accentBorderColor = 'hover:border-tealmed-300'
}) => {
  return (
    <div className={`bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-3 transition-all duration-200 ${accentBorderColor} hover:shadow-md`}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{label}</span>
        <div className={`w-10 h-10 rounded-2xl ${iconBgColor} ${iconTextColor} flex items-center justify-center font-bold shadow-2xs`}>
          {icon}
        </div>
      </div>
      <div>
        <span className="text-3xl font-extrabold text-slate-900 block tracking-tight">{value}</span>
        <span className="text-xs text-slate-500 font-medium block mt-1">{description}</span>
      </div>
    </div>
  );
};
