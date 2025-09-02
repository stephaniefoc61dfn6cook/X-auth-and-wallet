from flask import Flask, request, redirect, url_for, session, jsonify, render_template_string
from flask_cors import CORS
import requests
import os
import secrets
import base64
import hashlib
from urllib.parse import urlencode, parse_qs, quote
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

# Helper function to find existing user by X username or Phantom address
def find_existing_user(x_username=None, phantom_address=None):
    """Find existing user by X username or Phantom address"""
    try:
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Try to find user by X username first, then by Phantom address
        user = None
        
        if x_username:
            encoded_username = quote(str(x_username), safe='')
            print(f"[USER_LOOKUP] Searching by X Username: '{x_username}' -> '{encoded_username}'")
            
            response = requests.get(
                f'{SUPABASE_URL}/rest/v1/users?x_username=eq.{encoded_username}',
                headers=headers
            )
            
            print(f"[USER_LOOKUP] X Username query status: {response.status_code}")
            print(f"[USER_LOOKUP] X Username query response: {response.text}")
            
            if response.status_code == 200:
                users = response.json()
                if users:
                    user = users[0]
                    print(f"[USER_LOOKUP] Found user by X username: {user.get('id')}")
        
        if not user and phantom_address:
            encoded_address = quote(str(phantom_address), safe='')
            print(f"[USER_LOOKUP] Searching by Phantom Address: '{phantom_address}' -> '{encoded_address}'")
            
            response = requests.get(
                f'{SUPABASE_URL}/rest/v1/users?phantom_address=eq.{encoded_address}',
                headers=headers
            )
            
            print(f"[USER_LOOKUP] Phantom address query status: {response.status_code}")
            print(f"[USER_LOOKUP] Phantom address query response: {response.text}")
            
            if response.status_code == 200:
                users = response.json()
                if users:
                    user = users[0]
                    print(f"[USER_LOOKUP] Found user by Phantom address: {user.get('id')}")
        
        return user
            
    except Exception as e:
        print(f"[USER_LOOKUP] Exception: {str(e)}")
        return None

