import { useState } from "react";
import LiquidGlassPopup from "@/components/LiquidGlassPopup";
import Header from "@/components/Header";
import BtcChart from "@/components/BtcChart";
import BettingMarketplace from "@/components/BettingMarketplace";
const Index = () => {
  const [showPopup, setShowPopup] = useState(true);
  const handlePopupAccept = () => {
    setShowPopup(false);
  };
  return <div className="min-h-screen bg-background">
      {/* Main Content */}
      <div className={`transition-all duration-700 ${showPopup ? 'blur-sm scale-95' : ''}`}>
        <Header />
        
        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="space-y-8">
            {/* Welcome Section */}
            

            {/* BTC Chart */}
            <BtcChart />

            {/* Betting Marketplace */}
            <BettingMarketplace />
          </div>
        </main>
      </div>

      {/* Liquid Glass Popup */}
      {showPopup && <LiquidGlassPopup onAccept={handlePopupAccept} />}
    </div>;
};
export default Index;