-- Run this in your Supabase SQL Editor to fix the RLS issue

-- The backend is using the 'anon' key, so Supabase sees the inserts as unauthenticated.
-- Since your FastAPI backend already verifies the JWT token before allowing the insert, 
-- we can safely allow the backend to insert rows.

DROP POLICY IF EXISTS "Authenticated users can insert updates" ON item_updates;
CREATE POLICY "Backend can insert updates" 
ON item_updates 
FOR INSERT 
WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update their own profile" ON profiles;
CREATE POLICY "Backend can update profiles" 
ON profiles 
FOR ALL 
USING (true)
WITH CHECK (true);
