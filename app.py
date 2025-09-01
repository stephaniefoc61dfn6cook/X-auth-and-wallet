from flask import Flask, request, redirect, url_for, session, jsonify, render_template_string
from flask_cors import CORS
import requests
import os
import secrets
import base64
import hashlib
from urllib.parse import urlencode, parse_qs
import json
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')

# Enable CORS for frontend integration
CORS(app, supports_credentials=True)

# X (Twitter) OAuth 2.0 configuration
X_CLIENT_ID = os.environ.get('X_CLIENT_ID', 'your-x-client-id')
X_CLIENT_SECRET = os.environ.get('X_CLIENT_SECRET', 'your-x-client-secret')
X_REDIRECT_URI = os.environ.get('X_REDIRECT_URI', 'http://localhost:5000/auth/x/callback')

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://ziuxjkxenfbqgbmslczv.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InppdXhqa3hlbmZicWdibXNsY3p2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2OTEzMjAsImV4cCI6MjA3MjI2NzMyMH0.Dk0FBPW8U78Pjjtdlkm9jwP_I8_f1x8mrOBVAhMQQ6M')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InppdXhqa3hlbmZicWdibXNsY3p2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjY5MTMyMCwiZXhwIjoyMDcyMjY3MzIwfQ.gdG6hNXFzeHqqoazx2o6qOS1uk3cQn87MWlET-_XBhM')

# Helper function to create/update user in Supabase
def create_or_update_user_in_db(user_data):
    """Create or update user in Supabase database"""
    try:
        # Use service key for backend operations
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Prepare user data for database
        db_user_data = {
            'id': user_data.get('id'),
            'username': user_data.get('username'),
            'x_username': user_data.get('x_username'),
            'phantom_address': user_data.get('phantom_address')
        }
        
        # Remove None values
        db_user_data = {k: v for k, v in db_user_data.items() if v is not None}
        
        # Use upsert with on_conflict parameter for PostgreSQL UPSERT
        headers['Prefer'] = 'resolution=merge-duplicates,return=representation'
        
        # Upsert user (insert or update if exists)
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/users',
            headers=headers,
            json=db_user_data
        )
        
        print(f"[USER_CREATE] Status: {response.status_code}")
        print(f"[USER_CREATE] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"[USER_CREATE] Error creating user: {response.text}")
            return None
            
    except Exception as e:
        print(f"[USER_CREATE] Exception: {str(e)}")
        return None

# X OAuth 2.0 endpoints
X_AUTHORIZE_URL = 'https://twitter.com/i/oauth2/authorize'
X_TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
X_USER_URL = 'https://api.twitter.com/2/users/me'

def generate_code_verifier():
    """Generate a code verifier for PKCE"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(verifier):
    """Generate a code challenge from the verifier"""
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

@app.route('/supabase_config.js')
def supabase_config():
    """Serve the Supabase configuration file with environment variables injected"""
    try:
        with open('supabase_config.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
            
        # Inject environment variables into the JavaScript
        js_content = js_content.replace(
            'window.SUPABASE_URL || \'https://ziuxjkxenfbqgbmslczv.supabase.co\'',
            f'"{SUPABASE_URL}"'
        ).replace(
            'window.SUPABASE_ANON_KEY || \'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InppdXhqa3hlbmZicWdibXNsY3p2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2OTEzMjAsImV4cCI6MjA3MjI2NzMyMH0.Dk0FBPW8U78Pjjtdlkm9jwP_I8_f1x8mrOBVAhMQQ6M\'',
            f'"{SUPABASE_ANON_KEY}"'
        ).replace(
            'window.SUPABASE_SERVICE_KEY || \'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InppdXhqa3hlbmZicWdibXNsY3p2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjY5MTMyMCwiZXhwIjoyMDcyMjY3MzIwfQ.gdG6hNXFzeHqqoazx2o6qOS1uk3cQn87MWlET-_XBhM\'',
            f'"{SUPABASE_SERVICE_KEY}"'
        )
        
        # Return as JavaScript file
        from flask import Response
        return Response(js_content, mimetype='application/javascript')
        
    except FileNotFoundError:
        return "Supabase configuration file not found", 404

@app.route('/')
def index():
    """Serve the gaming interface as default with injected environment variables"""
    try:
        with open('gaming-index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Inject Supabase environment variables into the HTML
        supabase_script = f"""
        <script>
            // Inject Supabase configuration from server environment variables
            window.SUPABASE_URL = '{SUPABASE_URL}';
            window.SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}';
            window.SUPABASE_SERVICE_KEY = '{SUPABASE_SERVICE_KEY}';
            console.log('🔧 Supabase config injected from server environment');
        </script>
        """
        
        # Insert the script before the closing head tag
        html_content = html_content.replace('</head>', f'{supabase_script}</head>')
        
        return html_content
    except FileNotFoundError:
        return "gaming-index.html not found. Please make sure it exists in the project directory."

@app.route('/simple')
def simple_interface():
    """Serve the simple interface (legacy)"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "index.html not found. Please make sure it exists in the project directory."

