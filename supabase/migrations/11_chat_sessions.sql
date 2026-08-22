-- Migration 11: Chat Sessions Schema

CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE SET NULL,
    title TEXT DEFAULT 'New Consultation',
    channel TEXT DEFAULT 'web' CHECK (channel IN ('web', 'telegram')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.chat_messages
    ADD COLUMN IF NOT EXISTS hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS session_id TEXT;

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
