-- User onboarding: target role + interview timeline (Replit signup flow)
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS target_role TEXT,
  ADD COLUMN IF NOT EXISTS interview_timeline TEXT;

-- Optional: store role used per session for memory scoping
ALTER TABLE public.sessions
  ADD COLUMN IF NOT EXISTS target_role TEXT;
