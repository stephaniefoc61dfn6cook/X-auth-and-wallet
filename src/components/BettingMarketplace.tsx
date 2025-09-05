import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { TrendingUp, TrendingDown, Clock, Users, DollarSign } from "lucide-react";
interface BetData {
  abovePot: number;
  belowPot: number;
  aboveBets: number;
  belowBets: number;
  targetPrice: number;
  timeLeft: number;
}
interface LiveBet {
  id: string;
  username: string;
  amount: number;
  type: 'above' | 'below';
  timestamp: Date;
}
const BettingMarketplace = () => {
  const [betData, setBetData] = useState<BetData>({
    abovePot: 15750,
    belowPot: 8920,
    aboveBets: 47,
    belowBets: 23,
    targetPrice: 40000,
    timeLeft: 18 * 3600 + 45 * 60 + 23 // 18h 45m 23s in seconds
  });
  const [betAmount, setBetAmount] = useState("");
  const [userBet, setUserBet] = useState<{
    type: 'above' | 'below' | null;
    amount: number;
  }>({
    type: null,
    amount: 0
  });
  const [liveFeed, setLiveFeed] = useState<LiveBet[]>([]);

  // Random X usernames for simulation
  const xUsernames = ['@CryptoWolf2024', '@BTCMaximalist', '@DiamondHandsDAO', '@SatoshiFollower', '@CoinMaster88', '@BlockchainBro', '@CryptoPumper', '@HODLgang', '@BitcoinBull', '@AltcoinAlpha', '@DegenTrader', '@CryptoWhale42', '@SatStackr', '@BTCBeliever', '@CoinFlipKing', '@CryptoSage', '@DigitalGold', '@BlockRewards', '@CryptoNinja', '@BitBeast'];

  // Calculate dynamic odds
  const totalPot = betData.abovePot + betData.belowPot;
  const aboveOdds = totalPot / betData.abovePot;
  const belowOdds = totalPot / betData.belowPot;

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setBetData(prev => ({
        ...prev,
        timeLeft: Math.max(0, prev.timeLeft - 1)
      }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Simulate other users betting
  useEffect(() => {
    const simulateBets = setInterval(() => {
      const isAboveBet = Math.random() > 0.4; // 60% chance for above bets
      const betAmount = Math.floor(Math.random() * 500) + 100;
      const randomUsername = xUsernames[Math.floor(Math.random() * xUsernames.length)];

      // Add to live feed
      const newBet: LiveBet = {
        id: Math.random().toString(36).substr(2, 9),
        username: randomUsername,
        amount: betAmount,
        type: isAboveBet ? 'above' : 'below',
        timestamp: new Date()
      };
      setLiveFeed(prev => [newBet, ...prev].slice(0, 8)); // Keep only latest 8 bets

      setBetData(prev => ({
        ...prev,
        abovePot: prev.abovePot + (isAboveBet ? betAmount : 0),
        belowPot: prev.belowPot + (!isAboveBet ? betAmount : 0),
        aboveBets: prev.aboveBets + (isAboveBet ? 1 : 0),
        belowBets: prev.belowBets + (!isAboveBet ? 1 : 0)
      }));
    }, 5000); // New bet every 5 seconds

    return () => clearInterval(simulateBets);
  }, []);
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor(seconds % 3600 / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  const handleBet = (type: 'above' | 'below') => {
    const amount = parseFloat(betAmount);
    if (amount > 0) {
      setUserBet({
        type,
        amount
      });
      setBetData(prev => ({
        ...prev,
        abovePot: prev.abovePot + (type === 'above' ? amount : 0),
        belowPot: prev.belowPot + (type === 'below' ? amount : 0),
        aboveBets: prev.aboveBets + (type === 'above' ? 1 : 0),
        belowBets: prev.belowBets + (type === 'below' ? 1 : 0)
      }));
      setBetAmount("");
    }
  };
  const abovePercentage = betData.abovePot / totalPot * 100;
  const belowPercentage = betData.belowPot / totalPot * 100;
  return <Card className="bg-gradient-card border border-border rounded-2xl p-6 shadow-card">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-foreground mb-1">24H BTC Marketplace</h3>
            
          </div>
          <div className="flex items-center gap-2 bg-gradient-card border border-emerald/20 rounded-full px-4 py-2">
            <Clock size={16} className="text-emerald" />
            <span className="text-lg font-mono font-bold text-emerald">
              {formatTime(betData.timeLeft)}
            </span>
          </div>
        </div>

        {/* Betting Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Above Bet */}
          <div className="bg-gradient-card border border-emerald/20 rounded-xl p-4 space-y-3 transition-all duration-300 hover:shadow-glow hover:border-emerald/40 hover:scale-[1.02] cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="text-emerald" size={20} />
                <span className="font-semibold text-foreground">Above ${betData.targetPrice.toLocaleString()}</span>
              </div>
              <span className="text-xl font-bold text-emerald">{aboveOdds.toFixed(2)}x</span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Pool: ${betData.abovePot.toLocaleString()}</span>
                <span>{betData.aboveBets} bets</span>
              </div>
              <Progress value={abovePercentage} className="h-2" />
              <div className="text-xs text-muted-foreground">{abovePercentage.toFixed(1)}% of total pot</div>
            </div>

            <Button onClick={() => handleBet('above')} disabled={!betAmount || betData.timeLeft === 0} className="w-full bg-emerald hover:bg-emerald/90 text-primary-foreground font-semibold transition-all duration-200 hover:scale-105 active:scale-95 active:shadow-glow">
              Bet Above
            </Button>
          </div>

          {/* Below Bet */}
          <div className="bg-gradient-card border border-destructive/20 rounded-xl p-4 space-y-3 transition-all duration-300 hover:shadow-glow hover:border-destructive/40 hover:scale-[1.02] cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingDown className="text-destructive" size={20} />
                <span className="font-semibold text-foreground">Below ${betData.targetPrice.toLocaleString()}</span>
              </div>
              <span className="text-xl font-bold text-destructive">{belowOdds.toFixed(2)}x</span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Pool: ${betData.belowPot.toLocaleString()}</span>
                <span>{betData.belowBets} bets</span>
              </div>
              <Progress value={belowPercentage} className="h-2" />
              <div className="text-xs text-muted-foreground">{belowPercentage.toFixed(1)}% of total pot</div>
            </div>

            <Button onClick={() => handleBet('below')} disabled={!betAmount || betData.timeLeft === 0} variant="destructive" className="w-full font-semibold transition-all duration-200 hover:scale-105 active:scale-95 active:shadow-glow">
              Bet Below
            </Button>
          </div>
        </div>

        {/* Betting Input */}
        <div className="flex gap-3">
          <Input type="number" placeholder="Enter bet amount ($)" value={betAmount} onChange={e => setBetAmount(e.target.value)} className="flex-1 bg-input border-border" disabled={betData.timeLeft === 0} />
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setBetAmount("100")} disabled={betData.timeLeft === 0}>
              $100
            </Button>
            <Button variant="outline" onClick={() => setBetAmount("500")} disabled={betData.timeLeft === 0}>
              $500
            </Button>
          </div>
        </div>

        {/* User's Current Bet */}
        {userBet.type && <div className="bg-emerald/10 border border-emerald/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign size={16} className="text-emerald" />
              <span className="font-semibold text-foreground">Your Bet</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">
                ${userBet.amount} on BTC {userBet.type} ${betData.targetPrice.toLocaleString()}
              </span>
              <span className="font-bold text-emerald">
                Potential Win: ${(userBet.amount * (userBet.type === 'above' ? aboveOdds : belowOdds)).toFixed(2)}
              </span>
            </div>
          </div>}

        {/* Live Betting Feed */}
        <div className="pt-4 border-t border-border/50">
          <div className="flex items-center gap-2 mb-4">
            <Users size={16} className="text-emerald" />
            <h4 className="text-lg font-semibold text-foreground">Live Betting Activity</h4>
          </div>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {liveFeed.length === 0 ? <div className="text-center py-4 text-muted-foreground">
                Waiting for new bets...
              </div> : liveFeed.map(bet => <div key={bet.id} className="flex items-center justify-between bg-gradient-card border border-border/50 rounded-lg p-3 animate-fade-in">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-primary">X</span>
                    </div>
                    <div>
                      <div className="font-medium text-foreground">{bet.username}</div>
                      <div className="text-xs text-muted-foreground">
                        {bet.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground">${bet.amount}</span>
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${bet.type === 'above' ? 'bg-emerald/10 text-emerald' : 'bg-destructive/10 text-destructive'}`}>
                      {bet.type === 'above' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {bet.type.toUpperCase()}
                    </div>
                  </div>
                </div>)}
          </div>
        </div>

        {betData.timeLeft === 0 && <div className="text-center p-4 bg-muted/50 rounded-xl">
            <p className="text-lg font-semibold text-muted-foreground">
              Betting closed! Results will be available soon.
            </p>
          </div>}
      </div>
    </Card>;
};
export default BettingMarketplace;