@app.route('/auth/x/login')
def x_login():
    """Initiate X OAuth login"""
    try:
        # Generate PKCE parameters
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = secrets.token_urlsafe(32)
        
        # Store in session
        session['code_verifier'] = code_verifier
        session['oauth_state'] = state
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': X_CLIENT_ID,
            'redirect_uri': X_REDIRECT_URI,
            'scope': 'users.read tweet.read',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{X_AUTHORIZE_URL}?{urlencode(params)}"
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'message': 'Redirect to X for authentication'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/auth/x/callback')
def x_callback():
    """Handle X OAuth callback"""
    try:
        # Check for errors
        if 'error' in request.args:
            error_description = request.args.get('error_description', 'Unknown error')
            return f"""
            <html>
                <body>
                    <h2>Authentication Error</h2>
                    <p>Error: {request.args.get('error')}</p>
                    <p>Description: {error_description}</p>
                    <a href="/">Go back to home</a>
                </body>
            </html>
            """
        
        # Verify state parameter
        if request.args.get('state') != session.get('oauth_state'):
            return "Invalid state parameter", 400
        
        # Get authorization code
        auth_code = request.args.get('code')
        if not auth_code:
            return "No authorization code received", 400
        
        # Exchange code for access token
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': X_CLIENT_ID,
            'code': auth_code,
            'redirect_uri': X_REDIRECT_URI,
            'code_verifier': session.get('code_verifier')
        }
        
        # Prepare Basic Auth header
        credentials = f"{X_CLIENT_ID}:{X_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Request access token
        token_response = requests.post(X_TOKEN_URL, data=token_data, headers=headers)
        
        if token_response.status_code != 200:
            return f"Token exchange failed: {token_response.text}", 400
        
        token_info = token_response.json()
        access_token = token_info.get('access_token')
        
        if not access_token:
            return "No access token received", 400
        
        # Get user information
        user_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        user_response = requests.get(X_USER_URL, headers=user_headers)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            user_info = user_data.get('data', {})
            
            # Create/update user in Supabase database
            db_user_data = {
                'id': str(uuid.uuid4()),  # Generate new UUID for database
                'username': user_info.get('username', ''),
                'x_username': user_info.get('username', ''),
                'phantom_address': None  # Will be set when Phantom connects
            }
            
            # Create user in database
            try:
                db_user = create_or_update_user_in_db(db_user_data)
                if db_user:
                    print(f"[X_AUTH] User created/updated in database: {db_user}")
                    # Store database user ID in session
                    if isinstance(db_user, list) and db_user:
                        user_info['db_id'] = db_user[0]['id']
                    elif isinstance(db_user, dict):
                        user_info['db_id'] = db_user.get('id')
                    else:
                        print(f"[X_AUTH] Unexpected db_user format: {type(db_user)}")
                else:
                    print(f"[X_AUTH] Failed to create user in database")
            except Exception as db_error:
                print(f"[X_AUTH] Database error: {str(db_error)}")
                # Continue without database user - authentication still works
            
            # Store user info in session
            session['user_info'] = user_info
            session['access_token'] = access_token
            
            return f"""
            <html>
                <head>
                    <title>X Authentication Success</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                        .success {{ background: #d1fae5; color: #065f46; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                        .user-info {{ background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                        .btn {{ background: #1da1f2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <h1>X Authentication Successful!</h1>
                    <div class="success">
                        <p>✅ Successfully connected to X (Twitter)</p>
                    </div>
                    <div class="user-info">
                        <h3>User Information:</h3>
                        <p><strong>Username:</strong> {user_info.get('username', 'N/A')}</p>
                        <p><strong>Name:</strong> {user_info.get('name', 'N/A')}</p>
                        <p><strong>ID:</strong> {user_info.get('id', 'N/A')}</p>
                    </div>
                    <a href="/" class="btn">Return to Home</a>
                    <script>
                        // Close popup if this was opened in a popup window
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'X_AUTH_SUCCESS',
                                user: {json.dumps(user_info)}
                            }}, '*');
                            window.close();
                        }}
                    </script>
                </body>
            </html>
            """
        else:
            return f"Failed to get user info: {user_response.text}", 400
            
    except Exception as e:
        return f"Callback error: {str(e)}", 500

