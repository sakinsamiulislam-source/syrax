import React from "react";

interface SyraxLogoProps {
  className?: string;
  size?: number;
  showWordmark?: boolean;
  subtitle?: string;
}

export const SyraxLogo: React.FC<SyraxLogoProps> = ({
  className = "",
  size = 38,
  showWordmark = true,
  subtitle = "Autonomous AI Trading & Sub-Account OS",
}) => {
  return (
    <div className={`flex items-center gap-3 select-none shrink-0 ${className}`}>
      {/* Geometric S-Monogram Icon Container */}
      <div
        className="relative flex items-center justify-center rounded-xl bg-[#080C14] border border-cyan-500/40 p-2 shadow-lg shadow-cyan-500/15 group hover:border-cyan-400 hover:shadow-cyan-500/30 transition-all duration-300 shrink-0"
        style={{ width: size, height: size }}
      >
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Top Geometric S-Segment (Crisp Solid White) */}
          <path
            d="M20 20 H80 L66 35 H36 V48 L20 40 Z"
            fill="#FFFFFF"
          />

          {/* Bottom Geometric S-Segment (Crisp Solid White) */}
          <path
            d="M80 80 H20 L34 65 H64 V52 L80 60 Z"
            fill="#FFFFFF"
          />

          {/* Dynamic Central S-Spine & Upward Market Arrow (Electric Cyan #00E5FF) */}
          {/* Arrow Shaft / Center Diagonal */}
          <polygon
            points="24,62 38,50 64,28 78,16 68,36 52,48 34,64"
            fill="#00E5FF"
          />
          {/* Arrowhead (North-East Trajectory) */}
          <polygon
            points="78,16 54,16 62,24 78,16"
            fill="#00E5FF"
          />
          <polygon
            points="78,16 78,40 70,32 78,16"
            fill="#00E5FF"
          />

          {/* AI Precision Nodes */}
          <circle cx="28" cy="27.5" r="3" fill="#00E5FF" />
          <circle cx="72" cy="72.5" r="3" fill="#00E5FF" />
        </svg>
      </div>

      {/* Modern Bold Geometric Wordmark & Badge */}
      {showWordmark && (
        <div className="flex flex-col justify-center min-w-0">
          <div className="flex items-center gap-2 flex-nowrap whitespace-nowrap">
            <span className="text-base sm:text-lg font-black tracking-widest text-white font-sans uppercase leading-none">
              SYRAX
            </span>
            <span className="inline-flex items-center text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-300 border border-amber-500/40 tracking-tight shadow-sm leading-none whitespace-nowrap">
              Powered by Binance Agent OS
            </span>
          </div>
          {subtitle && (
            <p className="text-[10px] text-slate-400 font-medium tracking-tight mt-1 leading-none whitespace-nowrap">
              {subtitle}
            </p>
          )}
        </div>
      )}
    </div>
  );
};
