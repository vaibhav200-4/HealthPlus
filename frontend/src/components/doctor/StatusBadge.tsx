import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const normalized = (status || '').toLowerCase().trim();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  if (normalized === 'confirmed') {
    colorClasses = 'bg-sky-50 text-sky-800 border-sky-200/80';
  } else if (normalized === 'completed') {
    colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-200/80';
  } else if (normalized === 'cancelled') {
    colorClasses = 'bg-rose-50 text-rose-800 border-rose-200/80';
  } else if (normalized === 'pending') {
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-200/80';
  } else if (normalized === 'in_progress' || normalized === 'active') {
    colorClasses = 'bg-tealmed-50 text-tealmed-800 border-tealmed-200/80';
  }

  const paddingClasses = size === 'sm' ? 'px-2.5 py-0.5 text-[10px]' : 'px-3 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-extrabold uppercase rounded-full border shadow-2xs ${paddingClasses} ${colorClasses}`}>
      {status ? status.replace('_', ' ').toUpperCase() : 'UNKNOWN'}
    </span>
  );
};
