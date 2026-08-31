import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Stethoscope, 
  Calendar, 
  Clock, 
  Users, 
  User as UserIcon, 
  LogOut, 
  Menu, 
  X,
  LayoutDashboard,
  Pill
} from 'lucide-react';

export const DoctorNavbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-2xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Doctor Brand Logo */}
        <Link to="/doctor/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-tealmed-600 to-tealmed-500 flex items-center justify-center text-white shadow-md shadow-tealmed-600/20 group-hover:scale-105 transition-transform duration-300">
            <Stethoscope className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight text-slate-900 group-hover:text-tealmed-700 transition-colors">
              HealthPulse
            </span>
            <span className="block text-[10px] uppercase tracking-wider text-tealmed-600 font-extrabold -mt-1">
              Doctor Portal
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-1 font-semibold text-xs text-slate-600">
          <Link
            to="/doctor/dashboard"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/dashboard')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <LayoutDashboard className={`w-4 h-4 ${isActive('/doctor/dashboard') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Dashboard
          </Link>

          <Link
            to="/doctor/appointments"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/appointments')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Calendar className={`w-4 h-4 ${isActive('/doctor/appointments') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Appointments
          </Link>

          <Link
            to="/doctor/sessions"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/sessions')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Stethoscope className={`w-4 h-4 ${isActive('/doctor/sessions') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Sessions
          </Link>

          <Link
            to="/doctor/prescriptions"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/prescriptions')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Pill className={`w-4 h-4 ${isActive('/doctor/prescriptions') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Rx
          </Link>

          <Link
            to="/doctor/schedule"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/schedule')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Clock className={`w-4 h-4 ${isActive('/doctor/schedule') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Schedule
          </Link>

          <Link
            to="/doctor/patients"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/patients') || location.pathname.startsWith('/doctor/patients/')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Users className={`w-4 h-4 ${isActive('/doctor/patients') || location.pathname.startsWith('/doctor/patients/') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Patients & Records
          </Link>

          <Link
            to="/doctor/profile"
            className={`px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 ${
              isActive('/doctor/profile')
                ? 'bg-tealmed-50 text-tealmed-800 font-bold border border-tealmed-200/60 shadow-2xs'
                : 'hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <UserIcon className={`w-4 h-4 ${isActive('/doctor/profile') ? 'text-tealmed-700' : 'text-slate-400'}`} />
            Profile
          </Link>
        </nav>

        {/* Doctor Info & Logout */}
        <div className="hidden lg:flex items-center gap-3">
          <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-tealmed-100 to-emerald-100 text-tealmed-800 flex items-center justify-center font-extrabold text-xs border border-tealmed-300/80 shadow-2xs">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'D'}
              </div>
              <span className="max-w-[140px] truncate">{user?.name || 'Doctor Account'}</span>
            </div>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="p-2 text-slate-400 hover:text-rose-600 rounded-xl hover:bg-rose-50 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile menu toggle */}
        <div className="lg:hidden flex items-center gap-2">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-100 transition-colors"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-6 space-y-2 shadow-xl animate-in fade-in slide-in-from-top-2">
          <Link
            to="/doctor/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/dashboard') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Dashboard
          </Link>
          <Link
            to="/doctor/appointments"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/appointments') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Appointments
          </Link>
          <Link
            to="/doctor/sessions"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/sessions') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Sessions
          </Link>
          <Link
            to="/doctor/prescriptions"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/prescriptions') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Rx Prescriptions
          </Link>
          <Link
            to="/doctor/schedule"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/schedule') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Schedule
          </Link>
          <Link
            to="/doctor/patients"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/patients') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Patients & Records
          </Link>
          <Link
            to="/doctor/profile"
            onClick={() => setMobileMenuOpen(false)}
            className={`block px-3 py-2.5 rounded-xl font-bold text-xs ${
              isActive('/doctor/profile') ? 'bg-tealmed-50 text-tealmed-800' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            Profile & Credentials
          </Link>
          <div className="pt-3 border-t border-slate-100">
            <button
              onClick={() => {
                logout();
                setMobileMenuOpen(false);
                navigate('/login');
              }}
              className="w-full text-left px-3 py-2.5 text-rose-600 font-bold text-xs hover:bg-rose-50 rounded-xl transition-colors"
            >
              Logout Account
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
