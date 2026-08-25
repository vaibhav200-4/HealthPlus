import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ChatProvider } from './context/ChatContext';

// Components
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { FloatingChatbot } from './components/FloatingChatbot';

// Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { DoctorsPage } from './pages/DoctorsPage';
import { MyAppointmentsPage } from './pages/MyAppointmentsPage';
import { ChatHistoryPage } from './pages/ChatHistoryPage';
import { ProfilePage } from './pages/ProfilePage';

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

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const PatientRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isPatient, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user || !isPatient) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const DoctorRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isDoctor, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user || !isDoctor) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAdmin, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading session...</div>;
  if (!user || !isAdmin) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export const AppContent: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50">
      <Navbar />
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 flex-1">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/doctors" element={<DoctorsPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Patient Protected Routes */}
          <Route path="/dashboard" element={<PatientRoute><DashboardPage /></PatientRoute>} />
          <Route path="/my-appointments" element={<PatientRoute><MyAppointmentsPage /></PatientRoute>} />
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
            <AppContent />
          </ChatProvider>
        </ToastProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;
