import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { Bot, X, Send, Sparkles, User as UserIcon, RefreshCw, MessageSquare } from 'lucide-react';

export const FloatingChatbot: React.FC = () => {
  const { messages, loading, isOpen, setIsOpen, sendMessage } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, loading, isOpen]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input);
    setInput('');
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-medical-600 to-tealmed-600 text-white rounded-full shadow-2xl hover:shadow-medical-500/40 hover:scale-105 transition-all duration-300 group"
      >
        <div className="relative">
          <Bot className="w-6 h-6 text-white group-hover:rotate-12 transition-transform" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-slate-900 animate-pulse"></span>
        </div>
        <span className="font-semibold text-sm pr-1 hidden sm:inline">AI Health Assistant</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[92vw] sm:w-[420px] h-[580px] max-h-[85vh] bg-white rounded-3xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-5">
      {/* Chat Header */}
      <div className="p-4 bg-gradient-to-r from-medical-900 via-medical-800 to-tealmed-800 text-white flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/20">
            <Sparkles className="w-5 h-5 text-tealmed-300" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm">Hospital Health Assistant</h3>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full font-semibold border border-emerald-400/30">
                Online
              </span>
            </div>
            <p className="text-xs text-slate-300">Here to help with appointments, doctors, and healthcare services.</p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(false)}
          className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <div className="w-14 h-14 rounded-2xl bg-medical-50 text-medical-600 flex items-center justify-center mb-3 shadow-inner">
              <Bot className="w-8 h-8" />
            </div>
            <h4 className="font-semibold text-slate-800 mb-1">Hello! I'm your Health Assistant</h4>
            <p className="text-xs text-slate-500 mb-4 max-w-xs">
              Ask me about doctor specializations, available slots, or say "Book Dr. Neha tomorrow at 4 PM".
            </p>
            <div className="grid grid-cols-1 gap-2 w-full text-xs">
              <button
                onClick={() => sendMessage('Find me a cardiologist in Indore')}
                className="p-2.5 bg-white border border-slate-200 rounded-xl text-left hover:border-medical-400 hover:bg-medical-50/40 text-slate-700 transition-colors shadow-sm"
              >
                🔍 "Find me a cardiologist in Indore"
              </button>
              <button
                onClick={() => sendMessage('What doctors are available at Sunrise Hospital?')}
                className="p-2.5 bg-white border border-slate-200 rounded-xl text-left hover:border-medical-400 hover:bg-medical-50/40 text-slate-700 transition-colors shadow-sm"
              >
                🏥 "Doctors at Sunrise Hospital?"
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-medical-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-sm mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[80%] p-3.5 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-medical-600 to-medical-500 text-white rounded-br-none shadow-md shadow-medical-500/10'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.message}</div>
                {msg.created_at && (
                  <span
                    className={`block text-[10px] mt-1.5 text-right ${
                      msg.role === 'user' ? 'text-medical-200' : 'text-slate-400'
                    }`}
                  >
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-xs flex-shrink-0 mt-1">
                  <UserIcon className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-medical-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-sm">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-white p-3.5 rounded-2xl rounded-bl-none border border-slate-200 text-slate-500 text-sm flex items-center gap-2 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-medical-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-medical-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-2 h-2 bg-medical-600 rounded-full animate-bounce [animation-delay:0.4s]"></span>
              </div>
              <span className="text-xs font-medium text-slate-400">Health Assistant thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask AI or book appointment..."
          className="flex-1 px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 focus:bg-white transition-all placeholder:text-slate-400"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="w-10 h-10 rounded-full bg-medical-600 text-white flex items-center justify-center hover:bg-medical-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-medical-500/20 transition-all flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
