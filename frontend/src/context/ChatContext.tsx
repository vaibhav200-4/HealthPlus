import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';
import { ChatMessage } from '../types';

interface ChatContextType {
  messages: ChatMessage[];
  loading: boolean;
  uploading: boolean;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  sendMessage: (text: string) => Promise<void>;
  uploadFile: (file: File, customTitle?: string) => Promise<void>;
  sessionId: string;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>(() => {
    return localStorage.getItem('hospital_chat_session') || `session_${Math.random().toString(36).substring(2, 9)}`;
  });

  useEffect(() => {
    localStorage.setItem('hospital_chat_session', sessionId);
  }, [sessionId]);

  useEffect(() => {
    if (user) {
      fetchHistory();
    }
  }, [user]);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/chat/history');
      setMessages(res.data);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const tempUserMsg: ChatMessage = {
      id: Math.random().toString(),
      channel: 'web',
      session_id: sessionId,
      role: 'user',
      message: text,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await api.post('/chat/send', {
        message: text,
        session_id: sessionId,
        channel: 'web'
      });

      const tempAssistantMsg: ChatMessage = {
        id: Math.random().toString(),
        channel: 'web',
        session_id: sessionId,
        role: 'assistant',
        message: res.data.message,
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, tempAssistantMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg: ChatMessage = {
        id: Math.random().toString(),
        channel: 'web',
        session_id: sessionId,
        role: 'assistant',
        message: 'Sorry, I ran into an error processing your request. Please try again.',
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (file: File, customTitle?: string) => {
    setUploading(true);
    const title = customTitle?.trim() || file.name;
    const patientIdentifier = user?.id || user?.patient_code || user?.email || 'patient';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_identifier', patientIdentifier);
    formData.append('session_id', sessionId);
    formData.append('uploaded_by', 'patient');
    formData.append('from_chat', 'true');
    formData.append('title', title);

    try {
      const uploadRes = await api.post('/medical-records/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const tempUserMsg: ChatMessage = {
        id: uploadRes.data.id || Math.random().toString(),
        channel: 'web',
        session_id: sessionId,
        role: 'user',
        message: `[Uploaded document: ${title}]`,
        file_url: uploadRes.data.file_url,
        signed_file_url: uploadRes.data.signed_file_url,
        file_type: uploadRes.data.file_type,
        title: title,
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, tempUserMsg]);
      setLoading(true);

      const triggerText = `[Uploaded document: ${title}]`;
      const sendRes = await api.post('/chat/send', {
        message: triggerText,
        session_id: sessionId,
        channel: 'web'
      });

      const tempAssistantMsg: ChatMessage = {
        id: Math.random().toString(),
        channel: 'web',
        session_id: sessionId,
        role: 'assistant',
        message: sendRes.data.message,
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, tempAssistantMsg]);
    } catch (err: any) {
      console.error('File upload error:', err);
      throw err;
    } finally {
      setUploading(false);
      setLoading(false);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        loading,
        uploading,
        isOpen,
        setIsOpen,
        sendMessage,
        uploadFile,
        sessionId
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
