import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';
import { ChatMessage } from '../types';

interface ChatContextType {
  messages: ChatMessage[];
  loading: boolean;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  sendMessage: (text: string) => Promise<void>;
  sessionId: string;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
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

  return (
    <ChatContext.Provider
      value={{
        messages,
        loading,
        isOpen,
        setIsOpen,
        sendMessage,
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
