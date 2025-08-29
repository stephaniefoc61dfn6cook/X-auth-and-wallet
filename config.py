import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # X (Twitter) OAuth Configuration
    X_CLIENT_ID = os.environ.get('X_CLIENT_ID')
    X_CLIENT_SECRET = os.environ.get('X_CLIENT_SECRET')
    X_REDIRECT_URI = os.environ.get('X_REDIRECT_URI', 'http://localhost:5000/auth/x/callback')
    
    # X API URLs
    X_AUTHORIZE_URL = 'https://twitter.com/i/oauth2/authorize'
    X_TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
    X_USER_URL = 'https://api.twitter.com/2/users/me'
    
    # OAuth Scopes
    X_SCOPES = 'tweet.read users.read offline.access'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # In production, ensure these are set
    @classmethod
    def validate_config(cls):
        required_vars = ['X_CLIENT_ID', 'X_CLIENT_SECRET', 'FLASK_SECRET_KEY']
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
