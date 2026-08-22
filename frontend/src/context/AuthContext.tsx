import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  register: (name: string, email: string, password: string, phone?: string) => Promise<{ success: boolean; message?: string }>;
  linkTelegram: (telegram_id: string) => Promise<boolean>;
  logout: () => void;
  isAdmin: boolean;
  isDoctor: boolean;
  isPatient: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('hospital_auth_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchMe = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await api.get('/auth/me');
        setUser(res.data);
      } catch (err) {
        console.error('Failed to fetch user session:', err);
        localStorage.removeItem('hospital_auth_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    fetchMe();
  }, [token]);

  const login = async (email: string, password: string) => {
    try {
      const res = await api.post('/auth/login', { email, password });
      const { access_token, user: userData } = res.data;
      localStorage.setItem('hospital_auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      return { success: true };
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid login credentials';
      return { success: false, message: msg };
    }
  };

  const register = async (name: string, email: string, password: string, phone?: string) => {
    try {
      const res = await api.post('/auth/register', { name, email, password, phone });
      const { access_token, user: userData } = res.data;
      localStorage.setItem('hospital_auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      return { success: true };
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed';
      return { success: false, message: msg };
    }
  };

  const linkTelegram = async (telegram_id: string) => {
    try {
      const res = await api.post('/auth/link-telegram', { telegram_id });
      setUser(res.data);
      return true;
    } catch (err) {
      console.error('Failed to link Telegram ID:', err);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('hospital_auth_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        linkTelegram,
        logout,
        isAdmin: user?.role === 'admin',
        isDoctor: user?.role === 'doctor',
        isPatient: user?.role === 'user' || user?.role === 'patient'
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