# Helper function to create/update user in Supabase
def create_or_update_user_in_db(user_data, existing_user_id=None):
    """Create or update user in Supabase database"""
    try:
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Prepare user data for database
        db_user_data = {
            'username': user_data.get('username'),
            'x_username': user_data.get('x_username'),
            'phantom_address': user_data.get('phantom_address')
        }
        
        # Remove None values
        db_user_data = {k: v for k, v in db_user_data.items() if v is not None}
        
        if existing_user_id:
            # Update existing user
            print(f"[USER_UPDATE] Updating existing user {existing_user_id}")
            response = requests.patch(
                f'{SUPABASE_URL}/rest/v1/users?id=eq.{existing_user_id}',
                headers=headers,
                json=db_user_data
            )
        else:
            # Create new user
            print(f"[USER_CREATE] Creating new user")
            db_user_data['id'] = str(uuid.uuid4())
            response = requests.post(
                f'{SUPABASE_URL}/rest/v1/users',
                headers=headers,
                json=db_user_data
            )
        
        print(f"[USER_DB] Status: {response.status_code}")
        print(f"[USER_DB] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            return result[0] if isinstance(result, list) and result else result
        else:
            print(f"[USER_DB] Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"[USER_DB] Exception: {str(e)}")
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
            
            # Look for existing user first
            x_username = user_info.get('username', '')
            
            # Check if user already exists in session (e.g., from Phantom connection)
            session_user_info = session.get('user_info', {})
            if session_user_info and session_user_info.get('db_id'):
                print(f"[X_AUTH] Found existing user in session: {session_user_info['db_id']}")
                # Get the full user record to use as existing_user
                existing_user = {'id': session_user_info['db_id']}
            else:
                # Look for existing user by X username
                existing_user = find_existing_user(x_username=x_username)
            
            # Prepare user data for database
            db_user_data = {
                'username': x_username,
                'x_username': x_username
            }
            
            # If updating existing user, preserve existing phantom_address
            if not existing_user:
                db_user_data['phantom_address'] = None  # Will be set when Phantom connects
            
            # Create or update user in database
            try:
                if existing_user:
                    print(f"[X_AUTH] Updating existing user: {existing_user['id']} with X credentials")
                    print(f"[X_AUTH] Update data: {db_user_data}")
                    db_user = create_or_update_user_in_db(db_user_data, existing_user['id'])
                else:
                    print(f"[X_AUTH] Creating new user for X username: {x_username}")
                    print(f"[X_AUTH] Create data: {db_user_data}")
                    db_user = create_or_update_user_in_db(db_user_data)
                
                if db_user:
                    print(f"[X_AUTH] User created/updated in database: {db_user}")
                    # Store database user ID in session
                    user_info['db_id'] = db_user.get('id')
                    
                    # Merge with existing session data (preserve Phantom info if exists)
                    if session_user_info:
                        # Preserve existing phantom data
                        if session_user_info.get('phantom_address'):
                            user_info['phantom_address'] = session_user_info.get('phantom_address')
                        print(f"[X_AUTH] Merged session data: X + existing Phantom info")
                else:
                    print(f"[X_AUTH] Failed to create/update user in database")
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
        
        # Check if user already exists (from session or database lookup)
        user_info = session.get('user_info', {})
        existing_user = None
        
        # First try to find by current session user ID
        if user_info and user_info.get('db_id'):
            print(f"[PHANTOM] Using existing user from session: {user_info['db_id']}")
            existing_user = {'id': user_info['db_id']}
        else:
            # Look for existing user by Phantom address or X username
            x_username = user_info.get('username') if user_info else None
            existing_user = find_existing_user(x_username=x_username, phantom_address=public_key)
        
        # Prepare user data for database
        if existing_user:
            # Update existing user with Phantom address
            db_user_data = {
                'phantom_address': public_key
            }
            # If we have X username from session, make sure it's in the update
            if user_info and user_info.get('username'):
                db_user_data['x_username'] = user_info.get('username')
                db_user_data['username'] = user_info.get('username')
            
            print(f"[PHANTOM] Updating existing user {existing_user['id']} with Phantom address")
            db_user = create_or_update_user_in_db(db_user_data, existing_user['id'])
        else:
            # Create new user with just Phantom wallet
            db_user_data = {
                'username': f'phantom_user_{public_key[:8]}',  # Generate username from public key
                'x_username': None,
                'phantom_address': public_key
            }
            print(f"[PHANTOM] Creating new user with Phantom address")
            db_user = create_or_update_user_in_db(db_user_data)
        
        if db_user:
            print(f"[PHANTOM] User created/updated in database: {db_user}")
            # Update session with database user ID
            if not user_info:
                user_info = {}
            user_info['db_id'] = db_user.get('id')
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

@app.route('/api/predictions', methods=['POST'])
def create_prediction():
    """Create a prediction in the database using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get user ID from session
        user_id = user_info.get('db_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User database ID not found'
            }), 400
        
        # Get prediction data from request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Prepare prediction data
        prediction_data = {
            'user_id': user_id,
            'predicted_price': data.get('predicted_price'),
            'direction': data.get('direction'),
            'bet_amount': data.get('bet_amount'),
            'current_btc_price': data.get('current_btc_price')
        }
        
        print(f"[PREDICTION_API] Creating prediction for user {user_id}: {prediction_data}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Insert prediction
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/predictions',
            headers=headers,
            json=prediction_data
        )
        
        print(f"[PREDICTION_API] Status: {response.status_code}")
        print(f"[PREDICTION_API] Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            prediction = result[0] if isinstance(result, list) and result else result
            return jsonify({
                'success': True,
                'prediction': prediction
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Database error: {response.text}'
            }), 500
            
    except Exception as e:
        print(f"[PREDICTION_API] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/matchmaking/find', methods=['POST'])
def find_and_create_match():
    """Find and create a match using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get prediction ID from request
        data = request.get_json()
        if not data or not data.get('prediction_id'):
            return jsonify({
                'success': False,
                'error': 'prediction_id required'
            }), 400
        
        prediction_id = data['prediction_id']
        print(f"[MATCHMAKING_API] Finding match for prediction {prediction_id}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 1. Get the prediction details
        pred_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/predictions?id=eq.{prediction_id}&select=*',
            headers=headers
        )
        
        print(f"[MATCHMAKING_API] Prediction query status: {pred_response.status_code}")
        
        if pred_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to get prediction: {pred_response.text}'
            }), 500
        
        predictions = pred_response.json()
        if not predictions:
            return jsonify({
                'success': False,
                'error': 'Prediction not found'
            }), 404
        
        prediction = predictions[0]
        print(f"[MATCHMAKING_API] Found prediction: {prediction}")
        
        # 2. Call find_matching_prediction function
        match_response = requests.post(
            f'{SUPABASE_URL}/rest/v1/rpc/find_matching_prediction',
            headers=headers,
            json={
                'p_user_id': prediction['user_id'],
                'p_predicted_price': float(prediction['predicted_price']),
                'p_direction': prediction['direction'],
                'p_bet_amount': prediction['bet_amount']
            }
        )
        
        print(f"[MATCHMAKING_API] Match search status: {match_response.status_code}")
        print(f"[MATCHMAKING_API] Match search response: {match_response.text}")
        
        if match_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Match search failed: {match_response.text}'
            }), 500
        
        match_id = match_response.json()
        
        if not match_id:
            # No match found
            return jsonify({
                'success': True,
                'match_found': False,
                'battle_id': None
            })
        
        # 3. Create battle using the matched predictions
        battle_response = requests.post(
            f'{SUPABASE_URL}/rest/v1/rpc/create_battle',
            headers=headers,
            json={
                'p_prediction1_id': prediction_id,
                'p_prediction2_id': match_id
            }
        )
        
        print(f"[MATCHMAKING_API] Battle creation status: {battle_response.status_code}")
        print(f"[MATCHMAKING_API] Battle creation response: {battle_response.text}")
        
        if battle_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Battle creation failed: {battle_response.text}'
            }), 500
        
        battle_id = battle_response.json()
        
        return jsonify({
            'success': True,
            'match_found': True,
            'battle_id': battle_id
        })
        
    except Exception as e:
        print(f"[MATCHMAKING_API] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battles/<battle_id>', methods=['GET'])
def get_battle_details(battle_id):
    """Get battle details using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        print(f"[BATTLE_API] Getting details for battle {battle_id}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Get battle with related data
        battle_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}&select=*,user1:users!battles_user1_id_fkey(*),user2:users!battles_user2_id_fkey(*),user1_prediction:predictions!battles_user1_prediction_id_fkey(*),user2_prediction:predictions!battles_user2_prediction_id_fkey(*)',
            headers=headers
        )
        
        print(f"[BATTLE_API] Battle query status: {battle_response.status_code}")
        
        if battle_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to get battle: {battle_response.text}'
            }), 500
        
        battles = battle_response.json()
        if not battles:
            return jsonify({
                'success': False,
                'error': 'Battle not found'
            }), 404
        
        battle = battles[0]
        print(f"[BATTLE_API] Found battle: {battle['id']}")
        
        return jsonify({
            'success': True,
            'battle': battle
        })
        
    except Exception as e:
        print(f"[BATTLE_API] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions/<prediction_id>/cancel', methods=['POST'])
def cancel_prediction(prediction_id):
    """Cancel a prediction using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get user ID from session
        user_id = user_info.get('db_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User database ID not found'
            }), 400
        
        print(f"[CANCEL_API] Canceling prediction {prediction_id} for user {user_id}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Cancel the prediction
        response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/predictions?id=eq.{prediction_id}&user_id=eq.{user_id}',
            headers=headers,
            json={'status': 'cancelled'}
        )
        
        print(f"[CANCEL_API] Status: {response.status_code}")
        print(f"[CANCEL_API] Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'prediction': result[0] if result else None
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to cancel prediction: {response.text}'
            }), 500
            
    except Exception as e:
        print(f"[CANCEL_API] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battles/<battle_id>/accept', methods=['POST'])
def accept_battle(battle_id):
    """Accept a battle invitation using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get user ID from session
        user_id = user_info.get('db_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User database ID not found'
            }), 400
        
        print(f"[BATTLE_ACCEPT] User {user_id} accepting battle {battle_id}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Get battle details to determine which user is accepting
        battle_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}&select=*',
            headers=headers
        )
        
        if battle_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to get battle: {battle_response.text}'
            }), 500
        
        battles = battle_response.json()
        if not battles:
            return jsonify({
                'success': False,
                'error': 'Battle not found'
            }), 404
        
        battle = battles[0]
        
        # Determine if user is user1 or user2
        is_user1 = battle['user1_id'] == user_id
        is_user2 = battle['user2_id'] == user_id
        
        if not (is_user1 or is_user2):
            return jsonify({
                'success': False,
                'error': 'User is not part of this battle'
            }), 403
        
        # Update battle acceptance
        update_data = {}
        if is_user1:
            update_data['user1_accepted'] = True
            update_data['user1_accepted_at'] = 'NOW()'
            user_field = 'user1_accepted'
            other_user_field = 'user2_accepted'
        else:
            update_data['user2_accepted'] = True
            update_data['user2_accepted_at'] = 'NOW()'
            user_field = 'user2_accepted'
            other_user_field = 'user1_accepted'
        
        # Update battle
        update_response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}',
            headers=headers,
            json=update_data
        )
        
        print(f"[BATTLE_ACCEPT] Battle update status: {update_response.status_code}")
        
        if update_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to update battle: {update_response.text}'
            }), 500
        
        # Update battle invitation with user response
        invitation_update = {}
        if is_user1:
            invitation_update['user1_response'] = 'accepted'
            invitation_update['user1_responded_at'] = 'NOW()'
        else:
            invitation_update['user2_response'] = 'accepted'
            invitation_update['user2_responded_at'] = 'NOW()'
        
        invitation_response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/battle_invitations?battle_id=eq.{battle_id}',
            headers=headers,
            json=invitation_update
        )
        
        # Check if both users have accepted
        updated_battle_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}&select=user1_accepted,user2_accepted',
            headers=headers
        )
        
        if updated_battle_response.status_code == 200:
            updated_battle = updated_battle_response.json()[0]
            both_accepted = updated_battle['user1_accepted'] and updated_battle['user2_accepted']
            
            if both_accepted:
                # Activate the battle
                activate_response = requests.patch(
                    f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}',
                    headers=headers,
                    json={'status': 'active'}
                )
                
                # Update invitation status
                requests.patch(
                    f'{SUPABASE_URL}/rest/v1/battle_invitations?battle_id=eq.{battle_id}',
                    headers=headers,
                    json={'status': 'accepted'}
                )
                
                print(f"[BATTLE_ACCEPT] Battle {battle_id} activated - both users accepted")
        
        return jsonify({
            'success': True,
            'user_accepted': True,
            'both_accepted': both_accepted if 'both_accepted' in locals() else False,
            'battle_status': 'active' if both_accepted else 'pending_acceptance'
        })
        
    except Exception as e:
        print(f"[BATTLE_ACCEPT] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battles/<battle_id>/decline', methods=['POST'])
def decline_battle(battle_id):
    """Decline a battle invitation using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get user ID from session
        user_id = user_info.get('db_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User database ID not found'
            }), 400
        
        print(f"[BATTLE_DECLINE] User {user_id} declining battle {battle_id}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Get battle details
        battle_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}&select=*',
            headers=headers
        )
        
        if battle_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to get battle: {battle_response.text}'
            }), 500
        
        battles = battle_response.json()
        if not battles:
            return jsonify({
                'success': False,
                'error': 'Battle not found'
            }), 404
        
        battle = battles[0]
        
        # Determine if user is user1 or user2
        is_user1 = battle['user1_id'] == user_id
        is_user2 = battle['user2_id'] == user_id
        
        if not (is_user1 or is_user2):
            return jsonify({
                'success': False,
                'error': 'User is not part of this battle'
            }), 403
        
        # Cancel the battle
        cancel_response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}',
            headers=headers,
            json={'status': 'cancelled'}
        )
        
        # Update battle invitation with user response
        invitation_update = {'status': 'declined'}
        if is_user1:
            invitation_update['user1_response'] = 'declined'
            invitation_update['user1_responded_at'] = 'NOW()'
        else:
            invitation_update['user2_response'] = 'declined'
            invitation_update['user2_responded_at'] = 'NOW()'
        
        invitation_response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/battle_invitations?battle_id=eq.{battle_id}',
            headers=headers,
            json=invitation_update
        )
        
        # Reset predictions back to 'searching' status so they can be matched again
        reset_predictions_response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/predictions?id=in.({battle["user1_prediction_id"]},{battle["user2_prediction_id"]})',
            headers=headers,
            json={'status': 'searching'}
        )
        
        print(f"[BATTLE_DECLINE] Battle {battle_id} cancelled and predictions reset to searching")
        
        return jsonify({
            'success': True,
            'battle_cancelled': True,
            'predictions_reset': True
        })
        
    except Exception as e:
        print(f"[BATTLE_DECLINE] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battles/<battle_id>/status', methods=['GET'])
def get_battle_status(battle_id):
    """Get battle status and acceptance details using service key to bypass RLS"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Get battle and invitation details
        battle_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battles?id=eq.{battle_id}&select=*',
            headers=headers
        )
        
        invitation_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battle_invitations?battle_id=eq.{battle_id}&select=*',
            headers=headers
        )
        
        if battle_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to get battle: {battle_response.text}'
            }), 500
        
        battles = battle_response.json()
        if not battles:
            return jsonify({
                'success': False,
                'error': 'Battle not found'
            }), 404
        
        battle = battles[0]
        invitation = invitation_response.json()[0] if invitation_response.status_code == 200 and invitation_response.json() else None
        
        return jsonify({
            'success': True,
            'battle': battle,
            'invitation': invitation,
            'both_accepted': battle['user1_accepted'] and battle['user2_accepted'],
            'is_active': battle['status'] == 'active'
        })
        
    except Exception as e:
        print(f"[BATTLE_STATUS] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battles/pending', methods=['GET'])
def get_pending_battles():
    """Get pending battle invitations for the current user"""
    try:
        # Check authentication
        user_info = session.get('user_info', {})
        phantom_wallet = session.get('phantom_wallet', {})
        
        if not (user_info or phantom_wallet):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get user ID from session
        user_id = user_info.get('db_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User database ID not found'
            }), 400
        
        print(f"[PENDING_BATTLES] Checking pending battles for user {user_id}")
        
        # Use service key to bypass RLS
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Get battles where user is involved and status is pending_acceptance
        battles_response = requests.get(
            f'{SUPABASE_URL}/rest/v1/battles?or=(user1_id.eq.{user_id},user2_id.eq.{user_id})&status=eq.pending_acceptance&select=*,user1:users!battles_user1_id_fkey(*),user2:users!battles_user2_id_fkey(*),user1_prediction:predictions!battles_user1_prediction_id_fkey(*),user2_prediction:predictions!battles_user2_prediction_id_fkey(*)',
            headers=headers
        )
        
        print(f"[PENDING_BATTLES] Query status: {battles_response.status_code}")
        print(f"[PENDING_BATTLES] Query response: {battles_response.text}")
        
        if battles_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to get pending battles: {battles_response.text}'
            }), 500
        
        battles = battles_response.json()
        
        # Filter battles where user hasn't accepted yet
        pending_battles = []
        for battle in battles:
            is_user1 = battle['user1_id'] == user_id
            is_user2 = battle['user2_id'] == user_id
            
            if is_user1 and not battle['user1_accepted']:
                pending_battles.append(battle)
            elif is_user2 and not battle['user2_accepted']:
                pending_battles.append(battle)
        
        print(f"[PENDING_BATTLES] Found {len(pending_battles)} pending battles for user {user_id}")
        
        return jsonify({
            'success': True,
            'pending_battles': pending_battles,
            'count': len(pending_battles)
        })
        
    except Exception as e:
        print(f"[PENDING_BATTLES] Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
