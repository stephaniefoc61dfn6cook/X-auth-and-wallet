// ================================
// SUPABASE CONFIGURATION AND CLIENT
// ================================

// Supabase configuration - Add these to your .env file
const SUPABASE_CONFIG = {
    url: process.env.SUPABASE_URL || 'https://your-project.supabase.co',
    anonKey: process.env.SUPABASE_ANON_KEY || 'your-anon-key',
    serviceKey: process.env.SUPABASE_SERVICE_KEY || 'your-service-key' // Only for server-side operations
};

// Initialize Supabase client (for frontend)
let supabaseClient = null;

function initializeSupabase() {
    if (typeof window !== 'undefined' && window.supabase) {
        supabaseClient = window.supabase.createClient(
            SUPABASE_CONFIG.url,
            SUPABASE_CONFIG.anonKey,
            {
                auth: {
                    autoRefreshToken: true,
                    persistSession: true,
                    detectSessionInUrl: false
                },
                realtime: {
                    params: {
                        eventsPerSecond: 10
                    }
                }
            }
        );
        console.log('✅ Supabase client initialized');
        return true;
    }
    console.error('❌ Supabase not loaded');
    return false;
}

// ================================
// DATABASE HELPER FUNCTIONS
// ================================

class PvPDatabase {
    constructor() {
        this.client = supabaseClient;
        this.currentUser = null;
        this.subscriptions = new Map();
    }

    // ================================
    // USER MANAGEMENT
    // ================================
    
    async createOrUpdateUser(userData) {
        try {
            const { data, error } = await this.client
                .from('users')
                .upsert({
                    id: userData.id,
                    username: userData.username,
                    x_username: userData.x_username,
                    phantom_address: userData.phantom_address
                }, {
                    onConflict: 'id',
                    returning: 'representation'
                });

            if (error) throw error;
            this.currentUser = data[0];
            return data[0];
        } catch (error) {
            console.error('Error creating/updating user:', error);
            throw error;
        }
    }

    async getUserProfile(userId) {
        try {
            const { data, error } = await this.client
                .from('users')
                .select('*')
                .eq('id', userId)
                .single();

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error fetching user profile:', error);
            throw error;
        }
    }

    async getLeaderboard(limit = 10) {
        try {
            const { data, error } = await this.client
                .from('leaderboard_view')
                .select('*')
                .limit(limit);

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error fetching leaderboard:', error);
            throw error;
        }
    }

    // ================================
    // PREDICTION MANAGEMENT
    // ================================

    async createPrediction(predictionData) {
        try {
            const { data, error } = await this.client
                .from('predictions')
                .insert({
                    user_id: this.currentUser.id,
                    predicted_price: predictionData.price,
                    direction: predictionData.direction,
                    bet_amount: predictionData.betAmount,
                    current_btc_price: predictionData.currentBtcPrice
                })
                .select()
                .single();

            if (error) throw error;
            
            // Try to find a match immediately
            await this.findAndCreateMatch(data.id);
            
            return data;
        } catch (error) {
            console.error('Error creating prediction:', error);
            throw error;
        }
    }

    async getUserPredictions(userId) {
        try {
            const { data, error } = await this.client
                .from('predictions')
                .select('*')
                .eq('user_id', userId)
                .eq('status', 'searching')
                .order('created_at', { ascending: false });

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error fetching user predictions:', error);
            throw error;
        }
    }

    async cancelPrediction(predictionId) {
        try {
            const { data, error } = await this.client
                .from('predictions')
                .update({ status: 'cancelled' })
                .eq('id', predictionId)
                .eq('user_id', this.currentUser.id)
                .select()
                .single();

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error cancelling prediction:', error);
            throw error;
        }
    }

    // ================================
    // MATCHMAKING
    // ================================

    async findAndCreateMatch(predictionId) {
        try {
            // Get the prediction details
            const { data: prediction, error: predError } = await this.client
                .from('predictions')
                .select('*')
                .eq('id', predictionId)
                .single();

            if (predError) throw predError;

            // Use the database function to find a match
            const { data: matchId, error: matchError } = await this.client
                .rpc('find_matching_prediction', {
                    p_user_id: prediction.user_id,
                    p_predicted_price: prediction.predicted_price,
                    p_direction: prediction.direction,
                    p_bet_amount: prediction.bet_amount
                });

            if (matchError) throw matchError;

            if (matchId) {
                // Create battle
                const { data: battleId, error: battleError } = await this.client
                    .rpc('create_battle', {
                        p_prediction1_id: predictionId,
                        p_prediction2_id: matchId
                    });

                if (battleError) throw battleError;
                return battleId;
            }

            return null; // No match found
        } catch (error) {
            console.error('Error in matchmaking:', error);
            throw error;
        }
    }

    // ================================
    // BATTLE MANAGEMENT
    // ================================

    async getUserBattles(userId) {
        try {
            const { data, error } = await this.client
                .from('active_battles_view')
                .select('*')
                .or(`user1_id.eq.${userId},user2_id.eq.${userId}`)
                .order('created_at', { ascending: false });

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error fetching user battles:', error);
            throw error;
        }
    }

