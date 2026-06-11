-- Fix missing Foreign Key relationship between item_updates and profiles
-- This ensures that Supabase can perform Joins between these tables

-- 1. Ensure the user_id column in item_updates references profiles(id)
-- We use a DO block to make it idempotent
DO $$ 
BEGIN 
    -- Check if the constraint already exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'item_updates_user_id_fkey'
    ) THEN
        ALTER TABLE item_updates 
        ADD CONSTRAINT item_updates_user_id_fkey 
        FOREIGN KEY (user_id) 
        REFERENCES profiles(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- 2. Refresh PostgREST schema cache (Supabase does this automatically usually, but sometimes needs a nudge)
-- NOTIFY pgrst, 'reload schema'; 
