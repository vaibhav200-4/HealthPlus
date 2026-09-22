import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Stethoscope, 
  Building2, 
  CalendarClock, 
  ClipboardList, 
  Building,
  ShieldCheck,
  X
} from 'lucide-react';
import api from '../services/api';

interface HospitalAdminSidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export const HospitalAdminSidebar: React.FC<HospitalAdminSidebarProps> = ({
  mobileOpen = false,
  onClose
}) => {
  const location = useLocation();
  const [hospitalName, setHospitalName] = useState<string>('Hospital Admin');

  useEffect(() => {
    const fetchHospitalProfile = async () => {
      try {
        const res = await api.get('/hospital-admin/profile');
        if (res.data && res.data.hospital_name) {
          setHospitalName(res.data.hospital_name);
        }
      } catch (err) {
        console.error('Failed to fetch hospital profile for sidebar:', err);
      }
    };
    fetchHospitalProfile();
  }, []);

  const links = [
    { path: '/hospital-admin', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/hospital-admin/doctors', label: 'Doctors', icon: Stethoscope },
    { path: '/hospital-admin/departments', label: 'Departments', icon: Building2 },
    { path: '/hospital-admin/schedules', label: 'Schedules', icon: CalendarClock },
    { path: '/hospital-admin/appointments', label: 'Appointments', icon: ClipboardList },
    { path: '/hospital-admin/profile', label: 'Hospital Profile', icon: Building },
  ];

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between p-4 space-y-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="w-full px-3.5 py-3 bg-gradient-to-r from-teal-950/80 to-slate-800/80 rounded-xl border border-teal-800/60 flex items-center gap-3 text-xs font-semibold text-teal-400">
            <ShieldCheck className="w-5 h-5 text-teal-400 shrink-0" />
            <div className="truncate">
              <div className="text-[10px] uppercase tracking-wider text-teal-300/80 font-bold">Hospital Admin</div>
              <div className="text-xs text-white font-medium truncate">{hospitalName}</div>
            </div>
          </div>
          {onClose && (
            <button 
              onClick={onClose}
              className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <nav className="space-y-1 text-sm font-medium">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={onClose}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-colors ${
                  isActive
                    ? 'bg-teal-600 text-white font-semibold shadow-md shadow-teal-500/20'
                    : 'hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 text-xs text-slate-400 text-center truncate">
        Scoped Admin Panel
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Left Sidebar */}
      <aside className="w-64 shrink-0 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] border-r border-slate-800 hidden lg:block sticky top-16 self-start">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Backdrop & Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div 
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm transition-opacity" 
            onClick={onClose}
          />
          <aside className="relative w-72 max-w-[80vw] bg-slate-900 text-slate-300 h-full border-r border-slate-800 shadow-2xl z-10 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
