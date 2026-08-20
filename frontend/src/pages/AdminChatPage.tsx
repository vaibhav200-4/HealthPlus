import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { AdminSidebar } from '../components/AdminSidebar';
import { ChatMessage } from '../types';
import { MessageSquare, Bot, User as UserIcon, Globe, Smartphone } from 'lucide-react';

export const AdminChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await api.get('/admin/chat-history');
      setMessages(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <AdminSidebar />
      <main className="flex-1 p-6 sm:p-8 space-y-6 bg-slate-50/50 overflow-y-auto">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">System AI Chat Audit Log</h1>
          <p className="text-xs text-slate-500">Monitor all Web Chat and Telegram bot messages stored in Supabase.</p>
        </div>

        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 space-y-4 max-h-[700px] overflow-y-auto">
          {messages.map((msg) => (
            <div key={msg.id} className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-1 text-xs">
              <div className="flex items-center justify-between font-semibold">
                <span className="flex items-center gap-1.5 text-medical-700">
                  {msg.role === 'user' ? <UserIcon className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                  {msg.role.toUpperCase()} • User ID: {msg.user_id || 'Unlinked'}
                </span>
                <span className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                  {msg.channel === 'telegram' ? <Smartphone className="w-3 h-3 text-sky-500" /> : <Globe className="w-3 h-3 text-emerald-500" />}
                  {msg.channel.toUpperCase()}
                </span>
              </div>
              <p className="text-slate-800 font-medium pl-5">{msg.message}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};
