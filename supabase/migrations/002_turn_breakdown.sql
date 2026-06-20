-- Add per-turn feedback breakdown to reports (Priority 2)
-- Run in Supabase SQL Editor: interviewphodo project → SQL → New query

ALTER TABLE public.reports
ADD COLUMN IF NOT EXISTS turn_breakdown jsonb DEFAULT '[]'::jsonb;

COMMENT ON COLUMN public.reports.turn_breakdown IS
  'Per-question scores and feedback: [{turn, phase, score, feedback, student_preview, ...}]';
