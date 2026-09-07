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
  clearChat: () => void;
  sessionId: string;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const DEFAULT_GREETING_MESSAGE: ChatMessage = {
  id: 'welcome-greeting',
  channel: 'web',
  session_id: '',
  role: 'assistant',
  message: "Hello! I'm your health assistant. I can help you find doctors, book appointments, and answer questions. How can I help you today?",
  created_at: new Date().toISOString()
};

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>(() => {
    return localStorage.getItem('hospital_chat_session') || `session_${Math.random().toString(36).substring(2, 9)}`;
  });

  const clearChat = () => {
    setMessages([]);
    setLoading(false);
    setUploading(false);
    const newSession = `session_${Math.random().toString(36).substring(2, 9)}`;
    setSessionId(newSession);
    localStorage.removeItem('hospital_chat_session');
    Object.keys(localStorage).forEach((key) => {
      if (key.startsWith('hospital_chat_session')) {
        localStorage.removeItem(key);
      }
    });
  };

  useEffect(() => {
    if (sessionId && user) {
      localStorage.setItem('hospital_chat_session', sessionId);
      localStorage.setItem(`hospital_chat_session_${user.id}`, sessionId);
    }
  }, [sessionId, user]);

  useEffect(() => {
    if (user && user.id) {
      fetchHistory(user.id);
    } else {
      clearChat();
    }
  }, [user?.id]);

  const fetchHistory = async (userId: string) => {
    setLoading(true);
    try {
      const res = await api.get('/chat/history');
      const historyData: ChatMessage[] = res.data || [];
      if (historyData.length > 0) {
        setMessages(historyData);
        const lastMsg = historyData[historyData.length - 1];
        if (lastMsg?.session_id) {
          setSessionId(lastMsg.session_id);
        }
      } else {
        // Fresh session for logged-in user: show default greeting
        setMessages([{ ...DEFAULT_GREETING_MESSAGE, session_id: sessionId }]);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
      setMessages([{ ...DEFAULT_GREETING_MESSAGE, session_id: sessionId }]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || !user) return;

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
    if (!user) return;
    setUploading(true);
    const title = customTitle?.trim() || file.name;
    const patientIdentifier = user.id || user.patient_code || user.email || 'patient';

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
        clearChat,
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
