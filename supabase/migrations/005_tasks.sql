-- ============================================================
-- 005_tasks.sql
-- Agent tasks and subtasks
-- ============================================================

CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES auth.users(id)
        ON DELETE CASCADE,

    task_type TEXT NOT NULL,

    description TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'running',
                'completed',
                'failed',
                'cancelled',
                'waiting_approval'
            )
        ),

    conversation_id UUID
        REFERENCES public.conversations(id)
        ON DELETE SET NULL,

    parent_task_id UUID
        REFERENCES public.tasks(id)
        ON DELETE SET NULL,

    dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,

    result JSONB,

    error_message TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


ALTER TABLE public.tasks
ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own tasks"
ON public.tasks;

CREATE POLICY "Users can view own tasks"
ON public.tasks
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can create own tasks"
ON public.tasks;

CREATE POLICY "Users can create own tasks"
ON public.tasks
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can update own tasks"
ON public.tasks;

CREATE POLICY "Users can update own tasks"
ON public.tasks
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "Users can delete own tasks"
ON public.tasks;

CREATE POLICY "Users can delete own tasks"
ON public.tasks
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_tasks_user_id
ON public.tasks(user_id);

CREATE INDEX IF NOT EXISTS idx_tasks_status
ON public.tasks(status);

CREATE INDEX IF NOT EXISTS idx_tasks_conversation_id
ON public.tasks(conversation_id);

CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id
ON public.tasks(parent_task_id);

CREATE INDEX IF NOT EXISTS idx_tasks_created_at
ON public.tasks(created_at);


-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS update_tasks_updated_at
ON public.tasks;

CREATE TRIGGER update_tasks_updated_at
BEFORE UPDATE ON public.tasks
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();