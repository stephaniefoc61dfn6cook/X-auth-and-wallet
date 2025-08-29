# Deployment Guide for X-Connect Website

This guide covers deploying your X OAuth application to various hosting platforms that provide HTTPS domains required for X authentication.

## 🚀 Recommended: Render (Free Tier Available)

### Step 1: Prepare Your Code
1. Make sure all files are committed to a Git repository
2. Push to GitHub, GitLab, or Bitbucket

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your Git repository
4. Use these settings:
   - **Name**: `x-connect-website`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or paid for better performance)

### Step 3: Set Environment Variables
In Render dashboard, add these environment variables:
```
X_CLIENT_ID=your-x-client-id-from-twitter
X_CLIENT_SECRET=your-x-client-secret-from-twitter
X_REDIRECT_URI=https://your-app-name.onrender.com/auth/x/callback
FLASK_SECRET_KEY=your-super-secure-secret-key
FLASK_ENV=production
```

### Step 4: Get Your Domain
Render will provide a URL like: `https://your-app-name.onrender.com`

---

## 🌟 Alternative: Railway

### Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up and click "Deploy from GitHub"
3. Select your repository
4. Railway will auto-detect Python and deploy

### Environment Variables for Railway
```
X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret
X_REDIRECT_URI=https://your-app-name.up.railway.app/auth/x/callback
FLASK_SECRET_KEY=your-secure-key
FLASK_ENV=production
```

---

## 🔧 Alternative: Heroku

### Deploy to Heroku
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Deploy: `git push heroku main`

### Set Heroku Environment Variables
```bash
heroku config:set X_CLIENT_ID=your-x-client-id
heroku config:set X_CLIENT_SECRET=your-x-client-secret
heroku config:set X_REDIRECT_URI=https://your-app-name.herokuapp.com/auth/x/callback
heroku config:set FLASK_SECRET_KEY=your-secure-key
heroku config:set FLASK_ENV=production
```

---

## 📋 X Developer Portal Configuration

### Update Your X App Settings

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Select your app
3. Go to "App settings" → "Authentication settings"
4. Update these URLs:

**Callback URLs:**
```
https://your-domain.com/auth/x/callback
```

**Website URL:**
```
https://your-domain.com
```

**Terms of Service URL:**
```
https://your-domain.com/terms
```

**Privacy Policy URL:**
```
https://your-domain.com/privacy
```

### App Permissions
Make sure your app has these permissions:
- ✅ Read users
- ✅ Read tweets
- ⚠️ Additional permissions as needed

---

## ✅ Testing Your Deployment

### 1. Check Health Endpoint
Visit: `https://your-domain.com/health`
Should return: `{"status": "healthy", "service": "X OAuth Backend"}`

### 2. Test X Authentication
1. Visit your deployed website
2. Click "X Connect"
3. Should redirect to X OAuth
4. After authorization, should redirect back with success

### 3. Check Logs
- **Render**: Dashboard → Logs
- **Railway**: Dashboard → Deployments → Logs
- **Heroku**: `heroku logs --tail`

---

## 🔒 Security Checklist

### Production Environment Variables
- [ ] `FLASK_SECRET_KEY` is a strong, unique secret
- [ ] `X_CLIENT_SECRET` is kept secure
- [ ] `FLASK_ENV=production`
- [ ] All URLs use HTTPS

### X Developer Portal
- [ ] Callback URLs updated to production domain
- [ ] App permissions are correctly set
- [ ] Website URL points to your domain

### Application Security
- [ ] Debug mode is disabled in production
- [ ] CORS is properly configured
- [ ] Session security is enabled

---

## 🐛 Troubleshooting

### Common Issues

**"Invalid redirect URI"**
- Ensure X Developer Portal callback URL matches exactly
- Must use HTTPS in production

**"Client authentication failed"**
- Check X_CLIENT_ID and X_CLIENT_SECRET
- Ensure no extra spaces in environment variables

**"Application Error"**
- Check deployment logs
- Verify all environment variables are set
- Ensure requirements.txt includes all dependencies

### Getting Help
- Check hosting platform documentation
- Review X API documentation
- Check application logs for specific errors

---

## 📈 Next Steps After Deployment

1. **Custom Domain** (Optional)
   - Purchase a domain
   - Configure DNS with your hosting provider
   - Update X Developer Portal URLs

2. **SSL Certificate**
   - Most platforms provide free SSL automatically
   - Verify HTTPS is working

3. **Monitoring**
   - Set up uptime monitoring
   - Configure error tracking
   - Monitor application performance

Your X OAuth application is now ready for production use with a real HTTPS domain! 🎉

