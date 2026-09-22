import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ChatProvider } from './context/ChatContext';
import { getRoleDashboard } from './utils/roleUtils';

// Components
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { FloatingChatbot } from './components/FloatingChatbot';
import { FloatingUIProvider } from './context/FloatingUIContext';
import { HospitalAdminLayout } from './components/HospitalAdminLayout';

// Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { DoctorsPage } from './pages/DoctorsPage';
import { MyAppointmentsPage } from './pages/MyAppointmentsPage';
import { ChatHistoryPage } from './pages/ChatHistoryPage';
import { ProfilePage } from './pages/ProfilePage';
import { MyPrescriptionsPage } from './pages/MyPrescriptionsPage';

// Doctor Pages
import { DoctorDashboardPage } from './pages/doctor/DoctorDashboardPage';
import { DoctorAppointmentsPage } from './pages/doctor/DoctorAppointmentsPage';
import { DoctorSchedulePage } from './pages/doctor/DoctorSchedulePage';
import { DoctorPatientsPage } from './pages/doctor/DoctorPatientsPage';
import { DoctorPatientDetailPage } from './pages/doctor/DoctorPatientDetailPage';
import { DoctorProfilePage } from './pages/doctor/DoctorProfilePage';
import { DoctorSessionsPage } from './pages/doctor/DoctorSessionsPage';
import { DoctorPrescriptionsPage } from './pages/doctor/DoctorPrescriptionsPage';

// Admin Pages
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AdminDoctorsPage } from './pages/AdminDoctorsPage';
import { AdminHospitalsPage } from './pages/AdminHospitalsPage';
import { AdminDepartmentsPage } from './pages/AdminDepartmentsPage';
import { AdminSchedulesPage } from './pages/AdminSchedulesPage';
import { AdminAppointmentsPage } from './pages/AdminAppointmentsPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AdminChatPage } from './pages/AdminChatPage';

// Hospital Admin Pages
import { HospitalAdminDashboardPage } from './pages/hospital_admin/HospitalAdminDashboardPage';
import { HospitalAdminDoctorsPage } from './pages/hospital_admin/HospitalAdminDoctorsPage';
import { HospitalAdminDepartmentsPage } from './pages/hospital_admin/HospitalAdminDepartmentsPage';
import { HospitalAdminSchedulesPage } from './pages/hospital_admin/HospitalAdminSchedulesPage';
import { HospitalAdminAppointmentsPage } from './pages/hospital_admin/HospitalAdminAppointmentsPage';
import { HospitalAdminProfilePage } from './pages/hospital_admin/HospitalAdminProfilePage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const PatientRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isPatient, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!isPatient) return <Navigate to={getRoleDashboard(user.role)} replace />;
  return <>{children}</>;
};

const DoctorRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isDoctor, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!isDoctor) return <Navigate to={getRoleDashboard(user.role)} replace />;
  return <>{children}</>;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAdmin, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to={getRoleDashboard(user.role)} replace />;
  return <>{children}</>;
};

const HospitalAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isHospitalAdmin, isAdmin, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!isHospitalAdmin && !isAdmin) return <Navigate to={getRoleDashboard(user.role)} replace />;
  return <>{children}</>;
};

const RoleAwarePublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (user && (user.role === 'hospital_admin' || user.role === 'admin' || user.role === 'super_admin' || user.role === 'doctor')) {
    return <Navigate to={getRoleDashboard(user.role)} replace />;
  }
  return <>{children}</>;
};

export const AppContent: React.FC = () => {
  const location = useLocation();
  const isHospitalAdminPath = location.pathname.startsWith('/hospital-admin');

  if (isHospitalAdminPath) {
    return (
      <HospitalAdminRoute>
        <HospitalAdminLayout>
          <Routes>
            <Route path="/hospital-admin" element={<HospitalAdminDashboardPage />} />
            <Route path="/hospital-admin/doctors" element={<HospitalAdminDoctorsPage />} />
            <Route path="/hospital-admin/departments" element={<HospitalAdminDepartmentsPage />} />
            <Route path="/hospital-admin/schedules" element={<HospitalAdminSchedulesPage />} />
            <Route path="/hospital-admin/appointments" element={<HospitalAdminAppointmentsPage />} />
            <Route path="/hospital-admin/profile" element={<HospitalAdminProfilePage />} />
            <Route path="*" element={<Navigate to="/hospital-admin" replace />} />
          </Routes>
        </HospitalAdminLayout>
        <FloatingChatbot />
      </HospitalAdminRoute>
    );
  }

  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50">
      <Navbar />
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 flex-1">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<RoleAwarePublicRoute><LandingPage /></RoleAwarePublicRoute>} />
          <Route path="/doctors" element={<RoleAwarePublicRoute><DoctorsPage /></RoleAwarePublicRoute>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Patient Protected Routes */}
          <Route path="/dashboard" element={<PatientRoute><DashboardPage /></PatientRoute>} />
          <Route path="/my-appointments" element={<PatientRoute><MyAppointmentsPage /></PatientRoute>} />
          <Route path="/my-prescriptions" element={<PatientRoute><MyPrescriptionsPage /></PatientRoute>} />
          <Route path="/chat-history" element={<PatientRoute><ChatHistoryPage /></PatientRoute>} />
          <Route path="/profile" element={<PatientRoute><ProfilePage /></PatientRoute>} />

          {/* Doctor Protected Routes */}
          <Route path="/doctor/dashboard" element={<DoctorRoute><DoctorDashboardPage /></DoctorRoute>} />
          <Route path="/doctor/appointments" element={<DoctorRoute><DoctorAppointmentsPage /></DoctorRoute>} />
          <Route path="/doctor/sessions" element={<DoctorRoute><DoctorSessionsPage /></DoctorRoute>} />
          <Route path="/doctor/prescriptions" element={<DoctorRoute><DoctorPrescriptionsPage /></DoctorRoute>} />
          <Route path="/doctor/medical-records" element={<Navigate to="/doctor/patients" replace />} />
          <Route path="/doctor/schedule" element={<DoctorRoute><DoctorSchedulePage /></DoctorRoute>} />
          <Route path="/doctor/patients" element={<DoctorRoute><DoctorPatientsPage /></DoctorRoute>} />
          <Route path="/doctor/patients/:patientId" element={<DoctorRoute><DoctorPatientDetailPage /></DoctorRoute>} />
          <Route path="/doctor/profile" element={<DoctorRoute><DoctorProfilePage /></DoctorRoute>} />

          {/* Admin Protected Routes */}
          <Route path="/admin" element={<AdminRoute><AdminDashboardPage /></AdminRoute>} />
          <Route path="/admin/doctors" element={<AdminRoute><AdminDoctorsPage /></AdminRoute>} />
          <Route path="/admin/hospitals" element={<AdminRoute><AdminHospitalsPage /></AdminRoute>} />
          <Route path="/admin/departments" element={<AdminRoute><AdminDepartmentsPage /></AdminRoute>} />
          <Route path="/admin/schedules" element={<AdminRoute><AdminSchedulesPage /></AdminRoute>} />
          <Route path="/admin/appointments" element={<AdminRoute><AdminAppointmentsPage /></AdminRoute>} />
          <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
          <Route path="/admin/chats" element={<AdminRoute><AdminChatPage /></AdminRoute>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
      <FloatingChatbot />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <ToastProvider>
          <ChatProvider>
            <FloatingUIProvider>
              <AppContent />
            </FloatingUIProvider>
          </ChatProvider>
        </ToastProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;
