import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { DoctorNavbar } from './DoctorNavbar';
import { AdminNavbar } from './AdminNavbar';
import { 
  HeartPulse, 
  Calendar, 
  User as UserIcon, 
  Bot, 
  LogOut, 
  Menu, 
  X,
  Stethoscope,
  MessageSquare
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isDoctor, isAdmin } = useAuth();
  const { setIsOpen } = useChat();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Render role-specific navigation bars
  if (isDoctor) {
    return <DoctorNavbar />;
  }

  if (isAdmin) {
    return <AdminNavbar />;
  }

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-medical-600 to-medical-400 flex items-center justify-center text-white shadow-md shadow-medical-500/20 group-hover:scale-105 transition-transform duration-300">
            <HeartPulse className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-medical-900 via-medical-700 to-tealmed-700 bg-clip-text text-transparent">
              HealthPulse
            </span>
            <span className="block text-[10px] uppercase tracking-wider text-medical-600 font-bold -mt-1">
              Smart Healthcare
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 font-medium text-sm text-slate-600">
          <Link
            to="/"
            className={`px-3.5 py-2 rounded-lg transition-colors ${
              isActive('/') ? 'bg-medical-50 text-medical-700 font-semibold' : 'hover:text-medical-600 hover:bg-slate-50'
            }`}
          >
            Home
          </Link>
          <Link
            to="/doctors"
            className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isActive('/doctors') ? 'bg-medical-50 text-medical-700 font-semibold' : 'hover:text-medical-600 hover:bg-slate-50'
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            Find Doctors
          </Link>

          {user && (
            <>
              <Link
                to="/dashboard"
                className={`px-3.5 py-2 rounded-lg transition-colors ${
                  isActive('/dashboard') ? 'bg-medical-50 text-medical-700 font-semibold' : 'hover:text-medical-600 hover:bg-slate-50'
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/my-appointments"
                className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
                  isActive('/my-appointments') ? 'bg-medical-50 text-medical-700 font-semibold' : 'hover:text-medical-600 hover:bg-slate-50'
                }`}
              >
                <Calendar className="w-4 h-4" />
                Appointments
              </Link>
              <Link
                to="/chat-history"
                className={`px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
                  isActive('/chat-history') ? 'bg-medical-50 text-medical-700 font-semibold' : 'hover:text-medical-600 hover:bg-slate-50'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                Chat History
              </Link>
            </>
          )}
        </nav>

        {/* User CTA & AI Assistant Trigger */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-tealmed-500 to-medical-500 text-white font-medium text-sm shadow-md shadow-tealmed-500/20 hover:opacity-95 transition-all hover:scale-[1.02]"
          >
            <Bot className="w-4 h-4 animate-bounce" />
            AI Assistant
          </button>

          {user ? (
            <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
              <Link
                to="/profile"
                className="flex items-center gap-2 text-sm text-slate-700 font-medium hover:text-medical-600"
              >
                <div className="w-8 h-8 rounded-full bg-medical-100 text-medical-700 flex items-center justify-center font-bold text-sm border border-medical-200">
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="max-w-[120px] truncate">{user.name}</span>
              </Link>
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
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-semibold text-medical-700 hover:bg-medical-50 rounded-xl transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 text-sm font-semibold text-white bg-medical-600 hover:bg-medical-700 rounded-xl shadow-md shadow-medical-500/20 transition-all"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>

        {/* Mobile menu button */}
        <div className="md:hidden flex items-center gap-2">
          <button
            onClick={() => setIsOpen(true)}
            className="p-2 rounded-lg bg-tealmed-500 text-white shadow-sm"
          >
            <Bot className="w-5 h-5" />
          </button>
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
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Home
          </Link>
          <Link
            to="/doctors"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
          >
            Find Doctors
          </Link>

          {user && (
            <>
              <Link
                to="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
              >
                Dashboard
              </Link>
              <Link
                to="/my-appointments"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
              >
                My Appointments
              </Link>
              <Link
                to="/chat-history"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
              >
                Chat History
              </Link>
              <Link
                to="/profile"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
              >
                Profile & Settings
              </Link>
            </>
          )}

          <div className="pt-2 border-t border-slate-100 flex flex-col gap-2">
            {user ? (
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
            ) : (
              <div className="flex flex-col gap-2 pt-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 font-semibold text-medical-700 border border-medical-200 rounded-xl"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 font-semibold text-white bg-medical-600 rounded-xl"
                >
                  Create Account
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
