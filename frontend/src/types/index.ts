export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  telegram_id?: string;
  role: 'user' | 'patient' | 'doctor' | 'staff' | 'admin' | 'super_admin';
  patient_code?: string;
  date_of_birth?: string;
  gender?: string;
  blood_group?: string;
  address?: string;
  emergency_contact?: string;
  created_at?: string;
}

export interface Department {
  id: string;
  hospital_id: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive';
  created_at?: string;
  updated_at?: string;
}

export interface Doctor {
  id: string;
  profile_id?: string;
  hospital_id: string;
  hospital_name?: string;
  department_id?: string;
  department_name?: string;
  name: string;
  degree?: string;
  specialization: string;
  experience_years: number;
  designation?: string;
  languages: string[];
  consultation_fee: number;
  availability?: string;
  image_url?: string;
  rating?: number;
  total_reviews?: number;
  latitude?: number;
  longitude?: number;
  distance_meters?: number;
  source?: 'registered' | 'external';
  bookable?: boolean;
  phone?: string;
  address?: string;
}

export interface Hospital {
  id: string;
  hospital_name: string;
  street?: string;
  area?: string;
  city?: string;
  state?: string;
  pincode?: string;
  country?: string;
  phone?: string;
  email?: string;
  departments: string[];
}

export interface Appointment {
  id: string;
  user_id: string;
  doctor_id?: string;
  doctor_name: string;
  hospital_name: string;
  date: string;
  start_time: string;
  end_time: string;
  calendar_event_id?: string;
  status: 'pending' | 'confirmed' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled' | 'rejected' | 'no_show';
  patient_name: string;
  patient_phone?: string;
  patient_email?: string;
  notes?: string;
  idempotency_key?: string;
  created_at?: string;
}

export interface Session {
  id: string;
  appointment_id?: string;
  doctor_id: string;
  patient_id: string;
  patient_code?: string;
  started_at?: string;
  ended_at?: string;
  status: 'in_progress' | 'completed' | 'cancelled';
  symptoms?: string;
  diagnosis?: string;
  doctor_notes?: string;
  created_at?: string;
}

export interface PrescriptionItem {
  id?: string;
  medicine_name: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
  instructions?: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  patient_code?: string;
  doctor_id: string;
  doctor_name?: string;
  session_id?: string;
  notes?: string;
  items: PrescriptionItem[];
  created_at?: string;
}

export interface MedicalRecord {
  id: string;
  patient_id: string;
  patient_code?: string;
  doctor_id?: string;
  doctor_name?: string;
  session_id?: string;
  record_type: 'diagnosis' | 'lab_report' | 'xray' | 'mri' | 'blood_test' | 'discharge_summary' | 'other';
  title: string;
  description?: string;
  file_url?: string;
  signed_file_url?: string;
  uploaded_by?: 'patient' | 'doctor' | 'admin';
  file_type?: string;
  file_size_bytes?: number;
  created_at?: string;
}

export interface DoctorReview {
  id: string;
  patient_id: string;
  patient_code?: string;
  doctor_id: string;
  appointment_id: string;
  rating: number;
  review?: string;
  created_at?: string;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
  capacity?: number;
  booked?: number;
  blocked?: boolean;
}

export interface ChatMessage {
  id: string;
  user_id?: string;
  channel: 'web' | 'telegram';
  session_id: string;
  role: 'user' | 'assistant';
  message: string;
  telegram_id?: string;
  created_at?: string;
}

export interface VectorSearchResult {
  score: number;
  doctor_id: string;
  doctor_name: string;
  hospital_id: string;
  hospital_name: string;
  specialization: string;
  degree?: string;
  designation?: string;
  experience_years?: number;
  city?: string;
  consultation_fee?: number;
  availability?: string;
  text?: string;
}

export interface MockPaymentCard {
  id: string;
  type: 'visa' | 'mastercard' | 'amex' | 'healthpulse';
  cardNumberLast4: string;
  holderName: string;
  expiryMonth: string;
  expiryYear: string;
  isDefault?: boolean;
}