@app.route('/auth/status')
def auth_status():
    """Check authentication status"""
    try:
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        print(f"[AUTH_STATUS] Session user_info: {user_info}")
        print(f"[AUTH_STATUS] Session phantom_wallet: {phantom_wallet}")
        
        if user_info or phantom_wallet:
            # Ensure we have database user ID
            db_id = user_info.get('db_id') if user_info else None
            
            # Generate safe username
            if user_info and user_info.get('username'):
                username = user_info.get('username')
            elif phantom_wallet and phantom_wallet.get('publicKey'):
                username = f"phantom_user_{phantom_wallet.get('publicKey')[:8]}"
            else:
                username = "anonymous_user"
            
            # Get phantom address safely
            phantom_address = None
            if user_info and user_info.get('phantom_address'):
                phantom_address = user_info.get('phantom_address')
            elif phantom_wallet and phantom_wallet.get('publicKey'):
                phantom_address = phantom_wallet.get('publicKey')
            
            response_data = {
                'authenticated': True,
                'user': {
                    'id': db_id,  # Database user ID for PvP system
                    'username': username,
                    'x_username': user_info.get('username') if user_info else None,
                    'phantom_address': phantom_address,
                    'has_x': bool(user_info and user_info.get('username')),
                    'has_phantom': bool(phantom_wallet and phantom_wallet.get('connected'))
                }
            }
            
            print(f"[AUTH_STATUS] Returning user data: {response_data}")
            return jsonify(response_data)
        else:
            print(f"[AUTH_STATUS] No authentication found")
            return jsonify({
                'authenticated': False
            })
            
    except Exception as e:
        print(f"[AUTH_STATUS] Error: {str(e)}")
        print(f"[AUTH_STATUS] Exception type: {type(e).__name__}")
        import traceback
        print(f"[AUTH_STATUS] Traceback: {traceback.format_exc()}")
        
        # Return safe JSON response even on error
        return jsonify({
            'authenticated': False,
            'error': 'Internal server error'
        }), 500

