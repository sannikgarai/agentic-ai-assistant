-- ============================================================
-- 004_documents.sql
-- User uploaded documents
-- ============================================================

CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    file_name TEXT NOT NULL,

    file_path TEXT NOT NULL,

    document_type TEXT,

    mime_type TEXT,

    file_size BIGINT,

    fields JSONB NOT NULL DEFAULT '[]'::jsonb,

    extracted_text TEXT,

    processing_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            processing_status IN (
                'pending',
                'processing',
                'completed',
                'failed'
            )
        ),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


ALTER TABLE public.documents
ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own documents"
ON public.documents;

CREATE POLICY "Users can view own documents"
ON public.documents
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can upload own documents"
ON public.documents;

CREATE POLICY "Users can upload own documents"
ON public.documents
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can update own documents"
ON public.documents;

CREATE POLICY "Users can update own documents"
ON public.documents
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can delete own documents"
ON public.documents;

CREATE POLICY "Users can delete own documents"
ON public.documents
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_documents_user_id
ON public.documents(user_id);

CREATE INDEX IF NOT EXISTS idx_documents_document_type
ON public.documents(document_type);

CREATE INDEX IF NOT EXISTS idx_documents_processing_status
ON public.documents(processing_status);

CREATE INDEX IF NOT EXISTS idx_documents_created_at
ON public.documents(created_at);


-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS update_documents_updated_at
ON public.documents;

CREATE TRIGGER update_documents_updated_at
BEFORE UPDATE ON public.documents
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();