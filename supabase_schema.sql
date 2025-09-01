-- ================================
-- SUPABASE DATABASE SCHEMA FOR PVP BTC PREDICTION SYSTEM
-- ================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================
-- USERS TABLE
-- ================================
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    x_username VARCHAR(50),
    phantom_address VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- User stats
    total_battles INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    total_winnings DECIMAL(10,2) DEFAULT 0,
    
    -- User preferences
    preferred_bet_amount INTEGER DEFAULT 50,
    notification_enabled BOOLEAN DEFAULT true
);

-- ================================
-- PREDICTIONS TABLE (Queue)
-- ================================
CREATE TABLE predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Prediction details
    predicted_price DECIMAL(10,2) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('above', 'below')),
    bet_amount INTEGER NOT NULL CHECK (bet_amount IN (10, 50, 100)),
    
    -- Current BTC price when prediction was made
    current_btc_price DECIMAL(10,2) NOT NULL,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '4 hours'),
    
    -- Status
    status VARCHAR(20) DEFAULT 'searching' CHECK (status IN ('searching', 'matched', 'expired', 'cancelled')),
    
    -- Metadata
    user_agent TEXT,
    ip_address INET
);

-- ================================
-- BATTLES TABLE
-- ================================
CREATE TABLE battles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Participants
    user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user1_prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    user2_prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    
    -- Battle details
    pot_size INTEGER NOT NULL, -- Total pot (bet_amount * 2)
    battle_start_price DECIMAL(10,2) NOT NULL, -- BTC price when battle started
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Status and resolution
    status VARCHAR(20) DEFAULT 'pending_acceptance' CHECK (status IN ('pending_acceptance', 'active', 'resolved', 'cancelled')),
    winner_id UUID REFERENCES users(id),
    final_btc_price DECIMAL(10,2),
    
    -- Acceptance tracking
    user1_accepted BOOLEAN DEFAULT false,
    user2_accepted BOOLEAN DEFAULT false,
    user1_accepted_at TIMESTAMP WITH TIME ZONE,
    user2_accepted_at TIMESTAMP WITH TIME ZONE,
    
    -- Battle resolution details
    user1_distance DECIMAL(10,4), -- Distance from final price
    user2_distance DECIMAL(10,4),
    
    UNIQUE(user1_prediction_id, user2_prediction_id)
);

-- ================================
-- BATTLE_INVITATIONS TABLE (For 60-second acceptance)
-- ================================
CREATE TABLE battle_invitations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    battle_id UUID REFERENCES battles(id) ON DELETE CASCADE,
    
    -- Invitation details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '60 seconds'),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
    
    -- Response tracking
    user1_response VARCHAR(10) CHECK (user1_response IN ('accepted', 'declined')),
    user2_response VARCHAR(10) CHECK (user2_response IN ('accepted', 'declined')),
    user1_responded_at TIMESTAMP WITH TIME ZONE,
    user2_responded_at TIMESTAMP WITH TIME ZONE
);

-- ================================
-- BATTLE_HISTORY TABLE (For analytics)
-- ================================
CREATE TABLE battle_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    battle_id UUID REFERENCES battles(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Battle outcome
    won BOOLEAN NOT NULL,
    amount_won DECIMAL(10,2) DEFAULT 0,
    amount_lost DECIMAL(10,2) DEFAULT 0,
    
    -- Prediction accuracy
    predicted_price DECIMAL(10,2) NOT NULL,
    actual_price DECIMAL(10,2) NOT NULL,
    prediction_accuracy DECIMAL(5,4), -- Percentage accuracy
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================

-- Predictions indexes
CREATE INDEX idx_predictions_status ON predictions(status);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_searching ON predictions(status) WHERE status = 'searching';

-- Battles indexes
CREATE INDEX idx_battles_status ON battles(status);
CREATE INDEX idx_battles_user1_id ON battles(user1_id);
CREATE INDEX idx_battles_user2_id ON battles(user2_id);
CREATE INDEX idx_battles_ends_at ON battles(ends_at);
CREATE INDEX idx_battles_active ON battles(status) WHERE status = 'active';

-- Battle invitations indexes
CREATE INDEX idx_battle_invitations_expires_at ON battle_invitations(expires_at);
CREATE INDEX idx_battle_invitations_status ON battle_invitations(status);

-- Users indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_x_username ON users(x_username);

-- ================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE battles ENABLE ROW LEVEL SECURITY;
ALTER TABLE battle_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE battle_history ENABLE ROW LEVEL SECURITY;

-- Users can read all user profiles (for opponent info)
CREATE POLICY "Users can read all profiles" ON users
    FOR SELECT USING (true);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid()::text = id::text);

-- Users can read their own predictions and predictions they're battling against
CREATE POLICY "Users can read relevant predictions" ON predictions
    FOR SELECT USING (
        user_id::text = auth.uid()::text OR
        id IN (
            SELECT user1_prediction_id FROM battles WHERE user2_id::text = auth.uid()::text
            UNION
            SELECT user2_prediction_id FROM battles WHERE user1_id::text = auth.uid()::text
        )
    );

