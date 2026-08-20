import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ChatMessage } from '../types';
import { EmptyState } from '../components/EmptyState';
import { MessageSquare, Bot, User as UserIcon, Send, Smartphone, Globe, Link as LinkIcon } from 'lucide-react';

export const ChatHistoryPage: React.FC = () => {
  const { user, linkTelegram } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [telegramIdInput, setTelegramIdInput] = useState('');
  const [linking, setLinking] = useState(false);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/chat/history');
      setMessages(res.data || []);
    } catch (err) {
      console.error('Failed to fetch chat history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkTelegramSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!telegramIdInput.trim()) return;
    setLinking(true);
    const success = await linkTelegram(telegramIdInput.trim());
    if (success) {
      setTelegramIdInput('');
      fetchChatHistory();
    }
    setLinking(false);
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-800 rounded-3xl p-8 text-white shadow-xl space-y-3">
        <span className="text-xs font-bold text-tealmed-300 uppercase tracking-wider">Dual Channel Synchronization</span>
        <h1 className="text-3xl font-extrabold tracking-tight">AI Chat History</h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Chronological transcript of your AI conversations across Web Chat and Telegram linked accounts.
        </p>
      </div>

      {/* Telegram Link Card */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-sky-500" />
            Telegram Account Linking
          </h3>
          <p className="text-xs text-slate-500">
            {user?.telegram_id
              ? `Linked Telegram User ID: ${user.telegram_id}`
              : 'Link your Telegram user ID to view Telegram AI chat messages under this web account.'}
          </p>
        </div>

        {!user?.telegram_id && (
          <form onSubmit={handleLinkTelegramSubmit} className="flex items-center gap-2 w-full sm:w-auto">
            <input
              type="text"
              value={telegramIdInput}
              onChange={(e) => setTelegramIdInput(e.target.value)}
              placeholder="Telegram ID (e.g. 12345678)"
              className="px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-sky-500"
              required
            />
            <button
              type="submit"
              disabled={linking}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow transition-all flex items-center gap-1"
            >
              <LinkIcon className="w-3.5 h-3.5" />
              Link Account
            </button>
          </form>
        )}
      </div>

      {/* Chat Messages Log */}
      {loading ? (
        <div className="p-8 text-center bg-white rounded-3xl border border-slate-200">
          <p className="text-xs text-slate-500">Loading chat history...</p>
        </div>
      ) : messages.length === 0 ? (
        <EmptyState
          title="No Chat History"
          description="Start a conversation with our AI Assistant in Web Chat or Telegram!"
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 space-y-4 shadow-sm max-h-[600px] overflow-y-auto">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-medical-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-medical-600 to-medical-500 text-white rounded-br-none shadow'
                    : 'bg-slate-50 text-slate-800 border border-slate-200 rounded-bl-none'
                }`}
              >
                <div className="flex items-center justify-between gap-4 mb-1">
                  <span className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${
                    msg.role === 'user' ? 'text-medical-200' : 'text-slate-400'
                  }`}>
                    {msg.channel === 'telegram' ? <Smartphone className="w-3 h-3 text-sky-400" /> : <Globe className="w-3 h-3 text-emerald-400" />}
                    {msg.channel.toUpperCase()} CHANNEL
                  </span>
                  <span className={`text-[10px] ${msg.role === 'user' ? 'text-medical-200' : 'text-slate-400'}`}>
                    {msg.created_at ? new Date(msg.created_at).toLocaleString() : ''}
                  </span>
                </div>
                <div className="whitespace-pre-wrap">{msg.message}</div>
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-xs flex-shrink-0 mt-1">
                  <UserIcon className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
