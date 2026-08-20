import React from 'react';

export const SkeletonDoctorCard: React.FC = () => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-4 animate-pulse">
      <div className="h-44 bg-slate-200 rounded-xl"></div>
      <div className="space-y-2">
        <div className="h-5 bg-slate-200 rounded w-3/4"></div>
        <div className="h-3 bg-slate-200 rounded w-1/2"></div>
      </div>
      <div className="space-y-2 pt-2">
        <div className="h-3 bg-slate-200 rounded w-5/6"></div>
        <div className="h-3 bg-slate-200 rounded w-2/3"></div>
      </div>
      <div className="flex justify-between items-center pt-3 border-t border-slate-100">
        <div className="h-4 bg-slate-200 rounded w-1/4"></div>
        <div className="h-9 bg-slate-200 rounded-xl w-1/3"></div>
      </div>
    </div>
  );
};

export const SkeletonTableRow: React.FC = () => {
  return (
    <tr className="animate-pulse border-b border-slate-100">
      <td className="p-4"><div className="h-4 bg-slate-200 rounded w-24"></div></td>
      <td className="p-4"><div className="h-4 bg-slate-200 rounded w-32"></div></td>
      <td className="p-4"><div className="h-4 bg-slate-200 rounded w-20"></div></td>
      <td className="p-4"><div className="h-4 bg-slate-200 rounded w-16"></div></td>
      <td className="p-4"><div className="h-4 bg-slate-200 rounded w-12"></div></td>
    </tr>
  );
};