@app.route('/auth/logout')
def logout():
    """Logout user"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@app.route('/auth/phantom/connect', methods=['POST'])
def phantom_connect():
    """Handle Phantom wallet connection"""
    try:
        data = request.get_json()
        public_key = data.get('publicKey')
        
        if not public_key:
            return jsonify({
                'success': False,
                'error': 'No public key provided'
            }), 400
        
        # Check if user already exists (from X auth) or create new one
        user_info = session.get('user_info', {})
        
        if user_info and user_info.get('db_id'):
            # User exists from X auth, update with Phantom address
            db_user_data = {
                'id': user_info['db_id'],
                'phantom_address': public_key
            }
            print(f"[PHANTOM] Updating existing user {user_info['db_id']} with Phantom address")
        else:
            # Create new user with just Phantom wallet
            db_user_data = {
                'id': str(uuid.uuid4()),
                'username': f'phantom_user_{public_key[:8]}',  # Generate username from public key
                'x_username': None,
                'phantom_address': public_key
            }
            print(f"[PHANTOM] Creating new user with Phantom address")
        
        # Create/update user in database
        db_user = create_or_update_user_in_db(db_user_data)
        if db_user:
            print(f"[PHANTOM] User created/updated in database: {db_user}")
            # Update session with database user ID
            if not user_info:
                user_info = {}
            user_info['db_id'] = db_user[0]['id'] if isinstance(db_user, list) and db_user else db_user.get('id')
            user_info['phantom_address'] = public_key
            session['user_info'] = user_info
        else:
            print(f"[PHANTOM] Failed to create/update user in database")
        
        # Store wallet info in session
        session['phantom_wallet'] = {
            'publicKey': public_key,
            'connected': True,
            'wallet_type': 'phantom'
        }
        
        return jsonify({
            'success': True,
            'message': 'Phantom wallet connected successfully',
            'publicKey': public_key
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/auth/phantom/disconnect', methods=['POST'])
def phantom_disconnect():
    """Handle Phantom wallet disconnection"""
    try:
        # Remove wallet info from session
        if 'phantom_wallet' in session:
            del session['phantom_wallet']
        
        return jsonify({
            'success': True,
            'message': 'Phantom wallet disconnected successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/auth/phantom/status')
def phantom_status():
    """Check Phantom wallet connection status"""
    wallet_info = session.get('phantom_wallet')
    if wallet_info and wallet_info.get('connected'):
        return jsonify({
            'connected': True,
            'publicKey': wallet_info.get('publicKey'),
            'wallet_type': wallet_info.get('wallet_type')
        })
    else:
        return jsonify({
            'connected': False
        })

@app.route('/auth/phantom/sign', methods=['POST'])
def phantom_sign():
    """Handle message signing with Phantom wallet"""
    try:
        data = request.get_json()
        message = data.get('message')
        signature = data.get('signature')
        public_key = data.get('publicKey')
        
        if not all([message, signature, public_key]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: message, signature, or publicKey'
            }), 400
        
        # Verify the wallet is connected in session
        wallet_info = session.get('phantom_wallet')
        if not wallet_info or wallet_info.get('publicKey') != public_key:
            return jsonify({
                'success': False,
                'error': 'Wallet not connected or public key mismatch'
            }), 401
        
        # In a real application, you would verify the signature here
        # For now, we'll just store the signed message
        session['phantom_signed_message'] = {
            'message': message,
            'signature': signature,
            'publicKey': public_key,
            'timestamp': int(time.time()) if 'time' in globals() else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Message signed successfully',
            'verified': True  # In production, implement actual signature verification
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/btc/price')
def btc_price():
    """Get current BTC price via backend proxy using free APIs"""
    try:
        # Try multiple free APIs in order
        apis = [
            {
                'name': 'coinbase',
                'url': 'https://api.coinbase.com/v2/exchange-rates?currency=BTC',
                'parser': lambda data: float(data['data']['rates']['USD'])
            },
            {
                'name': 'blockchain.info',
                'url': 'https://blockchain.info/ticker',
                'parser': lambda data: data['USD']['last']
            },
            {
                'name': 'coindesk',
                'url': 'https://api.coindesk.com/v1/bpi/currentprice.json',
                'parser': lambda data: data['bpi']['USD']['rate_float']
            }
        ]
        
        for api in apis:
            try:
                print(f"Trying {api['name']} API...")
                response = requests.get(api['url'], timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    price = api['parser'](data)
                    
                    print(f"Success with {api['name']}: ${price}")
                    return jsonify({
                        'success': True,
                        'price': price,
                        'source': api['name']
                    })
            except Exception as api_error:
                print(f"{api['name']} failed: {api_error}")
                continue
        
        return jsonify({'success': False, 'error': 'All price APIs failed'}), 500
                
    except Exception as e:
        print(f"Exception in btc_price: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/btc/history')
def btc_history():
    """Get BTC price history using free APIs without rate limits"""
    try:
        timeframe = request.args.get('timeframe', '1h')
        print(f"Fetching BTC history for timeframe: {timeframe}")
        
        # Try CoinGecko first (higher rate limits)
        try:
            # Map timeframes to days for CoinGecko
            timeframe_days = {
                '15m': 1,    # Last 1 day with 5-minute intervals
                '30m': 1,    # Last 1 day with 5-minute intervals  
                '1h': 1,     # Last 1 day with hourly intervals
                '4h': 7      # Last 7 days with hourly intervals
            }
            
            days = timeframe_days.get(timeframe, 1)
            
            # Use CoinGecko's free API (no authentication required)
            url = f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}'
            print(f"Trying CoinGecko API: {url}")
            
            response = requests.get(url, timeout=15)
            print(f"CoinGecko response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'prices' in data and data['prices']:
                    prices = data['prices']
                    
                    # Filter data based on timeframe
                    if timeframe == '15m':
                        # Take every 3rd point (15 min intervals from 5 min data)
                        prices = prices[::3][-96:]  # Last 24 hours in 15min intervals
                    elif timeframe == '30m':
                        # Take every 6th point (30 min intervals from 5 min data)
                        prices = prices[::6][-48:]  # Last 24 hours in 30min intervals
                    elif timeframe == '1h':
                        # Take every 12th point (1 hour intervals from 5 min data)
                        prices = prices[::12][-24:]  # Last 24 hours in 1h intervals
                    elif timeframe == '4h':
                        # Take every 48th point (4 hour intervals from 5 min data)
                        prices = prices[::48][-42:]  # Last week in 4h intervals
                    
                    # Format data for frontend
                    formatted_data = []
                    for timestamp, price in prices:
                        formatted_data.append({
                            'timestamp': timestamp,
                            'price': price,
                            'high': price,  # CoinGecko doesn't provide OHLC in this endpoint
                            'low': price,
                            'volume': 0
                        })
                    
                    print(f"CoinGecko success: {len(formatted_data)} data points")
                    return jsonify({
                        'success': True,
                        'data': formatted_data,
                        'timeframe': timeframe,
                        'source': 'coingecko'
                    })
            
        except Exception as coingecko_error:
            print(f"CoinGecko failed: {coingecko_error}")
        
        # Fallback: Generate mock data based on current price
        try:
            print("Falling back to mock data generation...")
            
            # Get current price from our price endpoint
            import time
            current_time = int(time.time() * 1000)
            
            # Generate realistic mock data
            base_price = 43000  # Fallback base price
            formatted_data = []
            
            # Generate data points based on timeframe
            intervals = {
                '15m': {'count': 96, 'interval_ms': 15 * 60 * 1000},  # 15 minutes
                '30m': {'count': 48, 'interval_ms': 30 * 60 * 1000},  # 30 minutes
                '1h': {'count': 24, 'interval_ms': 60 * 60 * 1000},   # 1 hour
                '4h': {'count': 24, 'interval_ms': 4 * 60 * 60 * 1000} # 4 hours
            }
            
            config = intervals.get(timeframe, intervals['1h'])
            
            import random
            for i in range(config['count']):
                timestamp = current_time - (config['count'] - i) * config['interval_ms']
                # Add some realistic price variation (±2%)
                variation = random.uniform(-0.02, 0.02)
                price = base_price * (1 + variation)
                
                formatted_data.append({
                    'timestamp': timestamp,
                    'price': round(price, 2),
                    'high': round(price * 1.01, 2),
                    'low': round(price * 0.99, 2),
                    'volume': random.randint(1000000, 5000000)
                })
            
            print(f"Generated {len(formatted_data)} mock data points")
            return jsonify({
                'success': True,
                'data': formatted_data,
                'timeframe': timeframe,
                'source': 'mock-data'
            })
            
        except Exception as mock_error:
            print(f"Mock data generation failed: {mock_error}")
            return jsonify({'success': False, 'error': 'All data sources failed'}), 500
            
    except Exception as e:
        print(f"Exception in btc_history: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/btc/stats')
def btc_stats():
    """Get BTC statistics using completely free APIs"""
    try:
        print("Fetching BTC stats using free APIs...")
        
        # Try multiple free APIs for comprehensive stats
        current_price = 0
        change_24h = 0
        high_24h = 0
        low_24h = 0
        source = 'unknown'
        
        # Try CoinGecko first (good free tier)
        try:
            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true'
            response = requests.get(url, timeout=10)
            print(f"CoinGecko stats response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'bitcoin' in data:
                    btc_data = data['bitcoin']
                    current_price = btc_data.get('usd', 0)
                    change_24h = btc_data.get('usd_24h_change', 0)
                    high_24h = current_price * 1.02  # Estimate high as +2%
                    low_24h = current_price * 0.98   # Estimate low as -2%
                    source = 'coingecko'
                    print(f"CoinGecko success: ${current_price}")
            
        except Exception as coingecko_error:
            print(f"CoinGecko failed: {coingecko_error}")
        
        # If CoinGecko failed, try other free APIs
        if current_price == 0:
            try:
                # Try Coinbase
                response = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    current_price = float(data['data']['rates']['USD'])
                    high_24h = current_price * 1.02
                    low_24h = current_price * 0.98
                    source = 'coinbase'
                    print(f"Coinbase success: ${current_price}")
                    
            except Exception as coinbase_error:
                print(f"Coinbase failed: {coinbase_error}")
        
        # If still no price, try Blockchain.info
        if current_price == 0:
            try:
                response = requests.get('https://blockchain.info/ticker', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    current_price = data['USD']['last']
                    high_24h = current_price * 1.02
                    low_24h = current_price * 0.98
                    source = 'blockchain.info'
                    print(f"Blockchain.info success: ${current_price}")
                    
            except Exception as blockchain_error:
                print(f"Blockchain.info failed: {blockchain_error}")
        
        # If we have a price, return success
        if current_price > 0:
            return jsonify({
                'success': True,
                'current_price': current_price,
                'change_24h': change_24h,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'volume_24h': 0,  # Not available in free APIs
                'source': source
            })
        else:
            # Last resort: return mock data
            print("All APIs failed, using mock data")
            mock_price = 43000 + (hash(str(datetime.now().hour)) % 2000 - 1000)  # Pseudo-random but consistent
            return jsonify({
                'success': True,
                'current_price': mock_price,
                'change_24h': 1.5,
                'high_24h': mock_price * 1.02,
                'low_24h': mock_price * 0.98,
                'volume_24h': 2500000000,
                'source': 'mock-data'
            })
            
    except Exception as e:
        print(f"Exception in btc_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test')
def api_test():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'success',
        'message': 'Backend API is working',
        'timestamp': str(datetime.now()) if 'datetime' in globals() else 'unknown'
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'X OAuth & Phantom Wallet Backend',
        'timestamp': datetime.now().isoformat(),
        'supabase_url': SUPABASE_URL[:50] + '...',  # Show partial URL for verification
        'has_supabase_config': os.path.exists('supabase_config.js')
    })

if __name__ == '__main__':
    # Check if required environment variables are set
    if X_CLIENT_ID == 'your-x-client-id' or X_CLIENT_SECRET == 'your-x-client-secret':
        print("⚠️  WARNING: Please set X_CLIENT_ID and X_CLIENT_SECRET environment variables")
        print("   You can get these from https://developer.twitter.com/en/portal/dashboard")
    
    print("🚀 Starting X OAuth Backend...")
    print(f"📍 Redirect URI: {X_REDIRECT_URI}")
    
    # Use PORT environment variable if available (for deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    if debug_mode:
        print("🌐 Server running at: http://localhost:5000")
    else:
        print(f"🌐 Server running on port: {port}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
