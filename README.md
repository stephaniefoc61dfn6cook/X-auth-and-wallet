# X-Connect Website

A modern web application with X (Twitter) OAuth integration for user authentication.

## Features

- 🔐 X (Twitter) OAuth 2.0 authentication with PKCE
- 🎨 Modern, responsive UI design
- 🚀 Flask backend with secure session management
- 💳 Wallet Connect button (ready for integration)
- ✨ Real-time authentication status updates

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. X (Twitter) Developer Setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app or use an existing one
3. In your app settings, go to "Keys and Tokens"
4. Copy your **Client ID** and **Client Secret**
5. In "Authentication settings", add these redirect URIs:
   - `http://localhost:5000/auth/x/callback` (for development)
   - Your production callback URL (for production)

### 3. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your X API credentials:
   ```env
   X_CLIENT_ID=your-actual-client-id
   X_CLIENT_SECRET=your-actual-client-secret
   X_REDIRECT_URI=http://localhost:5000/auth/x/callback
   FLASK_SECRET_KEY=your-super-secret-key-here
   ```

### 4. Run the Application

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## API Endpoints

- `GET /` - Main application page
- `GET /auth/x/login` - Initiate X OAuth login
- `GET /auth/x/callback` - Handle X OAuth callback
- `GET /auth/status` - Check authentication status
- `GET /auth/logout` - Logout user
- `GET /health` - Health check

## How It Works

### X OAuth Flow

1. User clicks "X Connect" button
2. Frontend calls `/auth/x/login` endpoint
3. Backend generates PKCE parameters and returns X authorization URL
4. User is redirected to X for authentication
5. X redirects back to `/auth/x/callback` with authorization code
6. Backend exchanges code for access token
7. Backend fetches user information and stores in session
8. User is redirected back with success message

### Security Features

- **PKCE (Proof Key for Code Exchange)**: Protects against authorization code interception
- **State Parameter**: Prevents CSRF attacks
- **Secure Sessions**: User data stored securely in Flask sessions
- **CORS Support**: Configured for frontend-backend communication

## File Structure

```
x-connect-website/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── index.html         # Frontend interface
└── README.md          # This file
```

## Development Notes

- The application uses Flask's built-in development server
- Sessions are stored server-side for security
- CORS is enabled for frontend-backend communication
- Error handling includes user-friendly messages

## Production Deployment

**⚠️ IMPORTANT: X OAuth requires HTTPS domains for production use!**

### Quick Deploy Options:

1. **Render (Recommended - Free)**: See `DEPLOYMENT.md` for detailed instructions
2. **Railway**: Auto-deploy from GitHub with free tier
3. **Heroku**: Classic platform with easy deployment

### Key Steps:
1. Deploy to hosting platform with HTTPS
2. Set environment variables on the platform
3. Update X Developer Portal with production callback URL
4. Test X OAuth flow on live domain

📖 **See `DEPLOYMENT.md` for complete deployment instructions**

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**: Make sure your redirect URI in the X Developer Portal matches exactly
2. **"Invalid client credentials"**: Double-check your Client ID and Secret
3. **CORS errors**: Ensure the backend is running and accessible from your frontend

### Environment Variables

Make sure all required environment variables are set:
- `X_CLIENT_ID`
- `X_CLIENT_SECRET`
- `X_REDIRECT_URI`
- `FLASK_SECRET_KEY`

## Next Steps

- [ ] Add user profile management
- [ ] Implement tweet posting functionality
- [ ] Add wallet integration for crypto features
- [ ] Set up database for persistent user storage
- [ ] Add rate limiting and security headers
