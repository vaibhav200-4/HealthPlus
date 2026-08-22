import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  Stethoscope, 
  Building2, 
  Users, 
  ClipboardList, 
  CalendarClock, 
  MessageSquare, 
  LogOut, 
  Menu, 
  X 
} from 'lucide-react';

export const AdminNavbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-slate-900 text-white border-b border-slate-800 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Admin Brand Logo */}
        <Link to="/admin" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-400 flex items-center justify-center text-slate-950 font-bold shadow-md group-hover:scale-105 transition-transform duration-300">
            <ShieldAlert className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-amber-400 via-amber-200 to-white bg-clip-text text-transparent">
              HealthPulse
            </span>
            <span className="block text-[10px] uppercase tracking-wider text-amber-400 font-bold -mt-1">
              Admin Portal
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 font-medium text-xs text-slate-300">
          <Link
            to="/admin"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </Link>
          <Link
            to="/admin/doctors"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin/doctors') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            Doctors
          </Link>
          <Link
            to="/admin/hospitals"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin/hospitals') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <Building2 className="w-4 h-4" />
            Hospitals
          </Link>
          <Link
            to="/admin/users"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin/users') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <Users className="w-4 h-4" />
            Users
          </Link>
          <Link
            to="/admin/appointments"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin/appointments') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <ClipboardList className="w-4 h-4" />
            Appointments
          </Link>
          <Link
            to="/admin/schedules"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin/schedules') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <CalendarClock className="w-4 h-4" />
            Schedules
          </Link>
          <Link
            to="/admin/chats"
            className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/admin/chats') ? 'bg-amber-500/20 text-amber-400 font-semibold' : 'hover:text-white hover:bg-slate-800'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Chat Logs
          </Link>
        </nav>

        {/* Admin Info & Logout */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-3 pl-2 border-l border-slate-800">
            <span className="text-xs font-semibold text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded-full border border-amber-400/20">
              System Admin
            </span>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="p-2 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors"
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
            className="p-2 text-slate-400 hover:text-white rounded-lg"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-slate-900 px-4 pt-2 pb-6 space-y-2">
          <Link to="/admin" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Dashboard</Link>
          <Link to="/admin/doctors" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Doctors</Link>
          <Link to="/admin/hospitals" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Hospitals</Link>
          <Link to="/admin/users" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Users</Link>
          <Link to="/admin/appointments" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Appointments</Link>
          <Link to="/admin/schedules" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Schedules</Link>
          <Link to="/admin/chats" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800 text-sm">Chat Logs</Link>
          <div className="pt-2 border-t border-slate-800">
            <button
              onClick={() => {
                logout();
                setMobileMenuOpen(false);
                navigate('/login');
              }}
              className="w-full text-left px-3 py-2 text-rose-400 text-sm font-medium hover:bg-slate-800 rounded-lg"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
