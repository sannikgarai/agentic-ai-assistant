-- ============================================================
-- 003_messages.sql
-- Chat messages
-- ============================================================

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    conversation_id UUID NOT NULL
        REFERENCES public.conversations(id)
        ON DELETE CASCADE,

    role TEXT NOT NULL
        CHECK (
            role IN (
                'user',
                'assistant',
                'system',
                'tool'
            )
        ),

    content TEXT NOT NULL,

    message_type TEXT NOT NULL DEFAULT 'text'
        CHECK (
            message_type IN (
                'text',
                'voice',
                'image',
                'document',
                'tool'
            )
        ),

    language TEXT DEFAULT 'en',

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


ALTER TABLE public.messages
ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own messages"
ON public.messages;

CREATE POLICY "Users can view own messages"
ON public.messages
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE conversations.id = messages.conversation_id
        AND conversations.user_id = auth.uid()
    )
);


DROP POLICY IF EXISTS "Users can create own messages"
ON public.messages;

CREATE POLICY "Users can create own messages"
ON public.messages
FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE conversations.id = messages.conversation_id
        AND conversations.user_id = auth.uid()
    )
);


DROP POLICY IF EXISTS "Users can update own messages"
ON public.messages;

CREATE POLICY "Users can update own messages"
ON public.messages
FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE conversations.id = messages.conversation_id
        AND conversations.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE conversations.id = messages.conversation_id
        AND conversations.user_id = auth.uid()
    )
);


DROP POLICY IF EXISTS "Users can delete own messages"
ON public.messages;

CREATE POLICY "Users can delete own messages"
ON public.messages
FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE conversations.id = messages.conversation_id
        AND conversations.user_id = auth.uid()
    )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
ON public.messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_created_at
ON public.messages(created_at);