export const getRoleDashboard = (role?: string): string => {
  switch (role) {
    case 'hospital_admin':
      return '/hospital-admin';
    case 'admin':
    case 'super_admin':
      return '/admin';
    case 'doctor':
      return '/doctor/dashboard';
    case 'user':
    case 'patient':
      return '/';
    default:
      return '/login';
  }
};

