import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine } from "recharts";

interface DataPoint {
  time: string;
  price: number;
}

const BtcChart = () => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [currentPrice, setCurrentPrice] = useState(45250);

  // Generate initial data
  useEffect(() => {
    const initialData: DataPoint[] = [];
    const now = Date.now();
    let price = 45000;

    for (let i = 50; i >= 0; i--) {
      const time = new Date(now - i * 60000).toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      
      // Simulate price movement
      price += (Math.random() - 0.5) * 1000;
      price = Math.max(price, 40000); // Floor
      price = Math.min(price, 50000); // Ceiling
      
      initialData.push({ time, price: Math.round(price) });
    }
    
    setData(initialData);
    setCurrentPrice(Math.round(price));
  }, []);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const timeString = now.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit' 
      });

      setData(prevData => {
        const newPrice = prevData[prevData.length - 1]?.price || 45000;
        const priceChange = (Math.random() - 0.5) * 500;
        const updatedPrice = Math.round(Math.max(40000, Math.min(50000, newPrice + priceChange)));
        
        setCurrentPrice(updatedPrice);
        
        const newData = [
          ...prevData.slice(-49),
          { time: timeString, price: updatedPrice }
        ];
        
        return newData;
      });
    }, 3000); // Update every 3 seconds

    return () => clearInterval(interval);
  }, []);

  const priceChange = data.length >= 2 ? data[data.length - 1].price - data[data.length - 2].price : 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="bg-gradient-card border border-border rounded-2xl p-6 shadow-card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-foreground mb-1">Bitcoin (BTC)</h3>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-bold text-emerald">
              ${currentPrice.toLocaleString()}
            </span>
            <span className={`text-sm font-medium px-2 py-1 rounded-full ${
              isPositive 
                ? 'text-emerald bg-emerald/10' 
                : 'text-destructive bg-destructive/10'
            }`}>
              {isPositive ? '+' : ''}{priceChange.toFixed(0)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-emerald rounded-full animate-glow-pulse"></div>
          <span className="text-sm text-muted-foreground">Live</span>
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--emerald))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--emerald))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="time" 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              interval="preserveStartEnd"
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              domain={['dataMin - 500', 'dataMax + 500']}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--popover))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: '0 8px 32px -8px hsl(var(--background) / 0.6)'
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Price']}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="hsl(var(--emerald))" 
              strokeWidth={3}
              fill="url(#priceGradient)"
              dot={false}
              activeDot={{ 
                r: 6, 
                fill: 'hsl(var(--emerald))',
                stroke: 'hsl(var(--background))',
                strokeWidth: 2
              }}
            />
            <ReferenceLine 
              y={40000} 
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              strokeDasharray="8 4"
              label={{
                value: "Wager Target: $40,000",
                position: "insideTopRight",
                style: {
                  fill: "hsl(var(--primary))",
                  fontSize: "12px",
                  fontWeight: "600"
                }
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default BtcChart;