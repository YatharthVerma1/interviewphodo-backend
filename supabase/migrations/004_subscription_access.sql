-- Paid plan access windows (Starter = 1 month, Pro = 2 months).
-- sessions_used / sessions_limit continue to store credits consumed / allowance.
-- Free plan: 3 credits with no expiry (default sessions_limit = 3 on signup).
-- After paid plan expires: plan -> 'free', credits -> 0 (sessions_limit = sessions_used).

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS subscription_starts_at timestamptz,
  ADD COLUMN IF NOT EXISTS subscription_ends_at timestamptz;

COMMENT ON COLUMN users.subscription_starts_at IS
  'UTC start of paid plan access (Starter/Pro). NULL on free plan.';

COMMENT ON COLUMN users.subscription_ends_at IS
  'UTC end of paid plan access. After this, user is downgraded to free with 0 credits remaining.';
