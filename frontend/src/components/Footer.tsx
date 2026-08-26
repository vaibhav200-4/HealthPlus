import React from 'react';
import { HeartPulse, Phone, Mail, MapPin, Shield, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 pt-16 pb-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          {/* Col 1 */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-medical-500 text-white flex items-center justify-center font-bold">
                <HeartPulse className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold text-white tracking-tight">HealthPulse</span>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              Empowering healthcare accessibility with intelligent AI scheduling, real-time availability, and verified top-tier specialists.
            </p>
            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-3 py-1.5 rounded-lg w-fit">
              <Shield className="w-4 h-4" /> HIPAA Compliant & Secure Data
            </div>
          </div>

          {/* Col 2 */}
          <div>
            <h4 className="text-white font-semibold text-sm tracking-wider uppercase mb-4">Quick Links</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/doctors" className="hover:text-medical-400 transition-colors">Search Doctors</Link></li>
              <li><Link to="/doctors?specialization=Cardiology" className="hover:text-medical-400 transition-colors">Cardiology Specialists</Link></li>
              <li><Link to="/doctors?specialization=Neurology" className="hover:text-medical-400 transition-colors">Neurology Department</Link></li>
              <li><Link to="/dashboard" className="hover:text-medical-400 transition-colors">Patient Dashboard</Link></li>
            </ul>
          </div>

          {/* Col 3 */}
          <div>
            <h4 className="text-white font-semibold text-sm tracking-wider uppercase mb-4">Hospitals Network</h4>
            <ul className="space-y-2.5 text-sm">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-medical-500 flex-shrink-0 mt-0.5" />
                <span>Sunrise Multispeciality Hospital</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-medical-500 flex-shrink-0 mt-0.5" />
                <span>Green Valley Medical Centre</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-medical-500 flex-shrink-0 mt-0.5" />
                <span>Central City Hospital</span>
              </li>
            </ul>
          </div>

          {/* Col 4 */}
          <div>
            <h4 className="text-white font-semibold text-sm tracking-wider uppercase mb-4">Emergency & Contact</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex items-center gap-3">
                <Phone className="w-4 h-4 text-medical-400" />
                <span>24/7 Helpline: +91-731-4001001</span>
              </li>
              <li className="flex items-center gap-3">
                <Mail className="w-4 h-4 text-medical-400" />
                <span>care@healthpulse.example</span>
              </li>
              <li className="flex items-center gap-3">
                <MapPin className="w-4 h-4 text-medical-400" />
                <span>Vijay Nagar Main Road, Indore, MP</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 text-xs text-center text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 HealthPulse Hospital System. All rights reserved.</p>
          <div className="flex gap-6">
            <span className="hover:text-slate-400 cursor-pointer">Privacy Policy</span>
            <span className="hover:text-slate-400 cursor-pointer">Terms of Service</span>
            <span className="hover:text-slate-400 cursor-pointer">AI Health Assistant</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
