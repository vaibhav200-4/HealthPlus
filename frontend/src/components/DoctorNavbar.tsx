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
  FileText
} from 'lucide-react';

export const DoctorNavbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-tealmed-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Doctor Brand Logo */}
        <Link to="/doctor/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-tealmed-600 to-tealmed-400 flex items-center justify-center text-white shadow-md shadow-tealmed-500/20 group-hover:scale-105 transition-transform duration-300">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-tealmed-900 via-tealmed-700 to-medical-700 bg-clip-text text-transparent">
              HealthPulse
            </span>
            <span className="block text-[10px] uppercase tracking-wider text-tealmed-600 font-bold -mt-1">
              Doctor Portal
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 font-medium text-sm text-slate-600">
          <Link
            to="/doctor/dashboard"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/dashboard') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </Link>

          <Link
            to="/doctor/appointments"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/appointments') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <Calendar className="w-4 h-4" />
            Appointments
          </Link>

          <Link
            to="/doctor/sessions"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/sessions') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            Sessions
          </Link>

          <Link
            to="/doctor/prescriptions"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/prescriptions') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <Clock className="w-4 h-4" />
            Rx
          </Link>

          <Link
            to="/doctor/schedule"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/schedule') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <Clock className="w-4 h-4" />
            Schedule
          </Link>

          <Link
            to="/doctor/patients"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/patients') || location.pathname.startsWith('/doctor/patients/') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <Users className="w-4 h-4" />
            Patients & Records
          </Link>

          <Link
            to="/doctor/profile"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctor/profile') ? 'bg-tealmed-50 text-tealmed-700 font-semibold' : 'hover:text-tealmed-600 hover:bg-slate-50'
            }`}
          >
            <UserIcon className="w-4 h-4" />
            Profile
          </Link>
        </nav>

        {/* Doctor Info & Logout */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
            <div className="flex items-center gap-2 text-sm text-slate-700 font-medium">
              <div className="w-8 h-8 rounded-full bg-tealmed-100 text-tealmed-800 flex items-center justify-center font-bold text-sm border border-tealmed-200">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'D'}
              </div>
              <span className="max-w-[140px] truncate">{user?.name}</span>
            </div>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile menu button */}
        <div className="md:hidden flex items-center gap-2">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-600 hover:text-slate-900 rounded-lg"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-6 space-y-3 shadow-xl">
          <Link
            to="/doctor/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Dashboard
          </Link>
          <Link
            to="/doctor/appointments"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Appointments
          </Link>
          <Link
            to="/doctor/schedule"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Schedule
          </Link>
          <Link
            to="/doctor/patients"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Patients & Records
          </Link>
          <Link
            to="/doctor/profile"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Profile & Settings
          </Link>
          <div className="pt-2 border-t border-slate-100">
            <button
              onClick={() => {
                logout();
                setMobileMenuOpen(false);
                navigate('/login');
              }}
              className="w-full text-left px-3 py-2 text-rose-600 font-medium hover:bg-rose-50 rounded-lg"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
