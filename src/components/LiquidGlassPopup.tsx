import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

interface LiquidGlassPopupProps {
  onAccept: () => void;
}

const LiquidGlassPopup = ({ onAccept }: LiquidGlassPopupProps) => {
  const [isVisible, setIsVisible] = useState(true);

  const handleAccept = () => {
    setIsVisible(false);
    setTimeout(onAccept, 600); // Wait for animation to complete
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur effect */}
      <div className="absolute inset-0 backdrop-blur-sm bg-background/20" />
      
      {/* Glass popup */}
      <div className="relative animate-scale-in">
        <div className="bg-card/80 backdrop-blur-glass border border-emerald/20 rounded-2xl p-12 shadow-glow max-w-md w-full mx-4">
          {/* Glow effect */}
          <div className="absolute inset-0 bg-gradient-glow rounded-2xl opacity-60 animate-glow-pulse" />
          
          {/* Content */}
          <div className="relative z-10 text-center space-y-8">
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto bg-gradient-primary rounded-full flex items-center justify-center animate-float">
                <span className="text-2xl">₿</span>
              </div>
              <h2 className="text-3xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Ready to Betcoin?
              </h2>
              <p className="text-muted-foreground text-lg">
                Enter the future of crypto betting
              </p>
            </div>
            
            <Button 
              onClick={handleAccept}
              size="lg"
              className="w-full bg-gradient-primary hover:bg-gradient-primary/90 text-primary-foreground font-semibold py-4 text-lg shadow-emerald hover:shadow-glow transition-all duration-300 hover:scale-105"
            >
              Yes, Let's Go!
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiquidGlassPopup;