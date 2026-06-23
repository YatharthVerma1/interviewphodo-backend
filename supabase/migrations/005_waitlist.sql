-- Waitlist signups from the pre-launch landing page.
-- Separate from auth.users / public.users (product accounts only).
-- Run in Supabase Dashboard → SQL Editor → New query → Run.

-- ─────────────────────────────────────────────────────────────
-- Table
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.waitlist (
  id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  email         text        NOT NULL,
  college       text,
  source        text        NOT NULL DEFAULT 'landing',
  referrer      text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  converted_at  timestamptz,
  CONSTRAINT waitlist_email_not_empty CHECK (char_length(trim(email)) > 0)
);

-- Case-insensitive unique emails (prevents duplicate signups)
CREATE UNIQUE INDEX IF NOT EXISTS waitlist_email_lower_unique
  ON public.waitlist (lower(trim(email)));

CREATE INDEX IF NOT EXISTS waitlist_created_at_idx
  ON public.waitlist (created_at DESC);

CREATE INDEX IF NOT EXISTS waitlist_converted_at_idx
  ON public.waitlist (converted_at)
  WHERE converted_at IS NULL;

COMMENT ON TABLE public.waitlist IS
  'Pre-launch waitlist emails. Not linked to auth until user signs up for the product.';

-- Normalize email on insert/update
CREATE OR REPLACE FUNCTION public.waitlist_normalize_email()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.email := lower(trim(NEW.email));
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS waitlist_normalize_email_trigger ON public.waitlist;
CREATE TRIGGER waitlist_normalize_email_trigger
  BEFORE INSERT OR UPDATE OF email ON public.waitlist
  FOR EACH ROW
  EXECUTE FUNCTION public.waitlist_normalize_email();

-- When someone creates a real product account, mark waitlist row as converted
CREATE OR REPLACE FUNCTION public.mark_waitlist_converted()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  UPDATE public.waitlist
  SET converted_at = now()
  WHERE lower(trim(email)) = lower(trim(NEW.email))
    AND converted_at IS NULL;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_user_created_mark_waitlist ON public.users;
CREATE TRIGGER on_user_created_mark_waitlist
  AFTER INSERT ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION public.mark_waitlist_converted();

-- ─────────────────────────────────────────────────────────────
-- Row Level Security
-- ─────────────────────────────────────────────────────────────
ALTER TABLE public.waitlist ENABLE ROW LEVEL SECURITY;

-- Anyone (logged out or logged in) can join the waitlist — insert only
DROP POLICY IF EXISTS waitlist_public_insert ON public.waitlist;
CREATE POLICY waitlist_public_insert
  ON public.waitlist
  FOR INSERT
  TO anon, authenticated
  WITH CHECK (
    email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
  );

-- No public read/update/delete — view signups in Supabase Dashboard (service role)
-- or from backend scripts using SUPABASE_SERVICE_KEY.
