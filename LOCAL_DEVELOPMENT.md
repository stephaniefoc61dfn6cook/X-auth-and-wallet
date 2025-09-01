# 🖥️ Local Development Guide

## 🚀 How to Run Your Website Locally

### **Step 1: Install Dependencies**
```bash
python -m pip install -r requirements.txt
```

### **Step 2: Create Environment Variables**
Create a `.env` file in your project root with:

```env
# X (Twitter) API Configuration
X_CLIENT_ID=your-x-client-id-here
X_CLIENT_SECRET=your-x-client-secret-here
X_REDIRECT_URI=http://localhost:5000/auth/x/callback

# Flask Configuration
FLASK_SECRET_KEY=local-dev-secret-key
FLASK_ENV=development
```

**To get X API credentials:**
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Select your app → "Keys and Tokens"
3. Copy Client ID and Client Secret
4. In "Authentication settings", add: `http://localhost:5000/auth/x/callback`

### **Step 3: Run the Local Server**
```bash
python app.py
```

### **Step 4: Access Your Website**
Open your browser and go to:
- **Main Site**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **API Test**: http://localhost:5000/api/test
- **BTC Stats**: http://localhost:5000/api/btc/stats

## 🔧 Local Development Features

### **✅ What Works Locally:**
- ✅ **Gaming Interface** - Full UI with all features
- ✅ **BTC Live Prices** - Real API data from free sources
- ✅ **BTC Charts** - All timeframes (15m, 30m, 1h, 4h)
- ✅ **TradingView Integration** - Advanced chart modal
- ✅ **Phantom Wallet** - If you have Phantom extension installed
- ✅ **X OAuth** - If you configure X API credentials

### **⚠️ Local vs Production Differences:**
- **HTTPS**: Local uses HTTP, production uses HTTPS
- **Domain**: Local uses localhost:5000, production uses your domain
- **X OAuth**: Needs separate callback URL for local development
- **SSL**: Some wallet features work better with HTTPS

## 🧪 Testing Checklist

### **Basic Functionality:**
- [ ] Website loads at http://localhost:5000
- [ ] Welcome modal appears and can be dismissed
- [ ] BTC price loads and updates
- [ ] BTC chart displays with data
- [ ] Time filters work (15m, 30m, 1h, 4h)
- [ ] Advanced Chart button opens TradingView modal

### **Authentication Testing:**
- [ ] X Connect button works (if configured)
- [ ] Phantom Wallet Connect works (if extension installed)
- [ ] Play Now buttons show authentication status
- [ ] Sign Message works with Phantom wallet

### **API Endpoints:**
- [ ] `/health` returns healthy status
- [ ] `/api/test` returns success message
- [ ] `/api/btc/stats` returns BTC price data
- [ ] `/api/btc/history?timeframe=1h` returns chart data

## 🐛 Troubleshooting

### **Common Issues:**

**"Module not found" errors:**
```bash
python -m pip install -r requirements.txt
```

**"X OAuth not working":**
- Check X_CLIENT_ID and X_CLIENT_SECRET in .env
- Add `http://localhost:5000/auth/x/callback` to X Developer Portal
- Make sure .env file is in the same directory as app.py

**"Phantom wallet not found":**
- Install Phantom browser extension
- Make sure you're using a supported browser (Chrome, Firefox, Edge)

**"BTC chart not loading":**
- Check browser console for errors
- Try different timeframes (15m, 30m, 1h, 4h)
- Check `/api/btc/history?timeframe=1h` directly

**"Port already in use":**
- Another app is using port 5000
- Kill other Flask apps or change port in app.py

### **Debug Mode:**
The local server runs in debug mode, which means:
- ✅ **Auto-reload** when you change code
- ✅ **Detailed error messages** in browser
- ✅ **Console logging** for debugging
- ✅ **Hot reloading** for development

## 🔄 Development Workflow

### **Making Changes:**
1. **Edit code** in your IDE
2. **Save files** - Flask auto-reloads
3. **Refresh browser** - See changes immediately
4. **Check console** for errors or logs
5. **Test features** before deploying

### **Before Deploying:**
1. **Test all features locally**
2. **Check browser console for errors**
3. **Verify API endpoints work**
4. **Test authentication flows**
5. **Commit and push changes**

## 🌐 Local URLs Reference

- **Main Website**: http://localhost:5000
- **Simple Interface**: http://localhost:5000/simple
- **Health Check**: http://localhost:5000/health
- **API Test**: http://localhost:5000/api/test
- **BTC Price**: http://localhost:5000/api/btc/price
- **BTC Stats**: http://localhost:5000/api/btc/stats
- **BTC History**: http://localhost:5000/api/btc/history?timeframe=1h

## 📊 API Testing with Browser

You can test APIs directly in your browser:
1. Go to http://localhost:5000/api/btc/stats
2. Should see JSON response with BTC price
3. Try http://localhost:5000/api/btc/history?timeframe=15m
4. Should see array of historical price data

## 🚀 Ready for Production

When everything works locally:
1. **Commit your changes**: `git add . && git commit -m "Your message"`
2. **Push to GitHub**: `git push`
3. **Render auto-deploys** your changes
4. **Test on production** URL

Your local development environment is now ready! 🎉
