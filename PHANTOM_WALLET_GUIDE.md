# Phantom Wallet Integration Guide

## 🔮 What's New

Your website now supports **Phantom Wallet** integration alongside X OAuth! Users can:

- ✅ **Connect Phantom Wallet** - Securely connect their Solana wallet
- ✅ **Sign Messages** - Verify wallet ownership through message signing
- ✅ **Session Management** - Persistent wallet connection across page reloads
- ✅ **Dual Authentication** - Use both X OAuth and Phantom wallet simultaneously

## 🚀 Features Added

### **Backend Routes (Flask)**

1. **`POST /auth/phantom/connect`** - Handle wallet connection
2. **`POST /auth/phantom/disconnect`** - Handle wallet disconnection  
3. **`GET /auth/phantom/status`** - Check wallet connection status
4. **`POST /auth/phantom/sign`** - Handle message signing verification

### **Frontend Integration**

1. **Phantom Detection** - Automatically detects if Phantom wallet is installed
2. **Connection Flow** - Seamless wallet connection with error handling
3. **Message Signing** - Cryptographic proof of wallet ownership
4. **Dynamic UI** - Button states change based on connection status
5. **Install Prompt** - Guides users to install Phantom if not found

## 🎯 How It Works

### **Connection Flow:**
1. User clicks "Wallet Connect" button
2. Frontend checks if Phantom wallet is installed
3. If not installed → Shows install link
4. If installed → Requests wallet connection
5. User approves in Phantom popup
6. Backend stores wallet info in session
7. UI updates to show connected state
8. "Sign Message" button appears

### **Message Signing:**
1. User clicks "Sign Message" button
2. Frontend generates timestamped message
3. Phantom wallet prompts user to sign
4. Signed message sent to backend for verification
5. Backend confirms wallet ownership
6. UI shows verification success

## 🔧 API Endpoints

### **Connect Phantom Wallet**
```http
POST /auth/phantom/connect
Content-Type: application/json

{
  "publicKey": "wallet_public_key_here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Phantom wallet connected successfully",
  "publicKey": "wallet_public_key_here"
}
```

### **Check Connection Status**
```http
GET /auth/phantom/status
```

**Response:**
```json
{
  "connected": true,
  "publicKey": "wallet_public_key_here",
  "wallet_type": "phantom"
}
```

### **Sign Message**
```http
POST /auth/phantom/sign
Content-Type: application/json

{
  "message": "Sign this message to verify...",
  "signature": [signature_bytes_array],
  "publicKey": "wallet_public_key_here"
}
```

## 🛠️ Testing Your Integration

### **1. Install Phantom Wallet**
- Go to [phantom.app](https://phantom.app/)
- Install browser extension
- Create or import a Solana wallet

### **2. Test Connection**
1. Visit your website: https://x-connect-website.onrender.com/
2. Click "Wallet Connect"
3. Approve connection in Phantom popup
4. Should see: "Phantom wallet connected! [short_address]"

### **3. Test Message Signing**
1. After connecting, click "Sign Message"
2. Sign the message in Phantom
3. Should see: "Message signed successfully! ✓ Wallet verified"

### **4. Test Session Persistence**
1. Connect wallet
2. Refresh the page
3. Wallet should remain connected

## 🔒 Security Features

### **Session Management**
- Wallet info stored securely in Flask sessions
- Public keys validated on each request
- Automatic cleanup on disconnection

### **Message Signing Verification**
- Timestamped messages prevent replay attacks
- Cryptographic signature verification
- Public key validation against session

### **Error Handling**
- Graceful handling of wallet not installed
- User-friendly error messages
- Connection timeout handling
- Signature verification failures

## 🎨 UI/UX Features

### **Dynamic Button States**
- **Not Connected**: "Wallet Connect"
- **Connected**: "✓ Connected [address]"
- **Disconnected**: Returns to "Wallet Connect"

### **Status Messages**
- Connection progress feedback
- Error messages with solutions
- Success confirmations
- Install prompts for missing wallet

### **Visual Design**
- Phantom-branded gradient colors (#9945ff to #14f195)
- Smooth hover animations
- Responsive design
- Consistent with X Connect styling

## 🚀 Next Steps

### **Potential Enhancements:**

1. **Token Balance Display**
   - Show SOL balance
   - Display SPL token holdings

2. **Transaction Signing**
   - Send SOL transactions
   - Interact with Solana programs

3. **NFT Integration**
   - Display user's NFTs
   - NFT-based authentication

4. **Multi-Wallet Support**
   - Add Solflare wallet
   - Add Backpack wallet
   - Universal wallet adapter

5. **DeFi Features**
   - Swap tokens
   - Staking integration
   - DeFi protocol interactions

## 🐛 Troubleshooting

### **Common Issues:**

**"Phantom wallet not found"**
- Install Phantom browser extension
- Refresh the page after installation

**"Connection rejected by user"**
- User clicked "Cancel" in Phantom popup
- Try connecting again

**"Connection request already pending"**
- Check Phantom wallet for pending connection
- Approve or reject, then try again

**"Failed to sign message"**
- User rejected signing request
- Try signing again

### **Debug Tips:**
- Check browser console for detailed errors
- Verify Phantom wallet is unlocked
- Ensure website is loaded over HTTPS
- Check Flask backend logs in Render

Your Phantom wallet integration is now complete and ready for testing! 🎉
