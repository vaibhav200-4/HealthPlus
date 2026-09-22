import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { useFloatingUI } from '../context/FloatingUIContext';
import { 
  HeartPulse, 
  Bot, 
  LogOut, 
  Menu, 
  X,
  ShieldCheck
} from 'lucide-react';

interface HospitalAdminNavbarProps {
  onToggleMobileSidebar?: () => void;
  isMobileSidebarOpen?: boolean;
}

export const HospitalAdminNavbar: React.FC<HospitalAdminNavbarProps> = ({
  onToggleMobileSidebar,
  isMobileSidebarOpen = false
}) => {
  const { user, logout } = useAuth();
  const { setIsOpen: setChatContextOpen } = useChat();
  const { openChat } = useFloatingUI();
  const navigate = useNavigate();

  const handleOpenChat = () => {
    openChat();
    setChatContextOpen(true);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-900 text-white border-b border-slate-800 shadow-md h-16 shrink-0">
      <div className="w-full px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Left Side: Mobile Menu Button & Brand Logo */}
        <div className="flex items-center gap-3">
          {onToggleMobileSidebar && (
            <button
              onClick={onToggleMobileSidebar}
              className="lg:hidden p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              aria-label="Toggle Navigation Drawer"
            >
              {isMobileSidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          )}

          {/* Hospital Admin Brand Logo -> Links to /hospital-admin */}
          <Link to="/hospital-admin" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-emerald-400 flex items-center justify-center text-slate-950 font-bold shadow-md shadow-teal-500/20 group-hover:scale-105 transition-transform duration-300">
              <HeartPulse className="w-6 h-6 text-slate-950" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 via-emerald-200 to-white bg-clip-text text-transparent">
                HealthPulse
              </span>
              <span className="block text-[10px] uppercase tracking-wider text-teal-400 font-bold -mt-1">
                Hospital Operations
              </span>
            </div>
          </Link>
        </div>

        {/* Right Side: AI Assistant, Profile Chip, Logout */}
        <div className="flex items-center gap-3">
          {/* AI Health Assistant Trigger */}
          <button
            onClick={handleOpenChat}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white font-medium text-xs sm:text-sm shadow-md shadow-teal-600/20 transition-all hover:scale-[1.02]"
          >
            <Bot className="w-4 h-4 animate-bounce" />
            <span className="hidden sm:inline">AI Health Assistant</span>
            <span className="sm:hidden">AI Assistant</span>
          </button>

          {/* Admin Profile Chip & Logout */}
          <div className="flex items-center gap-3 pl-2 border-l border-slate-800">
            <Link
              to="/hospital-admin/profile"
              className="flex items-center gap-2 text-xs sm:text-sm text-slate-200 font-medium hover:text-teal-400 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-teal-500/20 text-teal-300 flex items-center justify-center font-bold text-xs border border-teal-500/30 shrink-0">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'A'}
              </div>
              <div className="hidden md:block text-left">
                <div className="text-xs font-semibold text-slate-100 max-w-[130px] truncate">
                  {user?.name || 'Hospital Admin'}
                </div>
                <div className="text-[10px] text-teal-400 font-medium flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 inline text-teal-400" />
                  <span>Admin</span>
                </div>
              </div>
            </Link>

            {/* Logout Icon */}
            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>
    </header>
  );
};
