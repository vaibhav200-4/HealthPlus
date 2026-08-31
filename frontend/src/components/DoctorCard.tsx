import React from 'react';
import { Doctor } from '../types';
import { getDoctorImage } from '../utils/doctorImages';
import { Stethoscope, Calendar, Clock, Star, MapPin, IndianRupee, Navigation, Phone, ExternalLink } from 'lucide-react';

interface DoctorCardProps {
  doctor: Doctor;
  hospitalName?: string;
  onBook: (doctor: Doctor) => void;
  onViewDetails?: (doctor: Doctor) => void;
}

export const DoctorCard: React.FC<DoctorCardProps> = ({
  doctor,
  hospitalName,
  onBook,
  onViewDetails
}) => {
  const imageUrl = getDoctorImage(doctor);
  const isExternal = doctor.source === 'external';

  // Format distance
  const formatDistance = (meters?: number) => {
    if (meters == null) return null;
    if (meters >= 1000) {
      return `${(meters / 1000).toFixed(1)} km away`;
    }
    return `${Math.round(meters)} m away`;
  };

  const distanceText = formatDistance(doctor.distance_meters);

  // Google Maps directions URL scheme
  const googleMapsDirectionsUrl =
    doctor.latitude != null && doctor.longitude != null
      ? `https://www.google.com/maps/dir/?api=1&destination=${doctor.latitude},${doctor.longitude}`
      : null;

  return (
    <div className={`bg-white rounded-2xl border ${isExternal ? 'border-slate-300/80 bg-slate-50/40' : 'border-slate-200/80'} shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col justify-between group`}>
      <div>
        {/* Image & Badges Header */}
        <div className="relative h-48 bg-gradient-to-tr from-slate-100 to-medical-50 overflow-hidden">
          <img
            src={imageUrl}
            alt={doctor.name}
            className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              (e.target as HTMLImageElement).src = imageUrl;
            }}
          />

          {/* Specialty Badge */}
          <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-md px-3 py-1 rounded-full text-xs font-semibold text-medical-700 shadow-sm border border-white">
            {doctor.specialization}
          </div>

          {/* External or Bookable Badge */}
          {isExternal ? (
            <div className="absolute top-3 left-3 bg-amber-500/95 backdrop-blur-md px-2.5 py-1 rounded-full text-[10px] font-bold text-white shadow-sm flex items-center gap-1">
              <span>External Clinic</span>
            </div>
          ) : (
            <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-2.5 py-1 rounded-lg text-xs font-medium text-white flex items-center gap-1">
              <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
              <span>{doctor.rating || 4.9} ({doctor.total_reviews || 20}+ reviews)</span>
            </div>
          )}
        </div>

        {/* Doctor Info */}
        <div className="p-5 space-y-3">
          <div>
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-lg font-bold text-slate-900 group-hover:text-medical-600 transition-colors line-clamp-1">
                {doctor.name}
              </h3>
              {distanceText && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-tealmed-50 text-tealmed-700 text-[11px] font-bold border border-tealmed-200/60 flex-shrink-0">
                  <Navigation className="w-3 h-3" />
                  {distanceText}
                </span>
              )}
            </div>
            <p className="text-xs font-medium text-slate-500 truncate">
              {doctor.degree} • {doctor.designation}
            </p>
          </div>

          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-medical-500 flex-shrink-0" />
              <span>{doctor.experience_years} Years Experience</span>
            </div>

            {(hospitalName || doctor.hospital_name || doctor.address) && (
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-medical-500 flex-shrink-0" />
                <span className="truncate">
                  {doctor.address || hospitalName || doctor.hospital_name}
                </span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-medical-500 flex-shrink-0" />
              <span className="truncate">{doctor.availability || 'Mon-Sat, 10 AM - 2 PM'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Fee & Action Buttons */}
      <div className="p-5 pt-3 flex flex-col gap-2.5 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              {isExternal ? 'Status' : 'Consultation Fee'}
            </span>
            {isExternal ? (
              <span className="text-xs font-semibold text-slate-500">Not on HealthPulse</span>
            ) : (
              <span className="text-base font-bold text-slate-900 flex items-center">
                <IndianRupee className="w-4 h-4 text-slate-700" />
                {doctor.consultation_fee}
              </span>
            )}
          </div>

          {/* Get Directions Button */}
          {googleMapsDirectionsUrl && (
            <a
              href={googleMapsDirectionsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 font-bold text-xs border border-slate-200 shadow-sm transition-all hover:scale-[1.02]"
              title="Open Directions in Google Maps"
            >
              <Navigation className="w-3.5 h-3.5 text-medical-600 fill-medical-600" />
              <span>Directions</span>
            </a>
          )}
        </div>

        {/* Main Action Button */}
        {isExternal ? (
          doctor.phone ? (
            <a
              href={`tel:${doctor.phone}`}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
            >
              <Phone className="w-3.5 h-3.5" />
              Contact Clinic ({doctor.phone})
            </a>
          ) : (
            <button
              disabled
              className="w-full flex items-center justify-center gap-1.5 px-4 py-2.5 bg-slate-200 text-slate-500 font-semibold text-xs rounded-xl cursor-not-allowed"
            >
              Contact Info Unavailable
            </button>
          )
        ) : (
          <button
            onClick={() => onBook(doctor)}
            className="w-full flex items-center justify-center gap-1.5 px-4 py-2.5 bg-medical-600 hover:bg-medical-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-medical-500/20 hover:scale-[1.01] transition-all"
          >
            <Calendar className="w-3.5 h-3.5" />
            Book Clinic Visit
          </button>
        )}
      </div>
    </div>
  );
};
