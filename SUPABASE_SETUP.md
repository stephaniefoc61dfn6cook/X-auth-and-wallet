# 🗄️ Supabase Database Setup Guide

## 📋 **Complete Setup Instructions**

### **Step 1: Create Supabase Project**

1. **Go to [supabase.com](https://supabase.com)**
2. **Sign up/Login** with GitHub
3. **Create New Project**
   - Project Name: `x-connect-pvp`
   - Database Password: Generate a strong password
   - Region: Choose closest to your users
4. **Wait for project initialization** (2-3 minutes)

### **Step 2: Run Database Schema**

1. **Go to SQL Editor** in your Supabase dashboard
2. **Create new query**
3. **Copy and paste** the entire contents of `supabase_schema.sql`
4. **Run the query** (this creates all tables, functions, and policies)

### **Step 3: Get API Keys**

1. **Go to Project Settings** → **API**
2. **Copy these values:**
   - Project URL: `https://your-project-id.supabase.co`
   - Anon Public Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - Service Role Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (keep secret!)

### **Step 4: Update Environment Variables**

#### **For Local Development (.env file):**
```env
# Existing variables...
X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret
X_REDIRECT_URI=http://localhost:5000/auth/x/callback
FLASK_SECRET_KEY=local-dev-secret
FLASK_ENV=development

# Add Supabase configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### **For Production (Render Environment Variables):**
1. **Go to your Render dashboard**
2. **Select your service**
3. **Go to Environment**
4. **Add these variables:**
   - `SUPABASE_URL` = `https://your-project-id.supabase.co`
   - `SUPABASE_ANON_KEY` = `your-anon-key`
   - `SUPABASE_SERVICE_KEY` = `your-service-key`

### **Step 5: Update Frontend Configuration**

Edit `supabase_config.js` to use your actual values:

```javascript
// Replace these with your actual Supabase values
const SUPABASE_CONFIG = {
    url: 'https://your-project-id.supabase.co',
    anonKey: 'your-anon-key-here',
    serviceKey: 'your-service-key-here' // Only for server-side
};
```

## 🎯 **Database Schema Overview**

### **Tables Created:**
- **`users`** - User profiles with stats and preferences
- **`predictions`** - Individual price predictions (queue entries)
- **`battles`** - Matched battles between two users  
- **`battle_invitations`** - 60-second acceptance window for battles
- **`battle_history`** - Historical record of all battle outcomes

### **Key Features:**
- ✅ **Row Level Security (RLS)** - Users can only see their own data
- ✅ **Real-time Subscriptions** - Live updates for battles and matches
- ✅ **Automatic Matching** - 0.5% price tolerance algorithm
- ✅ **Battle Resolution** - Automatic winner determination
- ✅ **User Statistics** - Win/loss tracking and leaderboards
- ✅ **Data Cleanup** - Automatic expired data removal

### **Functions Available:**
- `find_matching_prediction()` - Smart opponent matching
- `create_battle()` - Battle creation from matched predictions
- `resolve_battle()` - Battle resolution and stat updates
- `cleanup_expired_predictions()` - Cleanup expired data

## 🧪 **Testing the Database**

### **1. Test Basic Functionality:**
```sql
-- Check if tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Insert test user
INSERT INTO users (username) VALUES ('TestUser123');

-- Check users table
SELECT * FROM users;
```

### **2. Test PvP Functions:**
```sql
-- Test prediction creation
INSERT INTO predictions (user_id, predicted_price, direction, bet_amount, current_btc_price)
VALUES (
    (SELECT id FROM users LIMIT 1),
    45000, 'above', 50, 44500
);

-- Check predictions
SELECT * FROM predictions;
```

### **3. Test Real-time Features:**
1. **Open Supabase Dashboard** → **Table Editor**
2. **Insert a new prediction** manually
3. **Watch for real-time updates** in your app

## 🔧 **Local Development Testing**

### **1. Start Local Server:**
```bash
python run_local.py
```

### **2. Test PvP Flow:**
1. **Open** http://localhost:5000
2. **Click "Play Now"** on PVP Ranked
3. **Create a prediction** and enter queue
4. **Check browser console** for Supabase logs
5. **Check Supabase dashboard** for new data

### **3. Debug Common Issues:**

#### **"Supabase not initialized"**
- Check if `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set
- Verify the keys are correct in Supabase dashboard
- Check browser console for detailed errors

#### **"RLS Policy Error"**
- Make sure you ran the complete schema SQL
- Check that RLS policies were created properly
- Verify user authentication is working

#### **"Real-time not working"**
- Check that real-time is enabled in Supabase project settings
- Verify subscription code is running without errors
- Check network tab for WebSocket connections

## 🚀 **Production Deployment**

### **1. Update Production Environment:**
1. **Add Supabase variables** to Render
2. **Commit and push** your changes
3. **Wait for auto-deployment**

### **2. Test Production:**
1. **Visit your production URL**
2. **Test PvP functionality**
3. **Check Supabase logs** for any errors

### **3. Monitor Performance:**
- **Supabase Dashboard** → **Logs** → **Database**
- **Check API usage** and rate limits
- **Monitor real-time connections**

## 🎮 **How PvP Works with Supabase**

### **Real Multiplayer Flow:**
1. **User A** creates prediction → stored in `predictions` table
2. **Database function** automatically searches for matches
3. **User B** creates matching prediction → battle created in `battles` table
4. **Real-time notification** sent to both users
5. **Battle acceptance modal** appears with 60-second timer
6. **Both users accept** → battle becomes active
7. **After 4 hours** → battle auto-resolves with real BTC price
8. **Winner determined** → stats updated, history recorded

### **Key Advantages:**
- ✅ **Real multiplayer** - No more simulated opponents
- ✅ **Persistent data** - Battles survive page refreshes
- ✅ **Real-time updates** - Instant notifications
- ✅ **Scalable** - Handles thousands of concurrent users
- ✅ **Reliable** - Database-backed with ACID transactions
- ✅ **Secure** - Row Level Security protects user data

## 🏆 **Advanced Features**

### **Leaderboard:**
```sql
-- Get top players
SELECT * FROM leaderboard_view LIMIT 10;
```

### **Battle History:**
```sql
-- Get user's battle history
SELECT * FROM battle_history WHERE user_id = 'user-uuid';
```

### **Active Battles:**
```sql
-- Get all active battles
SELECT * FROM active_battles_view;
```

## 🔍 **Troubleshooting**

### **Common Errors:**

#### **"Anonymous access is disabled"**
- Enable anonymous access in Supabase Auth settings
- Or implement proper user authentication

#### **"Function not found"**
- Re-run the schema SQL to create functions
- Check function names match exactly

#### **"Permission denied"**
- Check RLS policies are correctly set up
- Verify user has proper permissions

### **Debug Steps:**
1. **Check browser console** for JavaScript errors
2. **Check Supabase logs** for database errors  
3. **Test API endpoints** directly in Supabase dashboard
4. **Verify environment variables** are loaded correctly

## 🎉 **Success Indicators**

When everything is working correctly, you should see:
- ✅ **Console logs**: "✅ PvP System initialized successfully"
- ✅ **Real battles**: Multiple users can battle each other
- ✅ **Data persistence**: Battles survive page refreshes
- ✅ **Real-time updates**: Instant match notifications
- ✅ **Accurate resolution**: Battles resolve with real BTC prices

Your PvP prediction system is now powered by a robust, scalable database! 🚀⚔️💰
