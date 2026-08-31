import React from 'react';
import { DoctorIllustration } from './DoctorIllustration';
import { Stethoscope } from 'lucide-react';

interface DoctorPortalHeroProps {
  badgeText?: string;
  badgeIcon?: React.ReactNode;
  title: string;
  subtitle?: string;
  metadata?: Array<{ icon?: React.ReactNode; label: string }>;
  actions?: React.ReactNode;
  showIllustration?: boolean;
}

export const DoctorPortalHero: React.FC<DoctorPortalHeroProps> = ({
  badgeText = 'Attending Specialist Portal',
  badgeIcon = <Stethoscope className="w-3.5 h-3.5 text-tealmed-700" />,
  title,
  subtitle,
  metadata,
  actions,
  showIllustration = false
}) => {
  return (
    <div className="relative bg-gradient-to-r from-tealmed-50/90 via-emerald-50/60 to-white rounded-3xl p-6 sm:p-8 border border-tealmed-100 shadow-sm overflow-hidden transition-all">
      {/* Subtle Background Pattern Accent */}
      <div className="absolute right-0 top-0 w-96 h-96 bg-gradient-to-bl from-tealmed-200/20 via-emerald-100/30 to-transparent rounded-full blur-2xl pointer-events-none -mr-20 -mt-20"></div>

      <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Left Side: Doctor Vector Illustration & Main Content */}
        <div className="flex flex-col sm:flex-row items-center sm:items-start text-center sm:text-left gap-5 flex-1">
          {showIllustration && (
            <div className="flex-shrink-0">
              <DoctorIllustration className="w-28 h-28 sm:w-36 sm:h-36" />
            </div>
          )}

          <div className="space-y-2 flex-1">
            {badgeText && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-white/80 rounded-full text-xs font-bold text-tealmed-800 border border-tealmed-200/80 shadow-xs">
                {badgeIcon}
                <span>{badgeText}</span>
              </div>
            )}

            <h1 className="text-2xl sm:text-3xl lg:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {title}
            </h1>

            {subtitle && (
              <p className="text-xs sm:text-sm font-medium text-slate-600 max-w-2xl leading-relaxed">
                {subtitle}
              </p>
            )}

            {/* Optional Metadata Row */}
            {metadata && metadata.length > 0 && (
              <div className="pt-2 flex flex-wrap items-center justify-center sm:justify-start gap-2.5 text-xs text-slate-600">
                {metadata.map((item, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-tealmed-200/60 font-semibold text-slate-700 shadow-2xs"
                  >
                    {item.icon}
                    {item.label}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side Action Buttons */}
        {actions && (
          <div className="flex flex-wrap items-center justify-center sm:justify-end gap-3 flex-shrink-0 w-full md:w-auto">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};
