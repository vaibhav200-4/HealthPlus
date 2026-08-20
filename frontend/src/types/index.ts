export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  telegram_id?: string;
  role: 'user' | 'admin';
  created_at?: string;
}

export interface Doctor {
  id: string;
  hospital_id: string;
  name: string;
  degree?: string;
  specialization: string;
  experience_years: number;
  designation?: string;
  languages: string[];
  consultation_fee: number;
  availability?: string;
  image_url?: string;
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
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  patient_name: string;
  patient_phone?: string;
  patient_email?: string;
  notes?: string;
  created_at?: string;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
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
