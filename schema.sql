-- ITUM Dining - Consensus Algorithm Database Schema

-- 1. Config table for algorithm parameters
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

INSERT INTO config (key, value, description) VALUES
('algo.time_window_minutes', '30', 'Only votes within this window are considered'),
('algo.decay_lambda', '0.1', 'Controls how fast old votes lose weight'),
('algo.confidence_threshold', '0.60', 'Minimum ratio required to accept a consensus'),
('algo.min_votes', '1', 'Minimum votes before algorithm runs'),
('algo.rep_correct_delta', '0.05', 'Reputation gain for a correct vote'),
('algo.rep_incorrect_delta', '0.02', 'Reputation loss for a wrong vote'),
('algo.rep_min', '0.10', 'Reputation floor'),
('algo.rep_max', '5.00', 'Reputation ceiling'),
('algo.coming_soon_window_min', '1', 'Min allowed ready_in_minutes value'),
('algo.coming_soon_window_max', '120', 'Max allowed ready_in_minutes value')
ON CONFLICT (key) DO NOTHING;

-- 2. Menu items table
CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    current_status TEXT DEFAULT 'available', -- 'available', 'unavailable', 'coming_soon'
    ready_in_minutes INTEGER,
    consensus_updated_at TIMESTAMPTZ DEFAULT NOW(),
    consensus_confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Profiles table to store reputation (linked to auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    division TEXT,
    reputation FLOAT DEFAULT 1.0,
    total_updates INTEGER DEFAULT 0,
    correct_updates INTEGER DEFAULT 0,
    avatar_url TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Item updates (votes)
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

-- Enable RLS (Optional, but recommended)
ALTER TABLE config ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_updates ENABLE ROW LEVEL SECURITY;

-- Simple Policies (Adjust as needed)
CREATE POLICY "Public read config" ON config FOR SELECT USING (true);
CREATE POLICY "Public read menu_items" ON menu_items FOR SELECT USING (true);
CREATE POLICY "Public read profiles" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Public read item_updates" ON item_updates FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert updates" ON item_updates FOR INSERT WITH CHECK (auth.role() = 'authenticated');
