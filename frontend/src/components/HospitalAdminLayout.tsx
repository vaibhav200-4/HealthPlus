import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { HospitalAdminNavbar } from './HospitalAdminNavbar';
import { HospitalAdminSidebar } from './HospitalAdminSidebar';

interface HospitalAdminLayoutProps {
  children?: React.ReactNode;
}

export const HospitalAdminLayout: React.FC<HospitalAdminLayoutProps> = ({ children }) => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <HospitalAdminNavbar 
        onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        isMobileSidebarOpen={mobileSidebarOpen}
      />
      <div className="flex flex-1 w-full relative">
        <HospitalAdminSidebar 
          mobileOpen={mobileSidebarOpen}
          onClose={() => setMobileSidebarOpen(false)}
        />
        <main className="flex-1 w-full p-6 sm:p-8 pb-24 bg-slate-50/50 overflow-y-auto min-h-[calc(100vh-4rem)]">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
};
