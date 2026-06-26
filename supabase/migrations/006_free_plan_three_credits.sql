-- Free plan = 3 credits (voice=1, video=2). Legacy signups used sessions_limit=2.

ALTER TABLE public.users
  ALTER COLUMN sessions_limit SET DEFAULT 3;

-- Repair brand-new free accounts that never consumed credits.
UPDATE public.users
SET sessions_limit = 3
WHERE COALESCE(plan, 'free') = 'free'
  AND COALESCE(sessions_used, 0) = 0
  AND COALESCE(sessions_limit, 0) < 3
  AND subscription_ends_at IS NULL;

-- Supabase auth trigger (if present) — keep signup rows aligned with backend.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.users (id, email, plan, sessions_used, sessions_limit)
  VALUES (NEW.id, NEW.email, 'free', 0, 3)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
