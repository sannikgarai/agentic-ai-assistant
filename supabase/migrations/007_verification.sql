-- ============================================================
-- 007_verification.sql
-- Document/application verification
-- ============================================================

CREATE TABLE IF NOT EXISTS public.verification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    verification_type TEXT NOT NULL,

    document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,

    application_id UUID
        REFERENCES public.applications(id)
        ON DELETE SET NULL,

    expected_fields JSONB NOT NULL DEFAULT '{}'::jsonb,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'verified',
                'mismatch',
                'failed',
                'ineligible',
                'manual_review'
            )
        ),

    score NUMERIC(5,4)
        CHECK (
            score >= 0
            AND score <= 1
        ),

    results JSONB NOT NULL DEFAULT '[]'::jsonb,

    mismatches JSONB NOT NULL DEFAULT '[]'::jsonb,

    eligibility JSONB,

    message TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


ALTER TABLE public.verification
ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own verification"
ON public.verification;

CREATE POLICY "Users can view own verification"
ON public.verification
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can create own verification"
ON public.verification;

CREATE POLICY "Users can create own verification"
ON public.verification
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can update own verification"
ON public.verification;

CREATE POLICY "Users can update own verification"
ON public.verification
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can delete own verification"
ON public.verification;

CREATE POLICY "Users can delete own verification"
ON public.verification
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_verification_user_id
ON public.verification(user_id);

CREATE INDEX IF NOT EXISTS idx_verification_status
ON public.verification(status);

CREATE INDEX IF NOT EXISTS idx_verification_application_id
ON public.verification(application_id);

CREATE INDEX IF NOT EXISTS idx_verification_type
ON public.verification(verification_type);

CREATE INDEX IF NOT EXISTS idx_verification_created_at
ON public.verification(created_at);