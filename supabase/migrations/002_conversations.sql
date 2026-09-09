-- ============================================================
-- 002_conversations.sql
-- Conversation history
-- ============================================================

CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    title TEXT,

    language TEXT NOT NULL DEFAULT 'en',

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


ALTER TABLE public.conversations
ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own conversations"
ON public.conversations;

CREATE POLICY "Users can view own conversations"
ON public.conversations
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can create own conversations"
ON public.conversations;

CREATE POLICY "Users can create own conversations"
ON public.conversations
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can update own conversations"
ON public.conversations;

CREATE POLICY "Users can update own conversations"
ON public.conversations
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can delete own conversations"
ON public.conversations;

CREATE POLICY "Users can delete own conversations"
ON public.conversations
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_conversations_user_id
ON public.conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_conversations_created_at
ON public.conversations(created_at);


-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS update_conversations_updated_at
ON public.conversations;

CREATE TRIGGER update_conversations_updated_at
BEFORE UPDATE ON public.conversations
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();