import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { User as UserIcon, Mail, Phone, Smartphone, Shield, CheckCircle2 } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, linkTelegram } = useAuth();
  const { showToast } = useToast();

  const [telegramId, setTelegramId] = useState(user?.telegram_id || '');
  const [saving, setSaving] = useState(false);

  const handleSaveTelegram = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const success = await linkTelegram(telegramId);
    if (success) {
      showToast('Telegram account linked successfully!', 'success');
    } else {
      showToast('Failed to link Telegram account', 'error');
    }
    setSaving(false);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-16">
      <div className="bg-gradient-to-r from-medical-900 to-tealmed-800 rounded-3xl p-8 text-white shadow-xl space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Patient Profile & Identity</h1>
        <p className="text-xs sm:text-sm text-slate-300">Manage account information and Telegram integration.</p>
      </div>

      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
          <div className="w-16 h-16 rounded-full bg-medical-100 text-medical-700 flex items-center justify-center font-extrabold text-2xl border-2 border-medical-200">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{user?.name}</h2>
            <p className="text-xs text-slate-500">{user?.email}</p>
            <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-medical-50 text-medical-700 uppercase">
              {user?.role} Account
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Account Identity Details</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Internal User ID (UUID)</span>
              <p className="font-mono text-slate-800 font-bold break-all">{user?.id}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
              <span className="text-slate-400 font-medium">Email Address</span>
              <p className="font-semibold text-slate-800">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Telegram Mapping Section */}
        <form onSubmit={handleSaveTelegram} className="pt-4 border-t border-slate-100 space-y-3">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-sky-500" />
            Link Telegram Identity
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Connecting your Telegram User ID associates Telegram bot messages with this primary application user account.
          </p>

          <div className="flex gap-2 max-w-md">
            <input
              type="text"
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              placeholder="e.g. 98765432"
              className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-sky-500"
            />
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow transition-all"
            >
              {saving ? 'Saving...' : 'Save Telegram ID'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
