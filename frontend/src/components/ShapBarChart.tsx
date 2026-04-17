"use client";

import type { ShapToken } from "@/lib/types";

export default function ShapBarChart({
  tokens,
  topN = 10,
}: {
  tokens: ShapToken[];
  topN?: number;
}) {
  const sorted = [...tokens]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, topN);

  const maxAbsValue = Math.max(...sorted.map((t) => Math.abs(t.value)), 0.001);

  return (
    <div className="space-y-1.5">
      {sorted.map((token, i) => {
        const widthPct = Math.round((Math.abs(token.value) / maxAbsValue) * 100);
        const isPositive = token.value >= 0;

        return (
          <div key={i} className="flex items-center gap-2">
            <span className="w-20 truncate text-right font-mono text-[10px] text-muted">
              {token.token}
            </span>
            <div className="flex-1">
              <div
                className={`h-3 rounded-sm ${isPositive ? "bg-shap-positive/60" : "bg-shap-negative/60"}`}
                style={{ width: `${Math.max(widthPct, 2)}%` }}
              />
            </div>
            <span className="w-14 font-mono text-[10px] text-muted">
              {token.value > 0 ? "+" : ""}
              {token.value.toFixed(3)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
