-- Migration 12: Telegram Accounts Schema

CREATE TABLE IF NOT EXISTS public.telegram_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    telegram_id TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'unlinked')),
    linked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telegram_accounts_user_id ON public.telegram_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_accounts_telegram_id ON public.telegram_accounts(telegram_id);
