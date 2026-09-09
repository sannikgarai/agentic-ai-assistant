-- ============================================================
-- 006_applications.sql
-- Government scheme applications
-- ============================================================

CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    scheme_name TEXT NOT NULL,

    portal_url TEXT,

    description TEXT,

    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (
            status IN (
                'draft',
                'preparing',
                'verification_pending',
                'waiting_approval',
                'submitted',
                'under_review',
                'approved',
                'rejected',
                'failed',
                'cancelled'
            )
        ),

    confirmation_number TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    submitted_at TIMESTAMPTZ
);


ALTER TABLE public.applications
ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own applications"
ON public.applications;

CREATE POLICY "Users can view own applications"
ON public.applications
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can create own applications"
ON public.applications;

CREATE POLICY "Users can create own applications"
ON public.applications
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can update own applications"
ON public.applications;

CREATE POLICY "Users can update own applications"
ON public.applications
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can delete own applications"
ON public.applications;

CREATE POLICY "Users can delete own applications"
ON public.applications
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_applications_user_id
ON public.applications(user_id);

CREATE INDEX IF NOT EXISTS idx_applications_status
ON public.applications(status);

CREATE INDEX IF NOT EXISTS idx_applications_scheme_name
ON public.applications(scheme_name);

CREATE INDEX IF NOT EXISTS idx_applications_created_at
ON public.applications(created_at);


-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS update_applications_updated_at
ON public.applications;

CREATE TRIGGER update_applications_updated_at
BEFORE UPDATE ON public.applications
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();