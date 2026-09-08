import React, { useEffect, useState, useRef } from "react";

interface AnimatedNumberProps {
  value: number;
  format?: (n: number) => string;
  className?: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  highlightChange?: boolean;
}

export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  decimals,
  format = (n) => decimals !== undefined ? n.toFixed(decimals) : n.toFixed(2),
  className = "",
  prefix = "",
  suffix = "",
  highlightChange = true,
}) => {
  const [displayValue, setDisplayValue] = useState(value);
  const [changeDir, setChangeDir] = useState<"up" | "down" | null>(null);
  const prevValueRef = useRef(value);

  useEffect(() => {
    const prev = prevValueRef.current;
    if (prev !== value) {
      if (highlightChange) {
        if (value > prev) {
          setChangeDir("up");
        } else if (value < prev) {
          setChangeDir("down");
        }
        const timer = setTimeout(() => setChangeDir(null), 1200);
        prevValueRef.current = value;
        setDisplayValue(value);
        return () => clearTimeout(timer);
      } else {
        prevValueRef.current = value;
        setDisplayValue(value);
      }
    }
  }, [value, highlightChange]);

  const highlightClass =
    changeDir === "up"
      ? "text-emerald-400 flash-up transition-all"
      : changeDir === "down"
      ? "text-rose-400 flash-down transition-all"
      : "";

  return (
    <span className={`inline-flex items-baseline font-mono ${className} ${highlightClass}`}>
      {prefix}
      {format(displayValue)}
      {suffix}
    </span>
  );
};
