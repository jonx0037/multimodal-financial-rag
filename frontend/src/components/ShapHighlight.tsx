"use client";

import type { CSSProperties } from "react";
import type { ShapToken } from "@/lib/types";

function tokenStyle(value: number, maxAbsValue: number): CSSProperties {
  if (maxAbsValue === 0) return {};
  const intensity = Math.min(Math.abs(value) / maxAbsValue, 1);
  const alpha = intensity * 0.4 + 0.05; // 5-45% opacity
  const cssVar =
    value > 0
      ? "var(--shap-positive)"
      : value < 0
        ? "var(--shap-negative)"
        : "transparent";
  return {
    backgroundColor: `color-mix(in srgb, ${cssVar} ${Math.round(alpha * 100)}%, transparent)`,
  };
}

export default function ShapHighlight({ tokens }: { tokens: ShapToken[] }) {
  const maxAbsValue = Math.max(...tokens.map((t) => Math.abs(t.value)), 0.001);

  return (
    <div className="flex flex-wrap gap-0.5 rounded-md border border-card-border bg-card p-3">
      {tokens.map((token, i) => (
        <span
          key={i}
          className="inline-block rounded px-0.5 font-mono text-xs"
          style={tokenStyle(token.value, maxAbsValue)}
          title={`${token.token}: ${token.value > 0 ? "+" : ""}${token.value.toFixed(4)}`}
        >
          {token.token}
        </span>
      ))}
    </div>
  );
}
