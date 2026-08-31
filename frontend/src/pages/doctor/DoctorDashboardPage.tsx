import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { Appointment, Doctor } from '../../types';
import { DoctorPortalHero } from '../../components/doctor/DoctorPortalHero';
import { StatCard } from '../../components/doctor/StatCard';
import { StatusBadge } from '../../components/doctor/StatusBadge';
import { 
  Calendar, 
  Clock, 
  Users, 
  CheckCircle2, 
  Stethoscope, 
  ArrowRight,
  Building,
  UserCheck,
  CalendarDays
} from 'lucide-react';

export const DoctorDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchDoctorDashboardData();
  }, []);

  const fetchDoctorDashboardData = async () => {
    try {
      const [statsRes, appRes] = await Promise.all([
        api.get('/doctors/me/stats'),
        api.get('/doctors/me/appointments')
      ]);
      setStats(statsRes.data);
      setAppointments(appRes.data || []);
    } catch (err) {
      console.error('Failed to load doctor dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (appId: string, newStatus: string) => {
    try {
      await api.patch(`/admin/appointments/${appId}/status`, { status: newStatus });
      fetchDoctorDashboardData();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const doctor: Doctor | undefined = stats?.doctor;
  const realName = doctor?.name || user?.name || 'Doctor';
  const todayFormatted = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Reusable Doctor Portal Hero Header */}
      <DoctorPortalHero
        showIllustration={true}
        badgeText="Attending Specialist Dashboard"
        badgeIcon={<Stethoscope className="w-4 h-4 text-tealmed-700" />}
        title={`Welcome back, Dr. ${realName.replace(/^Dr\.\s*/i, '')}! 👋`}
        subtitle="Here's what's happening in your practice today."
        metadata={[
          { icon: <CalendarDays className="w-3.5 h-3.5 text-tealmed-600" />, label: todayFormatted },
          { icon: <Clock className="w-3.5 h-3.5 text-tealmed-600" />, label: doctor?.availability || 'Tuesday to Saturday, 11:00 AM - 3:00 PM' },
          { icon: <Stethoscope className="w-3.5 h-3.5 text-tealmed-600" />, label: doctor?.specialization ? `${doctor.specialization} Specialist` : 'General Surgery Specialist' }
        ]}
        actions={
          <>
            <Link
              to="/doctor/appointments"
              className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-tealmed-600 hover:bg-tealmed-700 text-white font-bold text-xs shadow-md shadow-tealmed-600/20 transition-all"
            >
              <Calendar className="w-4 h-4" /> View All Appointments
            </Link>
            <Link
              to="/doctor/schedule"
              className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white text-slate-800 font-bold text-xs hover:bg-slate-100 transition-all border border-slate-200 shadow-2xs"
            >
              <Clock className="w-4 h-4 text-tealmed-700" /> Manage Shifts
            </Link>
          </>
        }
      />

      {/* Doctor Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Calendar className="w-5 h-5" />}
          label="Today's Appointments"
          value={stats?.today_appointments_count ?? 0}
          description="Scheduled for today"
          iconBgColor="bg-tealmed-50"
          iconTextColor="text-tealmed-700"
          accentBorderColor="hover:border-tealmed-300"
        />

        <StatCard
          icon={<Clock className="w-5 h-5" />}
          label="Upcoming Consults"
          value={stats?.upcoming_appointments_count ?? 0}
          description="Active confirmed / pending"
          iconBgColor="bg-sky-50"
          iconTextColor="text-sky-700"
          accentBorderColor="hover:border-sky-300"
        />

        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          label="Completed"
          value={stats?.completed_appointments_count ?? 0}
          description="Successfully completed"
          iconBgColor="bg-emerald-50"
          iconTextColor="text-emerald-700"
          accentBorderColor="hover:border-emerald-300"
        />

        <StatCard
          icon={<Users className="w-5 h-5" />}
          label="Total Patients"
          value={stats?.total_patients_count ?? 0}
          description="Unique patients seen"
          iconBgColor="bg-indigo-50"
          iconTextColor="text-indigo-700"
          accentBorderColor="hover:border-indigo-300"
        />
      </div>

      {/* Appointments Timeline Table */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-tealmed-600" />
            Appointments Assigned to You ({appointments.length})
          </h2>
          <Link to="/doctor/appointments" className="text-xs font-bold text-tealmed-700 hover:underline flex items-center gap-1">
            View All <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-tealmed-500 border-t-transparent rounded-full animate-spin"></div>
            Loading doctor appointments...
          </div>
        ) : appointments.length === 0 ? (
          <div className="p-8 text-center bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 space-y-2">
            <Calendar className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-sm font-semibold text-slate-700">No appointments assigned to your profile yet.</p>
            <p className="text-xs text-slate-500">Patient bookings via web or AI agent will appear here automatically.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3.5 rounded-l-xl">Patient Name</th>
                  <th className="p-3.5">Date & Time</th>
                  <th className="p-3.5">Hospital</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right rounded-r-xl">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {appointments.slice(0, 5).map((app) => {
                  const initial = app.patient_name ? app.patient_name.charAt(0).toUpperCase() : 'P';
                  return (
                    <tr key={app.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="p-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-tealmed-50 text-tealmed-800 flex items-center justify-center font-extrabold text-xs border border-tealmed-200/80 flex-shrink-0">
                            {initial}
                          </div>
                          <div>
                            <span className="font-extrabold text-slate-900 block">{app.patient_name}</span>
                            <span className="text-[10px] text-slate-500 font-medium">
                              {app.patient_email || app.patient_phone || 'No contact details'}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="p-3.5">
                        <span className="font-bold text-slate-800 block">{app.date}</span>
                        <span className="text-[10px] text-tealmed-700 font-semibold">{app.start_time} - {app.end_time}</span>
                      </td>

                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5 text-slate-700">
                          <Building className="w-3.5 h-3.5 text-slate-400" />
                          <span>{app.hospital_name || 'Hospital Node'}</span>
                        </div>
                      </td>

                      <td className="p-3.5">
                        <StatusBadge status={app.status} />
                      </td>

                      <td className="p-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {app.status !== 'completed' && (
                            <button
                              onClick={() => handleUpdateStatus(app.id, 'completed')}
                              className="px-2.5 py-1 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200/60 rounded-xl text-[10px] font-bold transition-colors"
                            >
                              Mark Completed
                            </button>
                          )}
                          {app.status !== 'cancelled' && (
                            <button
                              onClick={() => handleUpdateStatus(app.id, 'cancelled')}
                              className="px-2.5 py-1 bg-rose-50 text-rose-800 hover:bg-rose-100 border border-rose-200/60 rounded-xl text-[10px] font-bold transition-colors"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
