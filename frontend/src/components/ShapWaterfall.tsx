"use client";

import type { ShapToken } from "@/lib/types";

export default function ShapWaterfall({
  tokens,
  baseValue,
  prediction,
  topN = 10,
}: {
  tokens: ShapToken[];
  baseValue: number;
  prediction: number;
  topN?: number;
}) {
  const sorted = [...tokens]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, topN);

  let cumulative = baseValue;
  const bars = sorted.map((token) => {
    const start = cumulative;
    cumulative += token.value;
    return { token: token.token, value: token.value, start, end: cumulative };
  });

  const allValues = [
    baseValue,
    prediction,
    ...bars.map((b) => b.start),
    ...bars.map((b) => b.end),
  ];
  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const range = maxVal - minVal || 0.01;

  function toPct(val: number) {
    return ((val - minVal) / range) * 100;
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="w-20 text-right font-mono text-[10px] text-muted">base</span>
        <div className="relative flex-1 h-4">
          <div className="absolute h-4 w-0.5 bg-muted/50" style={{ left: `${toPct(baseValue)}%` }} />
          <span className="absolute top-0 font-mono text-[9px] text-muted" style={{ left: `${toPct(baseValue)}%`, transform: "translateX(-50%)" }}>
            {baseValue.toFixed(3)}
          </span>
        </div>
      </div>

      {bars.map((bar, i) => {
        const left = toPct(Math.min(bar.start, bar.end));
        const width = Math.abs(toPct(bar.end) - toPct(bar.start));
        const isPositive = bar.value >= 0;

        return (
          <div key={i} className="flex items-center gap-2">
            <span className="w-20 truncate text-right font-mono text-[10px] text-muted">{bar.token}</span>
            <div className="relative flex-1 h-4">
              <div
                className={`absolute h-4 rounded-sm ${isPositive ? "bg-shap-positive/60" : "bg-shap-negative/60"}`}
                style={{ left: `${left}%`, width: `${Math.max(width, 0.5)}%` }}
              />
              <div className="absolute h-4 w-px bg-muted/30" style={{ left: `${toPct(bar.start)}%` }} />
            </div>
            <span className="w-14 font-mono text-[10px] text-muted">
              {bar.value > 0 ? "+" : ""}{bar.value.toFixed(3)}
            </span>
          </div>
        );
      })}

      <div className="flex items-center gap-2">
        <span className="w-20 text-right font-mono text-[10px] font-semibold text-foreground">f(x)</span>
        <div className="relative flex-1 h-4">
          <div className="absolute h-4 w-0.5 bg-accent" style={{ left: `${toPct(prediction)}%` }} />
          <span className="absolute top-0 font-mono text-[9px] font-semibold text-accent" style={{ left: `${toPct(prediction)}%`, transform: "translateX(-50%)" }}>
            {prediction.toFixed(3)}
          </span>
        </div>
      </div>
    </div>
  );
}
