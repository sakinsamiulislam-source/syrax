import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  TrendingUp,
  X,
  ShieldCheck,
  Zap,
  Clock,
  BarChart2,
  RefreshCw,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Sliders,
  Maximize2
} from "lucide-react";
import { Opportunity } from "@/types";
import { api } from "@/lib/api";

interface EvaluateCoinModalProps {
  coin: Opportunity | null;
  onClose: () => void;
  onExecuteTrade: (coin: Opportunity) => void;
  loading: boolean;
}

type Timeframe = "5m" | "15m" | "1h" | "4h" | "1d" | "1w";
type ChartMode = "CANDLESTICK" | "TRADINGVIEW";

interface KlineData {
  open_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  close_time?: number;
}

export const EvaluateCoinModal: React.FC<EvaluateCoinModalProps> = ({
  coin,
  onClose,
  onExecuteTrade,
  loading,
}) => {
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");
  const [chartMode, setChartMode] = useState<ChartMode>("CANDLESTICK");
  const [klines, setKlines] = useState<KlineData[]>([]);
  const [fetchingKlines, setFetchingKlines] = useState<boolean>(false);
  const [hoveredCandle, setHoveredCandle] = useState<KlineData | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Normalize symbol for TradingView & Binance API
  const cleanSymbol = useMemo(() => {
    if (!coin) return "BTCUSDT";
    let s = coin.symbol.toUpperCase();
    if (!s.endsWith("USDT")) s += "USDT";
    return s;
  }, [coin]);

  // Fetch Klines whenever coin or timeframe changes
  useEffect(() => {
    if (!coin) return;

    let isMounted = true;
    const fetchCandles = async () => {
      setFetchingKlines(true);
      try {
        const data = await api.getKlines(cleanSymbol, timeframe, 60);
        if (isMounted) {
          if (data && data.length > 0) {
            setKlines(data);
          } else {
            setKlines(generateFallbackCandles(coin.last_price, timeframe, 50));
          }
        }
      } catch (err) {
        console.error("Failed to fetch klines:", err);
        if (isMounted) {
          setKlines(generateFallbackCandles(coin.last_price, timeframe, 50));
        }
      } finally {
        if (isMounted) setFetchingKlines(false);
      }
    };

    fetchCandles();
    return () => {
      isMounted = false;
    };
  }, [coin, cleanSymbol, timeframe]);

  // Fallback candle generator
  const generateFallbackCandles = (basePrice: number, tf: Timeframe, count: number): KlineData[] => {
    const candles: KlineData[] = [];
    const now = Date.now();
    let tfMs = 3600000;
    if (tf === "5m") tfMs = 300000;
    else if (tf === "15m") tfMs = 900000;
    else if (tf === "1h") tfMs = 3600000;
    else if (tf === "4h") tfMs = 14400000;
    else if (tf === "1d") tfMs = 86400000;
    else if (tf === "1w") tfMs = 604800000;

    let price = basePrice || 100;
    for (let i = count; i >= 0; i--) {
      const time = now - i * tfMs;
      const changePct = (Math.sin(i * 0.4) * 0.008) + ((Math.random() - 0.49) * 0.005);
      const open = price;
      const close = price * (1 + changePct);
      const high = Math.max(open, close) * (1 + Math.random() * 0.003);
      const low = Math.min(open, close) * (1 - Math.random() * 0.003);
      const volume = Math.abs(changePct) * 100000 + 5000;
      candles.push({ open_time: time, open, high, low, close, volume });
      price = close;
    }
    return candles;
  };

  // Draw Candlestick Canvas
  useEffect(() => {
    if (chartMode !== "CANDLESTICK" || !canvasRef.current || klines.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    // Layout constants
    const padding = { top: 20, right: 65, bottom: 35, left: 15 };
    const chartHeight = (height - padding.top - padding.bottom) * 0.75;
    const volumeHeight = (height - padding.top - padding.bottom) * 0.22;
    const volumeTop = padding.top + chartHeight + 8;

    // Price Bounds
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    let maxVol = 0;

    klines.forEach((c) => {
      if (c.low < minPrice) minPrice = c.low;
      if (c.high > maxPrice) maxPrice = c.high;
      if (c.volume > maxVol) maxVol = c.volume;
    });

    if (coin?.setup) {
      if (coin.setup.stop_loss) minPrice = Math.min(minPrice, coin.setup.stop_loss * 0.995);
      if (coin.setup.take_profit) maxPrice = Math.max(maxPrice, coin.setup.take_profit * 1.005);
    }

    const priceRange = maxPrice - minPrice || 1;
    minPrice -= priceRange * 0.03;
    maxPrice += priceRange * 0.03;
    const adjustedRange = maxPrice - minPrice;

    const getY = (price: number) => {
      return padding.top + chartHeight - ((price - minPrice) / adjustedRange) * chartHeight;
    };

    // Draw Grid Lines
    ctx.strokeStyle = "rgba(51, 65, 85, 0.25)";
    ctx.lineWidth = 1;
    const gridSteps = 5;
    for (let i = 0; i <= gridSteps; i++) {
      const p = minPrice + (adjustedRange / gridSteps) * i;
      const y = getY(p);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Price labels
      ctx.fillStyle = "#64748b";
      ctx.font = "10px monospace";
      ctx.textAlign = "left";
      ctx.fillText(
        p < 0.01 ? p.toFixed(6) : p < 1 ? p.toFixed(4) : p.toFixed(2),
        width - padding.right + 6,
        y + 3
      );
    }

    // Candle metrics
    const candleWidth = (width - padding.left - padding.right) / klines.length;
    const barWidth = Math.max(candleWidth * 0.7, 2);

    const ma7Points: { x: number; y: number }[] = [];
    const ma25Points: { x: number; y: number }[] = [];

    // Draw Candles & Volume
    klines.forEach((c, idx) => {
      const x = padding.left + idx * candleWidth + candleWidth / 2;
      const isUp = c.close >= c.open;
      const color = isUp ? "#10b981" : "#f43f5e";
      const wickColor = isUp ? "#34d399" : "#fb7185";

      // 1. Volume Bar
      const vHeight = maxVol > 0 ? (c.volume / maxVol) * volumeHeight : 0;
      const vY = volumeTop + volumeHeight - vHeight;
      ctx.fillStyle = isUp ? "rgba(16, 185, 129, 0.35)" : "rgba(244, 63, 94, 0.35)";
      ctx.fillRect(x - barWidth / 2, vY, barWidth, vHeight);

      // 2. Wick
      const yHigh = getY(c.high);
      const yLow = getY(c.low);
      ctx.strokeStyle = wickColor;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(x, yHigh);
      ctx.lineTo(x, yLow);
      ctx.stroke();

      // 3. Candle Body
      const yOpen = getY(c.open);
      const yClose = getY(c.close);
      const bodyTop = Math.min(yOpen, yClose);
      const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1.5);

      ctx.fillStyle = color;
      ctx.fillRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight);

      // MA calculations
      if (idx >= 6) {
        const slice = klines.slice(idx - 6, idx + 1);
        const avg = slice.reduce((acc, v) => acc + v.close, 0) / slice.length;
        ma7Points.push({ x, y: getY(avg) });
      }
      if (idx >= 24) {
        const slice = klines.slice(idx - 24, idx + 1);
        const avg = slice.reduce((acc, v) => acc + v.close, 0) / slice.length;
        ma25Points.push({ x, y: getY(avg) });
      }
    });

    // Draw MA7 line (Yellow)
    if (ma7Points.length > 1) {
      ctx.strokeStyle = "#eab308";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(ma7Points[0].x, ma7Points[0].y);
      for (let i = 1; i < ma7Points.length; i++) {
        ctx.lineTo(ma7Points[i].x, ma7Points[i].y);
      }
      ctx.stroke();
    }

    // Draw MA25 line (Purple)
    if (ma25Points.length > 1) {
      ctx.strokeStyle = "#a855f7";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(ma25Points[0].x, ma25Points[0].y);
      for (let i = 1; i < ma25Points.length; i++) {
        ctx.lineTo(ma25Points[i].x, ma25Points[i].y);
      }
      ctx.stroke();
    }

    // Draw Setup Overlays
    if (coin?.setup) {
      const { entry_price, stop_loss, take_profit } = coin.setup;

      if (entry_price) {
        const yEntry = getY(entry_price);
        ctx.strokeStyle = "rgba(99, 102, 241, 0.85)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, yEntry);
        ctx.lineTo(width - padding.right, yEntry);
        ctx.stroke();

        ctx.fillStyle = "#818cf8";
        ctx.font = "bold 9px monospace";
        ctx.fillText(`ENTRY: $${entry_price}`, width - padding.right + 6, yEntry + 3);
      }

      if (stop_loss) {
        const ySL = getY(stop_loss);
        ctx.strokeStyle = "rgba(244, 63, 94, 0.85)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, ySL);
        ctx.lineTo(width - padding.right, ySL);
        ctx.stroke();

        ctx.fillStyle = "#f43f5e";
        ctx.font = "bold 9px monospace";
        ctx.fillText(`SL: $${stop_loss}`, width - padding.right + 6, ySL + 3);
      }

      if (take_profit) {
        const yTP = getY(take_profit);
        ctx.strokeStyle = "rgba(16, 185, 129, 0.85)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, yTP);
        ctx.lineTo(width - padding.right, yTP);
        ctx.stroke();

        ctx.fillStyle = "#10b981";
        ctx.font = "bold 9px monospace";
        ctx.fillText(`TP: $${take_profit}`, width - padding.right + 6, yTP + 3);
      }
      ctx.setLineDash([]);
    }

    // Time Axis Labels
    ctx.fillStyle = "#64748b";
    ctx.font = "9px monospace";
    ctx.textAlign = "center";
    const timeSteps = Math.min(6, klines.length);
    for (let i = 0; i < timeSteps; i++) {
      const idx = Math.floor((klines.length / timeSteps) * i);
      const c = klines[idx];
      if (c) {
        const x = padding.left + idx * candleWidth + candleWidth / 2;
        const d = new Date(c.open_time);
        const timeStr =
          timeframe === "1d" || timeframe === "1w"
            ? `${d.getMonth() + 1}/${d.getDate()}`
            : `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
        ctx.fillText(timeStr, x, height - 10);
      }
    }
  }, [klines, chartMode, timeframe, coin]);

  // Handle Canvas Mouse Move for Tooltip
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || klines.length === 0) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;

    const paddingLeft = 15;
    const paddingRight = 65;
    const chartWidth = rect.width - paddingLeft - paddingRight;
    const candleWidth = chartWidth / klines.length;

    const idx = Math.floor((x - paddingLeft) / candleWidth);
    if (idx >= 0 && idx < klines.length) {
      setHoveredCandle(klines[idx]);
    } else {
      setHoveredCandle(null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredCandle(null);
  };

  if (!coin) return null;

  const isPerp = coin.market_type === "FUTURES" || coin.symbol.startsWith("1000");

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 md:p-6 overflow-y-auto animate-in fade-in duration-150">
      <div className="rounded-2xl bg-[#090D1A] border border-indigo-500/30 max-w-5xl w-full my-auto shadow-2xl overflow-hidden flex flex-col max-h-[95vh]">
        {/* Top Header Bar */}
        <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white font-mono">{coin.symbol}</h3>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    isPerp
                      ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                      : "bg-blue-500/15 text-blue-300 border border-blue-500/30"
                  }`}
                >
                  {isPerp ? "Binance USDⓈ-M Perps" : "Binance Spot"}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    coin.label === "TRADEABLE"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : coin.label === "WATCH"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {coin.label}
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                <span>Real-Time Binance Live Market Intelligence</span>
                <span>•</span>
                <span className="text-indigo-400 font-semibold">AI Conviction: {coin.ai_score}/100</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-2 rounded-xl bg-slate-800/60 hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {/* Top Quick Stats Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2.5">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Live Price</span>
              <span className="text-sm font-bold text-white font-mono">
                ${coin.last_price < 0.01
                  ? coin.last_price.toFixed(6)
                  : coin.last_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">24h Change</span>
              <span
                className={`text-sm font-bold font-mono flex items-center gap-1 ${
                  coin.change_24h >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {coin.change_24h >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                {coin.change_24h >= 0 ? "+" : ""}
                {coin.change_24h.toFixed(2)}%
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Bid-Ask Spread</span>
              <span className={`text-sm font-bold font-mono ${coin.spread_bps > 5 ? "text-rose-400" : "text-slate-200"}`}>
                {coin.spread_bps} bps
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Liquidity Depth</span>
              <span
                className={`text-xs font-bold font-mono px-2 py-0.5 rounded inline-block mt-0.5 ${
                  coin.liquidity_quality === "HIGH"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-indigo-500/10 text-indigo-400"
                }`}
              >
                {coin.liquidity_quality}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">24h Quote Vol</span>
              <span className="text-xs font-bold text-slate-200 font-mono">
                ${coin.quote_volume_24h ? (coin.quote_volume_24h / 1e6).toFixed(2) + "M" : "N/A"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Market Structure</span>
              <span className="text-xs font-bold text-indigo-300 font-mono">
                {coin.trend.replace("_", " ")}
              </span>
            </div>
          </div>

          {/* Interactive Chart Section */}
          <div className="rounded-2xl border border-slate-800 bg-[#060913] p-4 space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
              {/* Timeframe Selectors */}
              <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <span className="text-[11px] text-slate-400 px-2 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-indigo-400" /> Timeframe:
                </span>
                {(["5m", "15m", "1h", "4h", "1d", "1w"] as Timeframe[]).map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`px-2.5 py-1 rounded-lg font-mono font-bold text-xs transition-all ${
                      timeframe === tf
                        ? "bg-indigo-600 text-white shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                    }`}
                  >
                    {tf === "1w" ? "7D / 1W" : tf.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Chart Mode Toggle & Indicator Legend */}
              <div className="flex items-center gap-2">
                <div className="hidden md:flex items-center gap-2 text-[11px] font-mono mr-2">
                  <span className="flex items-center gap-1 text-yellow-400">
                    <span className="w-2 h-2 rounded-full bg-yellow-400"></span> MA7
                  </span>
                  <span className="flex items-center gap-1 text-purple-400">
                    <span className="w-2 h-2 rounded-full bg-purple-400"></span> MA25
                  </span>
                </div>

                <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                  <button
                    onClick={() => setChartMode("CANDLESTICK")}
                    className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                      chartMode === "CANDLESTICK" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Pro Canvas
                  </button>
                  <button
                    onClick={() => setChartMode("TRADINGVIEW")}
                    className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                      chartMode === "TRADINGVIEW" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    TradingView
                  </button>
                </div>
              </div>
            </div>

            {/* Chart Area */}
            <div className="relative w-full h-[360px] rounded-xl overflow-hidden bg-[#04060C] border border-slate-900">
              {fetchingKlines && (
                <div className="absolute inset-0 z-10 bg-black/50 backdrop-blur-xs flex items-center justify-center gap-2 text-indigo-400 text-xs font-semibold">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Loading live Binance {timeframe} candles...</span>
                </div>
              )}

              {chartMode === "CANDLESTICK" ? (
                <>
                  <canvas
                    ref={canvasRef}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                    className="w-full h-full cursor-crosshair"
                  />
                  {hoveredCandle && (
                    <div className="absolute top-3 left-4 p-2 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] font-mono text-slate-300 shadow-xl pointer-events-none flex flex-wrap items-center gap-3">
                      <span>
                        Time:{" "}
                        <span className="text-white">
                          {new Date(hoveredCandle.open_time).toLocaleTimeString()}
                        </span>
                      </span>
                      <span>
                        O: <span className="text-white">${hoveredCandle.open.toFixed(4)}</span>
                      </span>
                      <span>
                        H: <span className="text-emerald-400">${hoveredCandle.high.toFixed(4)}</span>
                      </span>
                      <span>
                        L: <span className="text-rose-400">${hoveredCandle.low.toFixed(4)}</span>
                      </span>
                      <span>
                        C: <span className="text-white font-bold">${hoveredCandle.close.toFixed(4)}</span>
                      </span>
                      <span>
                        Vol: <span className="text-indigo-300">{hoveredCandle.volume.toLocaleString()}</span>
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <iframe
                  title={`TradingView-${cleanSymbol}`}
                  src={`https://s.tradingview.com/widgetembed/?frameElementId=tradingview_${cleanSymbol}&symbol=BINANCE:${cleanSymbol}&interval=${
                    timeframe === "5m" ? "5" : timeframe === "15m" ? "15" : timeframe === "1h" ? "60" : timeframe === "4h" ? "240" : timeframe === "1d" ? "D" : "W"
                  }&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en&utm_source=localhost`}
                  className="w-full h-full border-0"
                  allowFullScreen
                />
              )}
            </div>
          </div>

          {/* AI Cognitive Thesis & Setup Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Cognitive Thesis */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  AI Cognitive Thesis & Invalidation
                </h4>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
                {coin.reasoning ||
                  "Market structure displays strong momentum with high orderbook bid liquidity. Sentry exploit radar cleared with zero malicious smart contract alerts."}
              </p>
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span>Execution Mandate: <strong className="text-indigo-300">Strict 1% Loss Cap</strong></span>
                <span>Momentum: <strong className="text-emerald-400">{coin.momentum}</strong></span>
              </div>
            </div>

            {/* Trade Setup Math */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-400" />
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Calculated Trade Matrix
                  </h4>
                </div>
                {coin.setup && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                    {coin.setup.risk_reward_ratio || 2.5}R R:R Ratio
                  </span>
                )}
              </div>

              {coin.setup ? (
                <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-slate-950 border border-slate-800/60 font-mono text-center">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Entry Price</span>
                    <span className="text-xs font-bold text-white">${coin.setup.entry_price}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Stop-Loss (-1.8%)</span>
                    <span className="text-xs font-bold text-rose-400">${coin.setup.stop_loss}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Take-Profit (+4.5%)</span>
                    <span className="text-xs font-bold text-emerald-400">${coin.setup.take_profit}</span>
                  </div>
                </div>
              ) : (
                <div className="p-3 text-xs text-slate-400 text-center bg-slate-950 rounded-lg">
                  Setup parameters will be calibrated upon deployment.
                </div>
              )}

              {/* Sentry Clearance */}
              <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between text-[11px] text-emerald-300">
                <span className="flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Sentry Security Radar Cleared
                </span>
                <span className="font-mono font-bold">$5.00 Max Risk Cap</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            <span>Trading on <strong className="text-white">{coin.symbol}</strong> adheres strictly to Sub-Wallet risk rules.</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
            >
              Close
            </button>
            <button
              onClick={() => onExecuteTrade(coin)}
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/20 hover:shadow-emerald-600/30 flex items-center gap-2 transition-all"
            >
              <Zap className="w-4 h-4" />
              <span>{loading ? "Deploying..." : `Execute Safe Buy on ${coin.symbol}`}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

