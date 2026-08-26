/**
 * HealthPulse Deterministic Doctor Image Registry
 * Provides persistent, high-quality, professional doctor profile photographs.
 */

// Unique professional photo mapping for doctors D001 through D010
export const DOCTOR_IMAGE_MAP: Record<string, string> = {
  // Dr. Arjun Mehta - Male Senior Cardiologist
  D001: 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Neha Sharma - Female Consultant Neurologist
  D002: 'https://images.unsplash.com/photo-1594824813566-788b5608d084?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Riya Kapoor - Female Senior Pediatrician
  D003: 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Vikram Joshi - Male Consultant Dermatologist
  D004: 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Sameer Patel - Male Senior Endocrinologist
  D005: 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Ananya Rao - Female Consultant Orthopedic Surgeon
  D006: 'https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Priya Nair - Female Consultant Gynecologist
  D007: 'https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Rahul Verma - Male Consultant Psychiatrist
  D008: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Karan Malhotra - Male Senior Pulmonologist
  D009: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&auto=format&fit=crop&q=80',
  
  // Dr. Meera Iyer - Female Senior General Surgeon
  D010: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500&auto=format&fit=crop&q=80',
};

// Distinct professional doctor pool for fallback hashing
const DOCTOR_IMAGE_POOL: string[] = [
  'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1594824813566-788b5608d084?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500&auto=format&fit=crop&q=80',
];

/**
 * Returns a deterministic, unique image URL for a given doctor record.
 */
export function getDoctorImage(doctor: { id?: string; name?: string; image_url?: string }): string {
  const docId = doctor.id || '';
  if (docId && DOCTOR_IMAGE_MAP[docId]) {
    return DOCTOR_IMAGE_MAP[docId];
  }

  // Check if doctor has a custom non-generic image_url
  if (doctor.image_url) {
    const isGenericDefault =
      doctor.image_url.includes('1537368910025-700350fe46c7') ||
      doctor.image_url.includes('1622253692010-333f2da6031d');
    if (!isGenericDefault) {
      return doctor.image_url;
    }
  }

  // Fallback hash by ID or Name
  const strToHash = docId || doctor.name || 'doctor';
  let hash = 0;
  for (let i = 0; i < strToHash.length; i++) {
    hash = (hash << 5) - hash + strToHash.charCodeAt(i);
    hash |= 0;
  }

  const index = Math.abs(hash) % DOCTOR_IMAGE_POOL.length;
  return DOCTOR_IMAGE_POOL[index];
}
