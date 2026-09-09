-- ============================================================
-- seed.sql
-- Optional development/demo data
-- ============================================================
--
-- IMPORTANT:
-- This file is for DEVELOPMENT/TESTING only.
-- Do NOT use real personal information here.
--
-- The tables profiles, conversations, messages, documents,
-- tasks, applications and verification are protected by RLS.
--
-- Because profiles and other records depend on auth.users,
-- this seed file does not create fake authenticated users.
-- ============================================================


-- ============================================================
-- DEVELOPMENT NOTES
-- ============================================================
--
-- Create a test user first through:
--
-- Supabase Dashboard
-- → Authentication
-- → Users
-- → Add user
--
-- Then use that user's UUID when inserting development data.
--
-- Example:
--
-- DO $$
-- DECLARE
--     test_user_id UUID;
-- BEGIN
--
--     SELECT id
--     INTO test_user_id
--     FROM auth.users
--     WHERE email = 'test@example.com'
--     LIMIT 1;
--
--     IF test_user_id IS NULL THEN
--         RAISE NOTICE 'Test user not found. Skipping seed data.';
--         RETURN;
--     END IF;
--
--     ...
--
-- END $$;
--


-- ============================================================
-- OPTIONAL DEVELOPMENT SEED
-- ============================================================

DO $$
DECLARE
    test_user_id UUID;
    conversation_id UUID;
    application_id UUID;
    task_id UUID;
    document_id UUID;
BEGIN

    -- --------------------------------------------------------
    -- Find an existing test/development user
    -- --------------------------------------------------------

    SELECT id
    INTO test_user_id
    FROM auth.users
    WHERE email = 'test@example.com'
    LIMIT 1;


    -- --------------------------------------------------------
    -- Do nothing if the test user does not exist
    -- --------------------------------------------------------

    IF test_user_id IS NULL THEN

        RAISE NOTICE
            'No test@example.com user found. Seed data was skipped.';

        RETURN;

    END IF;


    -- ========================================================
    -- PROFILE
    -- ========================================================

    INSERT INTO public.profiles (
        id,
        full_name,
        preferred_language,
        metadata
    )
    VALUES (
        test_user_id,
        'Test User',
        'en',
        jsonb_build_object(
            'environment', 'development',
            'seeded', true
        )
    )
    ON CONFLICT (id)
    DO UPDATE SET
        full_name = EXCLUDED.full_name,
        preferred_language = EXCLUDED.preferred_language,
        metadata = EXCLUDED.metadata,
        updated_at = NOW();


    -- ========================================================
    -- CONVERSATION
    -- ========================================================

    INSERT INTO public.conversations (
        user_id,
        title,
        language,
        metadata
    )
    VALUES (
        test_user_id,
        'Government Scheme Assistance',
        'en',
        jsonb_build_object(
            'environment', 'development',
            'seeded', true
        )
    )
    RETURNING id INTO conversation_id;


    -- ========================================================
    -- USER MESSAGE
    -- ========================================================

    INSERT INTO public.messages (
        conversation_id,
        role,
        content,
        message_type,
        language,
        metadata
    )
    VALUES (
        conversation_id,
        'user',
        'Help me find government schemes that I may be eligible for.',
        'text',
        'en',
        jsonb_build_object(
            'seeded', true
        )
    );


    -- ========================================================
    -- ASSISTANT MESSAGE
    -- ========================================================

    INSERT INTO public.messages (
        conversation_id,
        role,
        content,
        message_type,
        language,
        metadata
    )
    VALUES (
        conversation_id,
        'assistant',
        'I can search the available government scheme information and check the eligibility requirements.',
        'text',
        'en',
        jsonb_build_object(
            'seeded', true,
            'source', 'development_seed'
        )
    );


    -- ========================================================
    -- DOCUMENT
    -- ========================================================

    INSERT INTO public.documents (
        user_id,
        file_name,
        file_path,
        document_type,
        mime_type,
        file_size,
        fields,
        processing_status,
        metadata
    )
    VALUES (
        test_user_id,
        'sample_document.pdf',
        test_user_id::text || '/sample_document.pdf',
        'identity_document',
        'application/pdf',
        0,
        '[]'::jsonb,
        'pending',
        jsonb_build_object(
            'seeded', true,
            'environment', 'development'
        )
    )
    RETURNING id INTO document_id;


    -- ========================================================
    -- TASK
    -- ========================================================

    INSERT INTO public.tasks (
        user_id,
        task_type,
        description,
        status,
        conversation_id,
        dependencies,
        metadata
    )
    VALUES (
        test_user_id,
        'scheme_eligibility',
        'Check eligibility for available government schemes.',
        'pending',
        conversation_id,
        '[]'::jsonb,
        jsonb_build_object(
            'seeded', true
        )
    )
    RETURNING id INTO task_id;


    -- ========================================================
    -- APPLICATION
    -- ========================================================

    INSERT INTO public.applications (
        user_id,
        scheme_name,
        description,
        status,
        metadata
    )
    VALUES (
        test_user_id,
        'Sample Government Scheme',
        'Development-only sample application.',
        'draft',
        jsonb_build_object(
            'seeded', true,
            'environment', 'development'
        )
    )
    RETURNING id INTO application_id;


    -- ========================================================
    -- VERIFICATION
    -- ========================================================

    INSERT INTO public.verification (
        user_id,
        verification_type,
        document_ids,
        application_id,
        expected_fields,
        status,
        score,
        results,
        mismatches,
        eligibility,
        message,
        metadata
    )
    VALUES (
        test_user_id,
        'document_verification',
        jsonb_build_array(document_id),
        application_id,
        jsonb_build_object(
            'name', 'Test User'
        ),
        'pending',
        NULL,
        '[]'::jsonb,
        '[]'::jsonb,
        NULL,
        'Development verification record.',
        jsonb_build_object(
            'seeded', true
        )
    );


    -- ========================================================
    -- FINISH
    -- ========================================================

    RAISE NOTICE 'Development seed data inserted successfully.';
    RAISE NOTICE 'User ID: %', test_user_id;
    RAISE NOTICE 'Conversation ID: %', conversation_id;
    RAISE NOTICE 'Document ID: %', document_id;
    RAISE NOTICE 'Task ID: %', task_id;
    RAISE NOTICE 'Application ID: %', application_id;

END $$;