import React from 'react';

interface DoctorIllustrationProps {
  className?: string;
}

export const DoctorIllustration: React.FC<DoctorIllustrationProps> = ({ className = 'w-32 h-32 sm:w-40 sm:h-40' }) => {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      {/* Background Soft Glow & Organic Circle */}
      <div className="absolute inset-0 bg-gradient-to-br from-tealmed-100/80 via-emerald-100/60 to-tealmed-200/40 rounded-full blur-xs transform scale-105"></div>
      <div className="absolute inset-2 bg-gradient-to-tr from-white/90 to-tealmed-50 rounded-full border border-tealmed-200/50 shadow-inner"></div>

      {/* SVG Doctor Vector Art - Professional Semi-Realistic Flat Design */}
      <svg
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full relative z-10 drop-shadow-md"
      >
        <defs>
          <linearGradient id="docCoatGrad" x1="60" y1="100" x2="140" y2="190" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#F1F5F9" />
          </linearGradient>
          <linearGradient id="scrubsGrad" x1="85" y1="105" x2="115" y2="150" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0F766E" />
            <stop offset="100%" stopColor="#0D9488" />
          </linearGradient>
          <linearGradient id="bgCircleGrad" x1="20" y1="20" x2="180" y2="180" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#CCFBF1" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#E6FFFA" stopOpacity="0.4" />
          </linearGradient>
          <linearGradient id="tabletGrad" x1="120" y1="120" x2="160" y2="170" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0F172A" />
            <stop offset="100%" stopColor="#1E293B" />
          </linearGradient>
        </defs>

        {/* Soft Background Accent Circles & Medical Geometry */}
        <circle cx="100" cy="100" r="86" fill="url(#bgCircleGrad)" />
        <circle cx="100" cy="100" r="74" stroke="#99F6E4" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.6" fill="none" />

        {/* Subtle Healthcare Cross & Pulse Wave Accents */}
        <path d="M154 44h-4v-4h-3v4h-4v3h4v4h3v-4h4v-3z" fill="#0D9488" opacity="0.6" />
        <path d="M38 145h-3v-3h-2v3h-3v2h3v3h2v-3h3v-2z" fill="#14B8A6" opacity="0.5" />
        <path d="M26 100h18l4-7 6 15 7-20 5 16 4-4h18" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.22" />

        {/* Doctor Body Torso Base Shadow */}
        <path d="M48 188c0-28 20-45 52-45s52 17 52 45v12H48v-12z" fill="#E2E8F0" opacity="0.4" />

        {/* Inner V-Neck Scrubs */}
        <path d="M84 104l16 26 16-26v46H84v-46z" fill="url(#scrubsGrad)" />
        <path d="M90 104c3 3 17 3 20 0" stroke="#5EEAD4" strokeWidth="1.5" fill="none" />

        {/* Doctor Face & Neck */}
        <path d="M88 84h24v24c0 4-4 8-12 8s-12-4-12-8V84z" fill="#F3D5C8" />
        <path d="M88 94c5 4 19 4 24 0" fill="#E8BBA8" opacity="0.4" />

        {/* Face Contour */}
        <path d="M78 62c0-14 10-24 22-24s22 10 22 24c0 14-8 24-22 24S78 76 78 62z" fill="#F7E2D6" />

        {/* Hair - Professional Modern Style */}
        <path d="M76 60c0-16 12-25 24-25 14 0 24 8 25 22 1 1-3-4-8-5-7-2-18 0-23 4-3 2-10 11-12 11-2 0-6-3-6-7z" fill="#1E293B" />
        <path d="M77 60c0 5 1 9 3 12" stroke="#1E293B" strokeWidth="3" strokeLinecap="round" />
        <path d="M123 60c0 5-1 9-3 12" stroke="#1E293B" strokeWidth="3" strokeLinecap="round" />
        <circle cx="77" cy="67" r="3.5" fill="#F3D5C8" />
        <circle cx="123" cy="67" r="3.5" fill="#F3D5C8" />

        {/* Professional Semi-Realistic Facial Features */}
        <path d="M85 58c2-2 6-2 9 0" stroke="#334155" strokeWidth="2" strokeLinecap="round" />
        <path d="M106 58c2-2 6-2 9 0" stroke="#334155" strokeWidth="2" strokeLinecap="round" />
        <path d="M86 64c2 1.5 5 1.5 7 0" stroke="#0F172A" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M107 64c2 1.5 5 1.5 7 0" stroke="#0F172A" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M100 63v6l-2 2" stroke="#D9A593" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M94 76c3 2.5 9 2.5 12 0" stroke="#B91C1C" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.75" />

        {/* Stethoscope */}
        <path d="M80 94c-2 16 8 36 20 36 12 0 22-20 20-36" stroke="#334155" strokeWidth="3.5" strokeLinecap="round" fill="none" />
        <path d="M80 94v6" stroke="#94A3B8" strokeWidth="4" strokeLinecap="round" />
        <path d="M120 94v6" stroke="#94A3B8" strokeWidth="4" strokeLinecap="round" />
        <path d="M100 130v8" stroke="#334155" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="100" cy="141" r="5.5" fill="#0F766E" stroke="#E2E8F0" strokeWidth="2" />
        <circle cx="100" cy="141" r="2" fill="#99F6E4" />

        {/* White Doctor Coat */}
        <path d="M48 188c0-26 18-42 34-46l18 36H56l-8 10z" fill="url(#docCoatGrad)" stroke="#CBD5E1" strokeWidth="1" />
        <path d="M152 188c0-26-18-42-34-46l-18 36h44l8 10z" fill="url(#docCoatGrad)" stroke="#CBD5E1" strokeWidth="1" />
        <path d="M82 104l18 42-20-10-18-20c4-7 12-10 20-12z" fill="#FFFFFF" stroke="#94A3B8" strokeWidth="1" />
        <path d="M118 104l-18 42 20-10 18-20c-4-7-12-10-20-12z" fill="#FFFFFF" stroke="#94A3B8" strokeWidth="1" />

        {/* Coat Pocket & Pen Clip */}
        <rect x="62" y="152" width="16" height="22" rx="3" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1" />
        <line x1="66" y1="148" x2="66" y2="157" stroke="#0D9488" strokeWidth="2" strokeLinecap="round" />
        <circle cx="66" cy="147" r="1.5" fill="#0F766E" />

        {/* Medical Digital Tablet in Hand */}
        <g transform="rotate(-6 142 145)">
          <rect x="126" y="120" width="38" height="54" rx="5" fill="url(#tabletGrad)" stroke="#475569" strokeWidth="1.5" />
          <rect x="129" y="124" width="32" height="46" rx="3" fill="#0F766E" />
          <rect x="133" y="128" width="14" height="4" rx="1" fill="#99F6E4" />
          <line x1="133" y1="136" x2="153" y2="136" stroke="#CCFBF1" strokeWidth="2" strokeLinecap="round" />
          <line x1="133" y1="142" x2="157" y2="142" stroke="#5EEAD4" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="133" y1="147" x2="149" y2="147" stroke="#5EEAD4" strokeWidth="1.5" strokeLinecap="round" />
          <path d="M132 159l4-3 3 6 4-9 3 7 4-3h6" stroke="#34D399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <path d="M124 150c4 0 7 2 7 6s-3 6-7 6" stroke="#F3D5C8" strokeWidth="4" strokeLinecap="round" fill="none" />
        </g>
      </svg>
    </div>
  );
};

