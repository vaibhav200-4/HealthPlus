import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Stethoscope, 
  Building2, 
  CalendarClock, 
  ClipboardList, 
  Users, 
  MessageSquare,
  ShieldCheck
} from 'lucide-react';

export const AdminSidebar: React.FC = () => {
  const location = useLocation();

  const links = [
    { path: '/admin', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/admin/doctors', label: 'Doctors', icon: Stethoscope },
    { path: '/admin/hospitals', label: 'Hospitals', icon: Building2 },
    { path: '/admin/schedules', label: 'Schedules', icon: CalendarClock },
    { path: '/admin/appointments', label: 'Appointments', icon: ClipboardList },
    { path: '/admin/users', label: 'Users', icon: Users },
    { path: '/admin/chats', label: 'Chat Logs', icon: MessageSquare },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] p-4 space-y-6 flex flex-col justify-between hidden md:flex border-r border-slate-800">
      <div className="space-y-6">
        <div className="px-3 py-2 bg-slate-800/80 rounded-xl border border-slate-700/60 flex items-center gap-2 text-xs font-semibold text-amber-400">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
          <span>Administrator Control Center</span>
        </div>

        <nav className="space-y-1 text-sm font-medium">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-colors ${
                  isActive
                    ? 'bg-medical-600 text-white font-semibold shadow-md shadow-medical-500/20'
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

      <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 text-xs text-slate-500 text-center">
        Logged in as System Admin
      </div>
    </aside>
  );
};