    async acceptBattle(battleId, userId) {
        try {
            // Determine if user1 or user2
            const { data: battle, error: battleError } = await this.client
                .from('battles')
                .select('user1_id, user2_id')
                .eq('id', battleId)
                .single();

            if (battleError) throw battleError;

            const isUser1 = battle.user1_id === userId;
            const updateField = isUser1 ? 'user1_accepted' : 'user2_accepted';
            const timestampField = isUser1 ? 'user1_accepted_at' : 'user2_accepted_at';

            // Update battle acceptance
            const { data, error } = await this.client
                .from('battles')
                .update({
                    [updateField]: true,
                    [timestampField]: new Date().toISOString()
                })
                .eq('id', battleId)
                .select()
                .single();

            if (error) throw error;

            // Check if both users accepted
            if (data.user1_accepted && data.user2_accepted) {
                await this.client
                    .from('battles')
                    .update({
                        status: 'active',
                        started_at: new Date().toISOString()
                    })
                    .eq('id', battleId);

                // Update invitation status
                await this.client
                    .from('battle_invitations')
                    .update({ status: 'accepted' })
                    .eq('battle_id', battleId);
            }

            return data;
        } catch (error) {
            console.error('Error accepting battle:', error);
            throw error;
        }
    }

    async declineBattle(battleId, userId) {
        try {
            // Update battle status to cancelled
            const { data, error } = await this.client
                .from('battles')
                .update({ status: 'cancelled' })
                .eq('id', battleId)
                .select()
                .single();

            if (error) throw error;

            // Update invitation status
            await this.client
                .from('battle_invitations')
                .update({ status: 'declined' })
                .eq('battle_id', battleId);

            // Reset predictions back to searching
            await this.client
                .from('predictions')
                .update({ status: 'searching' })
                .in('id', [data.user1_prediction_id, data.user2_prediction_id]);

            return data;
        } catch (error) {
            console.error('Error declining battle:', error);
            throw error;
        }
    }

    async resolveBattle(battleId, finalBtcPrice) {
        try {
            const { data, error } = await this.client
                .rpc('resolve_battle', {
                    p_battle_id: battleId,
                    p_final_btc_price: finalBtcPrice
                });

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error resolving battle:', error);
            throw error;
        }
    }

    // ================================
    // REAL-TIME SUBSCRIPTIONS
    // ================================

    subscribeToUserBattles(userId, callback) {
        const subscription = this.client
            .channel(`user-battles-${userId}`)
            .on(
                'postgres_changes',
                {
                    event: '*',
                    schema: 'public',
                    table: 'battles',
                    filter: `user1_id=eq.${userId}`,
                },
                callback
            )
            .on(
                'postgres_changes',
                {
                    event: '*',
                    schema: 'public',
                    table: 'battles',
                    filter: `user2_id=eq.${userId}`,
                },
                callback
            )
            .subscribe();

        this.subscriptions.set(`user-battles-${userId}`, subscription);
        return subscription;
    }

    subscribeToBattleInvitations(userId, callback) {
        const subscription = this.client
            .channel(`battle-invitations-${userId}`)
            .on(
                'postgres_changes',
                {
                    event: 'INSERT',
                    schema: 'public',
                    table: 'battle_invitations',
                },
                async (payload) => {
                    // Get battle details to check if user is involved
                    const { data: battle } = await this.client
                        .from('battles')
                        .select('user1_id, user2_id')
                        .eq('id', payload.new.battle_id)
                        .single();

                    if (battle && (battle.user1_id === userId || battle.user2_id === userId)) {
                        callback(payload);
                    }
                }
            )
            .subscribe();

        this.subscriptions.set(`battle-invitations-${userId}`, subscription);
        return subscription;
    }

    subscribeToMatchmaking(userId, callback) {
        const subscription = this.client
            .channel(`matchmaking-${userId}`)
            .on(
                'postgres_changes',
                {
                    event: 'UPDATE',
                    schema: 'public',
                    table: 'predictions',
                    filter: `user_id=eq.${userId}`,
                },
                (payload) => {
                    if (payload.new.status === 'matched') {
                        callback(payload);
                    }
                }
            )
            .subscribe();

        this.subscriptions.set(`matchmaking-${userId}`, subscription);
        return subscription;
    }

    unsubscribe(channelName) {
        const subscription = this.subscriptions.get(channelName);
        if (subscription) {
            subscription.unsubscribe();
            this.subscriptions.delete(channelName);
        }
    }

    unsubscribeAll() {
        for (const [channelName, subscription] of this.subscriptions) {
            subscription.unsubscribe();
        }
        this.subscriptions.clear();
    }

    // ================================
    // UTILITY FUNCTIONS
    // ================================

    async cleanupExpiredData() {
        try {
            const { error } = await this.client.rpc('cleanup_expired_predictions');
            if (error) throw error;
        } catch (error) {
            console.error('Error cleaning up expired data:', error);
        }
    }

    async getBattleHistory(userId, limit = 20) {
        try {
            const { data, error } = await this.client
                .from('battle_history')
                .select('*')
                .eq('user_id', userId)
                .order('created_at', { ascending: false })
                .limit(limit);

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error fetching battle history:', error);
            throw error;
        }
    }
}

// ================================
// GLOBAL INSTANCE
// ================================

// Global database instance
let pvpDatabase = null;

function initializePvPDatabase() {
    if (supabaseClient) {
        pvpDatabase = new PvPDatabase();
        console.log('✅ PvP Database initialized');
        return pvpDatabase;
    }
    console.error('❌ Supabase client not initialized');
    return null;
}

// Export for use in other files
if (typeof window !== 'undefined') {
    window.PvPDatabase = PvPDatabase;
    window.initializePvPDatabase = initializePvPDatabase;
    window.initializeSupabase = initializeSupabase;
}
