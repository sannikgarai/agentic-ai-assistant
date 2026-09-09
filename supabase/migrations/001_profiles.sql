-- ============================================================
-- 001_profiles.sql
-- User profile table
-- ============================================================

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    full_name TEXT,
    avatar_url TEXT,
    phone TEXT,
    date_of_birth DATE,
    address TEXT,

    preferred_language TEXT NOT NULL DEFAULT 'en',

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Users can view own profile"
ON public.profiles;

CREATE POLICY "Users can view own profile"
ON public.profiles
FOR SELECT
TO authenticated
USING (auth.uid() = id);


DROP POLICY IF EXISTS "Users can create own profile"
ON public.profiles;

CREATE POLICY "Users can create own profile"
ON public.profiles
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = id);


DROP POLICY IF EXISTS "Users can update own profile"
ON public.profiles;

CREATE POLICY "Users can update own profile"
ON public.profiles
FOR UPDATE
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);


DROP POLICY IF EXISTS "Users can delete own profile"
ON public.profiles;

CREATE POLICY "Users can delete own profile"
ON public.profiles
FOR DELETE
TO authenticated
USING (auth.uid() = id);


-- ============================================================
-- UPDATED_AT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS update_profiles_updated_at
ON public.profiles;

CREATE TRIGGER update_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();


-- ============================================================
-- AUTOMATIC PROFILE CREATION
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN

    INSERT INTO public.profiles (
        id,
        full_name,
        avatar_url,
        preferred_language
    )
    VALUES (
        NEW.id,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name'
        ),
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE(
            NEW.raw_user_meta_data->>'preferred_language',
            'en'
        )
    );

    RETURN NEW;

END;
$$;


DROP TRIGGER IF EXISTS on_auth_user_created
ON auth.users;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();