-- Users can insert their own predictions
CREATE POLICY "Users can insert own predictions" ON predictions
    FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

-- Users can update their own predictions
CREATE POLICY "Users can update own predictions" ON predictions
    FOR UPDATE USING (user_id::text = auth.uid()::text);

-- Users can read battles they're involved in
CREATE POLICY "Users can read own battles" ON battles
    FOR SELECT USING (
        user1_id::text = auth.uid()::text OR 
        user2_id::text = auth.uid()::text
    );

-- Users can update battles they're involved in (for acceptance)
CREATE POLICY "Users can update own battles" ON battles
    FOR UPDATE USING (
        user1_id::text = auth.uid()::text OR 
        user2_id::text = auth.uid()::text
    );

-- Similar policies for battle_invitations and battle_history
CREATE POLICY "Users can read relevant battle invitations" ON battle_invitations
    FOR SELECT USING (
        battle_id IN (
            SELECT id FROM battles 
            WHERE user1_id::text = auth.uid()::text OR user2_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can read own battle history" ON battle_history
    FOR SELECT USING (user_id::text = auth.uid()::text);

-- ================================
-- FUNCTIONS FOR BUSINESS LOGIC
-- ================================

-- Function to find matching predictions
CREATE OR REPLACE FUNCTION find_matching_prediction(
    p_user_id UUID,
    p_predicted_price DECIMAL,
    p_direction VARCHAR,
    p_bet_amount INTEGER
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    match_id UUID;
    price_tolerance DECIMAL := p_predicted_price * 0.005; -- 0.5% tolerance
    opposite_direction VARCHAR := CASE WHEN p_direction = 'above' THEN 'below' ELSE 'above' END;
BEGIN
    -- Find a matching prediction
    SELECT id INTO match_id
    FROM predictions
    WHERE status = 'searching'
        AND user_id != p_user_id
        AND direction = opposite_direction
        AND bet_amount <= p_bet_amount -- Match with smaller or equal bet
        AND ABS(predicted_price - p_predicted_price) <= price_tolerance
        AND created_at < NOW() -- Older predictions get priority
    ORDER BY created_at ASC
    LIMIT 1;
    
    RETURN match_id;
END;
$$;

-- Function to create a battle from matched predictions
CREATE OR REPLACE FUNCTION create_battle(
    p_prediction1_id UUID,
    p_prediction2_id UUID
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    battle_id UUID;
    pred1 RECORD;
    pred2 RECORD;
    pot_amount INTEGER;
BEGIN
    -- Get prediction details
    SELECT * INTO pred1 FROM predictions WHERE id = p_prediction1_id;
    SELECT * INTO pred2 FROM predictions WHERE id = p_prediction2_id;
    
    -- Calculate pot size (smaller bet amount * 2)
    pot_amount := LEAST(pred1.bet_amount, pred2.bet_amount) * 2;
    
    -- Create battle
    INSERT INTO battles (
        user1_id, user2_id, 
        user1_prediction_id, user2_prediction_id,
        pot_size, battle_start_price, ends_at
    ) VALUES (
        pred1.user_id, pred2.user_id,
        pred1.id, pred2.id,
        pot_amount, pred1.current_btc_price,
        NOW() + INTERVAL '4 hours'
    ) RETURNING id INTO battle_id;
    
    -- Update predictions status
    UPDATE predictions 
    SET status = 'matched' 
    WHERE id IN (p_prediction1_id, p_prediction2_id);
    
    -- Create battle invitation
    INSERT INTO battle_invitations (battle_id) VALUES (battle_id);
    
    RETURN battle_id;
END;
$$;

-- Function to resolve battle
CREATE OR REPLACE FUNCTION resolve_battle(
    p_battle_id UUID,
    p_final_btc_price DECIMAL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    battle RECORD;
    pred1 RECORD;
    pred2 RECORD;
    user1_dist DECIMAL;
    user2_dist DECIMAL;
    winner_user_id UUID;
BEGIN
    -- Get battle and prediction details
    SELECT * INTO battle FROM battles WHERE id = p_battle_id;
    SELECT * INTO pred1 FROM predictions WHERE id = battle.user1_prediction_id;
    SELECT * INTO pred2 FROM predictions WHERE id = battle.user2_prediction_id;
    
    -- Calculate distances
    user1_dist := ABS(p_final_btc_price - pred1.predicted_price);
    user2_dist := ABS(p_final_btc_price - pred2.predicted_price);
    
    -- Determine winner
    winner_user_id := CASE 
        WHEN user1_dist < user2_dist THEN battle.user1_id
        WHEN user2_dist < user1_dist THEN battle.user2_id
        ELSE NULL -- Tie
    END;
    
    -- Update battle
    UPDATE battles SET
        status = 'resolved',
        resolved_at = NOW(),
        final_btc_price = p_final_btc_price,
        winner_id = winner_user_id,
        user1_distance = user1_dist,
        user2_distance = user2_dist
    WHERE id = p_battle_id;
    
    -- Update user stats
    IF winner_user_id IS NOT NULL THEN
        -- Winner stats
        UPDATE users SET
            total_battles = total_battles + 1,
            wins = wins + 1,
            total_winnings = total_winnings + battle.pot_size
        WHERE id = winner_user_id;
        
        -- Loser stats
        UPDATE users SET
            total_battles = total_battles + 1,
            losses = losses + 1
        WHERE id = CASE 
            WHEN winner_user_id = battle.user1_id THEN battle.user2_id 
            ELSE battle.user1_id 
        END;
    ELSE
        -- Tie - both get battle count
        UPDATE users SET
            total_battles = total_battles + 1
        WHERE id IN (battle.user1_id, battle.user2_id);
    END IF;
    
    -- Create battle history records
    INSERT INTO battle_history (battle_id, user_id, won, amount_won, amount_lost, predicted_price, actual_price, prediction_accuracy)
    VALUES 
        (p_battle_id, battle.user1_id, 
         winner_user_id = battle.user1_id,
         CASE WHEN winner_user_id = battle.user1_id THEN battle.pot_size ELSE 0 END,
         CASE WHEN winner_user_id != battle.user1_id THEN pred1.bet_amount ELSE 0 END,
         pred1.predicted_price, p_final_btc_price,
         1.0 - (user1_dist / p_final_btc_price)),
        (p_battle_id, battle.user2_id,
         winner_user_id = battle.user2_id,
         CASE WHEN winner_user_id = battle.user2_id THEN battle.pot_size ELSE 0 END,
         CASE WHEN winner_user_id != battle.user2_id THEN pred2.bet_amount ELSE 0 END,
         pred2.predicted_price, p_final_btc_price,
         1.0 - (user2_dist / p_final_btc_price));
END;
$$;

-- ================================
-- TRIGGERS FOR AUTOMATIC CLEANUP
-- ================================

-- Function to cleanup expired predictions
CREATE OR REPLACE FUNCTION cleanup_expired_predictions()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE predictions 
    SET status = 'expired' 
    WHERE status = 'searching' 
        AND expires_at < NOW();
        
    UPDATE battle_invitations
    SET status = 'expired'
    WHERE status = 'pending'
        AND expires_at < NOW();
END;
$$;

-- Create a trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================
-- SAMPLE DATA FOR TESTING
-- ================================

-- Insert sample users (you can remove this in production)
INSERT INTO users (id, username, x_username, phantom_address) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'TestUser1', 'testuser1', '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM'),
    ('550e8400-e29b-41d4-a716-446655440002', 'TestUser2', 'testuser2', '4vJ9JU1bJJE96FWSJKvHsmmFADCg4gpZQff4P3bkLKi'),
    ('550e8400-e29b-41d4-a716-446655440003', 'TestUser3', 'testuser3', '8qbHbw2BbbTHBW1sbeqakYXVKRQM8Ne7pLK7m6CVfeR');

-- ================================
-- VIEWS FOR EASY QUERYING
-- ================================

-- View for active battles with user details
CREATE VIEW active_battles_view AS
SELECT 
    b.id,
    b.pot_size,
    b.battle_start_price,
    b.ends_at,
    b.status,
    u1.username as user1_username,
    u1.x_username as user1_x_username,
    u2.username as user2_username,
    u2.x_username as user2_x_username,
    p1.predicted_price as user1_prediction,
    p1.direction as user1_direction,
    p2.predicted_price as user2_prediction,
    p2.direction as user2_direction,
    EXTRACT(EPOCH FROM (b.ends_at - NOW())) as seconds_remaining
FROM battles b
JOIN users u1 ON b.user1_id = u1.id
JOIN users u2 ON b.user2_id = u2.id
JOIN predictions p1 ON b.user1_prediction_id = p1.id
JOIN predictions p2 ON b.user2_prediction_id = p2.id
WHERE b.status IN ('pending_acceptance', 'active');

-- View for user leaderboard
CREATE VIEW leaderboard_view AS
SELECT 
    username,
    x_username,
    total_battles,
    wins,
    losses,
    total_winnings,
    CASE 
        WHEN total_battles > 0 THEN ROUND((wins::DECIMAL / total_battles) * 100, 2)
        ELSE 0 
    END as win_percentage,
    created_at
FROM users
WHERE total_battles > 0
ORDER BY total_winnings DESC, win_percentage DESC;

-- ================================
-- COMMENTS AND DOCUMENTATION
-- ================================

COMMENT ON TABLE users IS 'User profiles with stats and preferences';
COMMENT ON TABLE predictions IS 'Individual price predictions (queue entries)';
COMMENT ON TABLE battles IS 'Matched battles between two users';
COMMENT ON TABLE battle_invitations IS '60-second acceptance window for battles';
COMMENT ON TABLE battle_history IS 'Historical record of all battle outcomes';

COMMENT ON FUNCTION find_matching_prediction IS 'Finds a compatible opponent prediction within 0.5% price range';
COMMENT ON FUNCTION create_battle IS 'Creates a new battle from two matched predictions';
COMMENT ON FUNCTION resolve_battle IS 'Resolves a battle and updates user stats';
COMMENT ON FUNCTION cleanup_expired_predictions IS 'Cleans up expired predictions and invitations';
