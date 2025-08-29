# Production Setup for x-connect-website.onrender.com

## 🚀 Your Deployed Website
**URL**: https://x-connect-website.onrender.com/

## 📋 Render Environment Variables

Set these in your Render dashboard:

```env
X_CLIENT_ID=your-twitter-client-id-here
X_CLIENT_SECRET=your-twitter-client-secret-here
X_REDIRECT_URI=https://x-connect-website.onrender.com/auth/x/callback
FLASK_SECRET_KEY=generate-a-strong-secret-key-here
FLASK_ENV=production
```

### How to Set Environment Variables in Render:
1. Go to your Render dashboard
2. Select your "x-connect-website" service
3. Click "Environment" in the left sidebar
4. Add each variable above
5. Click "Save Changes"
6. Your app will automatically redeploy

## 🐦 X Developer Portal Configuration

### Required URLs for your X App:

**Callback URLs:**
```
https://x-connect-website.onrender.com/auth/x/callback
```

**Website URL:**
```
https://x-connect-website.onrender.com
```

**Terms of Service URL:**
```
https://x-connect-website.onrender.com/terms
```

**Privacy Policy URL:**
```
https://x-connect-website.onrender.com/privacy
```

### Steps to Update X Developer Portal:
1. Visit: https://developer.twitter.com/en/portal/dashboard
2. Select your app
3. Go to "App settings" → "Authentication settings"
4. Update "Callback URLs" with your production URL
5. Update "Website URL" with your domain
6. Save changes

## 🔑 Getting Your X API Credentials

If you haven't created a Twitter Developer account yet:

1. **Apply for Developer Account**
   - Go to https://developer.twitter.com/en/apply-for-access
   - Fill out the application (usually approved within 24-48 hours)

2. **Create a New App**
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Click "Create App"
   - Fill in app details

3. **Get Your Credentials**
   - Go to your app → "Keys and Tokens"
   - Copy "Client ID" and "Client Secret"
   - These are your `X_CLIENT_ID` and `X_CLIENT_SECRET`

## ✅ Testing Your Production Setup

### 1. Health Check
Visit: https://x-connect-website.onrender.com/health
Should return: `{"status": "healthy", "service": "X OAuth Backend"}`

### 2. Test X OAuth Flow
1. Go to https://x-connect-website.onrender.com/
2. Click "X Connect" button
3. Should redirect to Twitter OAuth
4. After authorization, should redirect back with success message

### 3. Check OAuth Endpoints
- **Login**: https://x-connect-website.onrender.com/auth/x/login
- **Status**: https://x-connect-website.onrender.com/auth/status
- **Logout**: https://x-connect-website.onrender.com/auth/logout

## 🛠️ Troubleshooting

### Common Issues:

**"Invalid redirect URI"**
- Ensure X Developer Portal callback URL matches exactly: `https://x-connect-website.onrender.com/auth/x/callback`
- No trailing slashes, must use HTTPS

**"Client authentication failed"**
- Double-check `X_CLIENT_ID` and `X_CLIENT_SECRET` in Render environment variables
- Ensure no extra spaces or characters

**"Application Error"**
- Check Render logs: Dashboard → your service → Logs
- Verify all environment variables are set correctly

**CORS Issues**
- Should be resolved with Flask-CORS configuration
- Check browser console for specific errors

### Getting Help:
- **Render Logs**: Dashboard → Service → Logs
- **X API Docs**: https://developer.twitter.com/en/docs/authentication/oauth-2-0
- **Flask-CORS Docs**: https://flask-cors.readthedocs.io/

## 🎉 Success Checklist

- [ ] Render environment variables are set
- [ ] X Developer Portal URLs are updated
- [ ] Health endpoint returns success
- [ ] X Connect button opens Twitter OAuth
- [ ] OAuth callback works correctly
- [ ] User information is displayed after login

Your X OAuth integration is now ready for production use! 🚀
