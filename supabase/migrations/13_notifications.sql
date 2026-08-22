-- Migration 13: Notifications Schema

CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    hospital_id TEXT REFERENCES public.hospitals(id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN (
        'appointment_booked',
        'appointment_confirmed',
        'appointment_reminder',
        'appointment_cancelled',
        'appointment_rescheduled',
        'schedule_changed',
        'review_request'
    )),
    channel TEXT DEFAULT 'web' CHECK (channel IN ('web', 'telegram', 'email')),
    payload JSONB DEFAULT '{}'::jsonb,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON public.notifications(status);
