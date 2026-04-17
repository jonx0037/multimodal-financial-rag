"use client";

import type { ShapToken } from "@/lib/types";

function tokenColor(value: number, maxAbsValue: number): string {
  if (maxAbsValue === 0) return "bg-transparent";
  const intensity = Math.min(Math.abs(value) / maxAbsValue, 1);
  const alpha = Math.round(intensity * 40 + 5); // 5-45% opacity
  if (value > 0) return `bg-shap-positive/${alpha}`;
  if (value < 0) return `bg-shap-negative/${alpha}`;
  return "bg-transparent";
}

export default function ShapHighlight({ tokens }: { tokens: ShapToken[] }) {
  const maxAbsValue = Math.max(...tokens.map((t) => Math.abs(t.value)), 0.001);

  return (
    <div className="flex flex-wrap gap-0.5 rounded-md border border-card-border bg-card p-3">
      {tokens.map((token, i) => (
        <span
          key={i}
          className={`inline-block rounded px-0.5 font-mono text-xs ${tokenColor(token.value, maxAbsValue)}`}
          title={`${token.token}: ${token.value > 0 ? "+" : ""}${token.value.toFixed(4)}`}
        >
          {token.token}
        </span>
      ))}
    </div>
  );
}
