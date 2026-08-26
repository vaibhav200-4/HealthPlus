import React from 'react';
import { Doctor } from '../types';
import { getDoctorImage } from '../utils/doctorImages';
import { Stethoscope, Calendar, Clock, Star, MapPin, IndianRupee } from 'lucide-react';

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

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col justify-between group">
      <div>
        {/* Image & Specialty Badge Header */}
        <div className="relative h-48 bg-gradient-to-tr from-slate-100 to-medical-50 overflow-hidden">
          <img
            src={imageUrl}
            alt={doctor.name}
            className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              (e.target as HTMLImageElement).src = imageUrl;
            }}
          />
          <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-md px-3 py-1 rounded-full text-xs font-semibold text-medical-700 shadow-sm border border-white">
            {doctor.specialization}
          </div>
          <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-2.5 py-1 rounded-lg text-xs font-medium text-white flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span>4.9 (120+ reviews)</span>
          </div>
        </div>

        {/* Doctor Content Info */}
        <div className="p-5 space-y-3">
          <div>
            <h3 className="text-lg font-bold text-slate-900 group-hover:text-medical-600 transition-colors">
              {doctor.name}
            </h3>
            <p className="text-xs font-medium text-slate-500">{doctor.degree} • {doctor.designation}</p>
          </div>

          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-medical-500 flex-shrink-0" />
              <span>{doctor.experience_years} Years Experience</span>
            </div>
            {hospitalName && (
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-medical-500 flex-shrink-0" />
                <span className="truncate">{hospitalName}</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-medical-500 flex-shrink-0" />
              <span className="truncate">{doctor.availability || 'Mon-Sat, 10 AM - 2 PM'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Fee & Action */}
      <div className="p-5 pt-0 flex items-center justify-between border-t border-slate-100 mt-2">
        <div>
          <span className="text-[11px] font-medium text-slate-400 block uppercase">Consultation Fee</span>
          <span className="text-base font-bold text-slate-900 flex items-center">
            <IndianRupee className="w-4 h-4 text-slate-700" />
            {doctor.consultation_fee}
          </span>
        </div>

        <button
          onClick={() => onBook(doctor)}
          className="flex items-center gap-1.5 px-4 py-2 bg-medical-600 hover:bg-medical-700 text-white font-semibold text-xs rounded-xl shadow-md shadow-medical-500/20 hover:scale-[1.02] transition-all"
        >
          <Calendar className="w-3.5 h-3.5" />
          Book Slot
        </button>
      </div>
    </div>
  );
};
