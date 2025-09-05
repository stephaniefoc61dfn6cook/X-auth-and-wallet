import { Button } from "@/components/ui/button";
import { Wallet, Twitter } from "lucide-react";
import { useState, useEffect } from "react";

declare global {
  interface Window {
    solana?: {
      isPhantom?: boolean;
      connect: () => Promise<{ publicKey: { toString: () => string } }>;
      disconnect: () => Promise<void>;
      signMessage: (message: Uint8Array, encoding: string) => Promise<{
        signature: Uint8Array;
        publicKey: { toString: () => string };
      }>;
    };
  }
}

const Header = () => {
  const [xpPoints] = useState(2450);
  const [walletConnected, setWalletConnected] = useState(false);
  const [xConnected, setXConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string>("");
  const [xUsername, setXUsername] = useState<string>("");
  const [status, setStatus] = useState<{ type: 'success' | 'error' | '', message: string }>({ type: '', message: '' });

  // Check authentication status on component mount
  useEffect(() => {
    checkAuthStatus();
    checkPhantomStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/auth/status', {
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.authenticated) {
        setXConnected(true);
        setXUsername(data.user.username || data.user.name);
      }
    } catch (error) {
      console.error('Auth status check error:', error);
    }
  };

  const checkPhantomStatus = async () => {
    try {
      const response = await fetch('/auth/phantom/status', {
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.connected) {
        setWalletConnected(true);
        setWalletAddress(data.publicKey);
      }
    } catch (error) {
      console.error('Phantom status check error:', error);
    }
  };

  const handleXConnect = async () => {
    if (xConnected) {
      // Disconnect
      try {
        const response = await fetch('/auth/logout', {
          method: 'GET',
          credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
          setXConnected(false);
          setXUsername("");
          setStatus({ type: 'success', message: 'Disconnected from X successfully!' });
          setTimeout(() => setStatus({ type: '', message: '' }), 3000);
        }
      } catch (error) {
        console.error('Disconnect error:', error);
        setStatus({ type: 'error', message: 'Failed to disconnect. Please try again.' });
        setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      }
      return;
    }

    try {
      // Call backend to initiate X OAuth
      const response = await fetch('/auth/x/login', {
        method: 'GET',
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Open X OAuth in a popup window
        const popup = window.open(
          data.auth_url,
          'x_oauth',
          'width=600,height=700,scrollbars=yes,resizable=yes'
        );
        
        // Listen for authentication completion
        const handleMessage = (event: MessageEvent) => {
          if (event.data.type === 'X_AUTH_SUCCESS') {
            popup?.close();
            setXConnected(true);
            setXUsername(event.data.user.username);
            setStatus({ type: 'success', message: `X connected successfully! Welcome, ${event.data.user.name || event.data.user.username}!` });
            setTimeout(() => setStatus({ type: '', message: '' }), 3000);
            window.removeEventListener('message', handleMessage);
          }
        };
        
        window.addEventListener('message', handleMessage);
        
        // Check if popup was closed without authentication
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            window.removeEventListener('message', handleMessage);
            // Check authentication status
            checkAuthStatus();
          }
        }, 1000);
        
      } else {
        setStatus({ type: 'error', message: 'Failed to initiate X authentication: ' + (data.error || 'Unknown error') });
        setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      }
      
    } catch (error) {
      console.error('X Connect error:', error);
      setStatus({ type: 'error', message: 'Connection error. Please try again.' });
      setTimeout(() => setStatus({ type: '', message: '' }), 3000);
    }
  };

  const handleWalletConnect = async () => {
    if (walletConnected) {
      // Disconnect
      try {
        // Disconnect from Phantom
        if (window.solana && window.solana.disconnect) {
          await window.solana.disconnect();
        }
        
        // Notify backend
        const response = await fetch('/auth/phantom/disconnect', {
          method: 'POST',
          credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
          setWalletConnected(false);
          setWalletAddress("");
          setStatus({ type: 'success', message: 'Phantom wallet disconnected successfully!' });
          setTimeout(() => setStatus({ type: '', message: '' }), 3000);
        }
        
      } catch (error) {
        console.error('Disconnect error:', error);
        setStatus({ type: 'error', message: 'Failed to disconnect. Please try again.' });
        setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      }
      return;
    }

    // Check if Phantom wallet is available
    if (!window.solana || !window.solana.isPhantom) {
      setStatus({ type: 'error', message: 'Phantom wallet not found! Please install Phantom wallet extension.' });
      setTimeout(() => setStatus({ type: '', message: '' }), 5000);
      return;
    }
    
    try {
      setStatus({ type: 'success', message: 'Connecting to Phantom wallet...' });
      
      // Connect to Phantom wallet
      const response = await window.solana.connect();
      const publicKey = response.publicKey.toString();
      
      // Send connection info to backend
      const backendResponse = await fetch('/auth/phantom/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          publicKey: publicKey
        })
      });
      
      const data = await backendResponse.json();
      
      if (data.success) {
        setWalletConnected(true);
        setWalletAddress(publicKey);
        const shortKey = publicKey.substring(0, 4) + '...' + publicKey.substring(publicKey.length - 4);
        setStatus({ type: 'success', message: `Phantom wallet connected! ${shortKey}` });
        setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      } else {
        setStatus({ type: 'error', message: 'Failed to connect wallet: ' + (data.error || 'Unknown error') });
        setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      }
      
    } catch (error: any) {
      console.error('Phantom wallet connection error:', error);
      
      if (error.code === 4001) {
        setStatus({ type: 'error', message: 'Connection rejected by user.' });
      } else if (error.code === -32002) {
        setStatus({ type: 'error', message: 'Connection request already pending. Check your wallet.' });
      } else {
        setStatus({ type: 'error', message: 'Failed to connect wallet. Please try again.' });
      }
      setTimeout(() => setStatus({ type: '', message: '' }), 3000);
    }
  };

  const handleSignMessage = async () => {
    if (!window.solana) return;
    
    try {
      const message = `Sign this message to verify your wallet ownership.\nTimestamp: ${new Date().toISOString()}`;
      const encodedMessage = new TextEncoder().encode(message);
      
      setStatus({ type: 'success', message: 'Please sign the message in your Phantom wallet...' });
      
      // Request signature from Phantom
      const signedMessage = await window.solana.signMessage(encodedMessage, 'utf8');
      
      // Send to backend for verification
      const response = await fetch('/auth/phantom/sign', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          message: message,
          signature: Array.from(signedMessage.signature),
          publicKey: signedMessage.publicKey.toString()
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStatus({ type: 'success', message: 'Message signed successfully! ✓ Wallet verified' });
      } else {
        setStatus({ type: 'error', message: 'Failed to verify signature: ' + (data.error || 'Unknown error') });
      }
      setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      
    } catch (error: any) {
      console.error('Message signing error:', error);
      
      if (error.code === 4001) {
        setStatus({ type: 'error', message: 'Message signing rejected by user.' });
      } else {
        setStatus({ type: 'error', message: 'Failed to sign message. Please try again.' });
      }
      setTimeout(() => setStatus({ type: '', message: '' }), 3000);
    }
  };

  const getButtonText = (connected: boolean, username: string, address: string, defaultText: string, connectedText: string) => {
    if (!connected) return defaultText;
    if (username) return `✓ ${username}`;
    if (address) {
      const shortKey = address.substring(0, 4) + '...' + address.substring(address.length - 4);
      return `✓ ${shortKey}`;
    }
    return connectedText;
  };

  return (
    <div className="relative">
      <header className="w-full bg-gradient-card border-b border-border/50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left side - Connect buttons */}
        <div className="flex items-center gap-4">
          <Button onClick={handleXConnect} variant={xConnected ? "default" : "outline"} size="lg" className={`
              flex items-center gap-3 font-medium transition-all duration-300
              ${xConnected ? 'bg-gradient-primary text-primary-foreground shadow-emerald hover:shadow-glow' : 'border-emerald/30 text-emerald hover:bg-emerald/10 hover:border-emerald/50'}
            `}>
            <Twitter size={20} />
              {getButtonText(xConnected, xUsername, "", 'X Connect', 'X Connected')}
          </Button>
          
          <Button onClick={handleWalletConnect} variant={walletConnected ? "default" : "outline"} size="lg" className={`
              flex items-center gap-3 font-medium transition-all duration-300
              ${walletConnected ? 'bg-gradient-primary text-primary-foreground shadow-emerald hover:shadow-glow' : 'border-emerald/30 text-emerald hover:bg-emerald/10 hover:border-emerald/50'}
            `}>
            <Wallet size={20} />
              {getButtonText(walletConnected, "", walletAddress, 'Wallet Connect', 'Wallet Connected')}
            </Button>
            
            {walletConnected && (
              <Button onClick={handleSignMessage} variant="outline" size="lg" className="flex items-center gap-3 font-medium transition-all duration-300 border-purple-500/30 text-purple-400 hover:bg-purple-500/10 hover:border-purple-500/50">
                <span>✍️</span>
                Sign Message
          </Button>
            )}
        </div>

        {/* Center - Logo */}
        <div className="absolute left-1/2 transform -translate-x-1/2">
            <h1 className="text-2xl font-bold text-emerald">X-Connect</h1>
        </div>

        {/* Right side - User XP */}
        <div className="flex items-center gap-3">
          <div className="bg-gradient-card border border-emerald/20 rounded-full px-4 py-2 shadow-emerald/20">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald rounded-full animate-glow-pulse"></div>
              <span className="text-sm font-medium text-muted-foreground">XP</span>
              <span className="text-lg font-bold text-emerald">
                {xpPoints.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>
      </header>
      
      {/* Status Message */}
      {status.message && (
        <div className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 px-4 py-2 rounded-lg shadow-lg transition-all duration-300 ${
          status.type === 'success' 
            ? 'bg-emerald/10 border border-emerald/20 text-emerald' 
            : 'bg-destructive/10 border border-destructive/20 text-destructive'
        }`}>
          {status.message}
        </div>
      )}
    </div>
  );
};
export default Header;