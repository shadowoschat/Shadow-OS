-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;

-- Users Table Policies
-- Users can view their own profile
CREATE POLICY "Users can view own profile" 
ON users FOR SELECT 
USING (auth.uid() = id);

-- Users can update their own profile (except role)
CREATE POLICY "Users can update own profile" 
ON users FOR UPDATE 
USING (auth.uid() = id);

-- Chat History Policies
CREATE POLICY "Users can view own chat history" 
ON chat_history FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chat history" 
ON chat_history FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chat history" 
ON chat_history FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own chat history" 
ON chat_history FOR DELETE 
USING (auth.uid() = user_id);

-- Memory Policies
CREATE POLICY "Users can view own memory" 
ON memory FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own memory" 
ON memory FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own memory" 
ON memory FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own memory" 
ON memory FOR DELETE 
USING (auth.uid() = user_id);

-- Login History Policies
CREATE POLICY "Users can view own login history" 
ON login_history FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own login history" 
ON login_history FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Devices Policies
CREATE POLICY "Users can view own devices" 
ON devices FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own devices" 
ON devices FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own devices" 
ON devices FOR DELETE 
USING (auth.uid() = user_id);

-- Admin Policies (Assuming role='admin' in public.users)
-- Create a helper function to check if the current user is an admin
CREATE OR REPLACE FUNCTION is_admin() RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
  );
$$ LANGUAGE sql SECURITY DEFINER;

-- Admin can view/modify all users
CREATE POLICY "Admins can view all users" ON users FOR SELECT USING (is_admin());
CREATE POLICY "Admins can update all users" ON users FOR UPDATE USING (is_admin());
CREATE POLICY "Admins can delete all users" ON users FOR DELETE USING (is_admin());

-- Admin can view all chat history
CREATE POLICY "Admins can view all chat history" ON chat_history FOR SELECT USING (is_admin());

-- Admin can view all memories
CREATE POLICY "Admins can view all memory" ON memory FOR SELECT USING (is_admin());

-- Admin can view all login history
CREATE POLICY "Admins can view all login history" ON login_history FOR SELECT USING (is_admin());

-- Admin can view all admin events
CREATE POLICY "Admins can view all admin events" ON admin_events FOR SELECT USING (is_admin());
CREATE POLICY "Admins can insert admin events" ON admin_events FOR INSERT WITH CHECK (is_admin());
