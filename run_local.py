#!/usr/bin/env python3
"""
Local Development Server Script
Run this to start your website locally for testing
"""

import os
import sys
from datetime import datetime

def check_requirements():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_cors
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: python -m pip install -r requirements.txt")
        return False

def create_env_template():
    """Create .env template if it doesn't exist"""
    env_path = '.env'
    env_template = '''# Local Development Environment Variables
# Update with your actual X API credentials

# X (Twitter) API Configuration
X_CLIENT_ID=your-x-client-id-here
X_CLIENT_SECRET=your-x-client-secret-here
X_REDIRECT_URI=http://localhost:5000/auth/x/callback

# Flask Configuration
FLASK_SECRET_KEY=local-dev-secret-key-change-this
FLASK_ENV=development
'''
    
    if not os.path.exists(env_path):
        try:
            with open(env_path, 'w') as f:
                f.write(env_template)
            print(f"✅ Created {env_path} template")
            print("📝 Edit .env file with your X API credentials")
        except Exception as e:
            print(f"⚠️  Could not create .env file: {e}")
    else:
        print("✅ .env file exists")

def main():
    print("🚀 Starting X-Connect Website Local Development Server")
    print("=" * 60)
    print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Directory: {os.getcwd()}")
    print()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Create .env template
    create_env_template()
    
    print()
    print("🌐 Your website will be available at:")
    print("   📱 Main Site: http://localhost:5000")
    print("   🔧 Health Check: http://localhost:5000/health")
    print("   📊 API Test: http://localhost:5000/api/test")
    print("   💰 BTC Stats: http://localhost:5000/api/btc/stats")
    print()
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Import and run the app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
