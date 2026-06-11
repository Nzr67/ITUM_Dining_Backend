-- ITUM Dining - Robust Schema with Reliable Joins

-- 1. Ensure Table Structure
CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    canteen TEXT,
    current_status TEXT DEFAULT 'available',
    ready_in_minutes INTEGER,
    consensus_updated_at TIMESTAMPTZ DEFAULT NOW(),
    consensus_confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure UNIQUE constraint on 'name'
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'menu_items_name_key') THEN
        ALTER TABLE menu_items ADD CONSTRAINT menu_items_name_key UNIQUE (name);
    END IF;
END $$;

-- 2. Profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    student_id TEXT,
    division TEXT,
    reputation FLOAT DEFAULT 1.0,
    total_updates INTEGER DEFAULT 0,
    correct_updates INTEGER DEFAULT 0,
    avatar_url TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Item updates (Linking to profiles table for reliable Joins)
CREATE TABLE IF NOT EXISTS item_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES menu_items(id) ON DELETE CASCADE,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    reported_status TEXT NOT NULL,
    ready_in_minutes INTEGER,
    rep_snapshot FLOAT NOT NULL,
    was_correct BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Create Index on canteen
CREATE INDEX IF NOT EXISTS idx_menu_items_canteen ON menu_items(canteen);

-- 5. Config
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- 6. Security (RLS)
ALTER TABLE config ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_updates ENABLE ROW LEVEL SECURITY;

-- Idempotent Policies
DO $$ 
BEGIN
    DROP POLICY IF EXISTS "Public read config" ON config;
    CREATE POLICY "Public read config" ON config FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public read menu_items" ON menu_items;
    CREATE POLICY "Public read menu_items" ON menu_items FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public read profiles" ON profiles;
    CREATE POLICY "Public read profiles" ON profiles FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Public read item_updates" ON item_updates;
    CREATE POLICY "Public read item_updates" ON item_updates FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Users can update their own profile" ON profiles;
    CREATE POLICY "Users can update their own profile" ON profiles FOR ALL USING (auth.uid() = id);

    DROP POLICY IF EXISTS "Authenticated users can insert updates" ON item_updates;
    CREATE POLICY "Authenticated users can insert updates" ON item_updates FOR INSERT WITH CHECK (auth.role() = 'authenticated');
END $$;

-- 7. Seed Data
INSERT INTO config (key, value) VALUES 
('algo.time_window_minutes', '30'), 
('algo.decay_lambda', '0.1'), 
('algo.confidence_threshold', '0.60'), 
('algo.min_votes', '1')
ON CONFLICT (key) DO NOTHING;

INSERT INTO menu_items (name, description, canteen) VALUES 
('Vegetable Food', 'Fresh mix of seasonal vegetables', 'goda'),
('Fish Food', 'Fried fish with spicy sambol', 'vala'),
('Chicken Food', 'Curry chicken with rice', 'civil'),
('Egg Food', 'Boiled or fried egg', 'goda'),
('String Hoppers', 'With coconut sambol and dhal', 'goda'),
('Fried Rice', 'Basmati rice with chicken', 'vala'),
('Kottu Roti', 'Chopped roti with spices', 'civil')
ON CONFLICT (name) DO UPDATE SET 
    description = EXCLUDED.description,
    canteen = EXCLUDED.canteen;
