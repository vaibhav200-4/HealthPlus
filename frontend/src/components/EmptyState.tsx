import React, { ReactNode } from 'react';
import { FolderOpen } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-10 text-center bg-slate-50/50 border-2 border-dashed border-slate-200 rounded-3xl my-6">
      <div className="w-16 h-16 rounded-2xl bg-white text-medical-600 flex items-center justify-center mb-4 shadow-sm border border-slate-100">
        {icon || <FolderOpen className="w-8 h-8 text-slate-400" />}
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-sm mb-6 leading-relaxed">{description}</p>
      {action}
    </div>
  );
};
