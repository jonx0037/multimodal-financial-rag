"use client";

import { useState } from "react";
import {
  MODALITIES,
  MODALITY_COLORS,
  type Modality,
} from "@/lib/types";

interface FilterBarProps {
  modalities: Modality[];
  ticker: string;
  dateAfter: string;
  dateBefore: string;
  useCompact: boolean;
  onModalitiesChange: (modalities: Modality[]) => void;
  onTickerChange: (ticker: string) => void;
  onDateAfterChange: (date: string) => void;
  onDateBeforeChange: (date: string) => void;
  onCompactChange: (compact: boolean) => void;
}

export default function FilterBar({
  modalities,
  ticker,
  dateAfter,
  dateBefore,
  useCompact,
  onModalitiesChange,
  onTickerChange,
  onDateAfterChange,
  onDateBeforeChange,
  onCompactChange,
}: FilterBarProps) {
  const [open, setOpen] = useState(false);

  function toggleModality(m: Modality) {
    if (modalities.includes(m)) {
      if (modalities.length > 1) {
        onModalitiesChange(modalities.filter((x) => x !== m));
      }
    } else {
      onModalitiesChange([...modalities, m]);
    }
  }

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="font-mono text-xs text-muted transition-colors hover:text-foreground md:hidden"
      >
        {open ? "▾ Hide filters" : "▸ Filters"}
      </button>

      <div className={`${open ? "block" : "hidden"} md:block`}>
        <div className="flex flex-wrap items-center gap-3 pt-2 md:pt-0">
          {/* Modality toggles */}
          <div className="flex gap-1.5">
            {MODALITIES.map((m) => {
              const active = modalities.includes(m);
              return (
                <button
                  key={m}
                  onClick={() => toggleModality(m)}
                  className={`rounded-full border px-3 py-1 font-mono text-xs capitalize transition-all ${
                    active
                      ? MODALITY_COLORS[m]
                      : "border-card-border text-muted opacity-40 hover:opacity-70"
                  }`}
                >
                  {m}
                </button>
              );
            })}
          </div>

          {/* Ticker input */}
          <input
            type="text"
            placeholder="TICKER"
            value={ticker}
            onChange={(e) => onTickerChange(e.target.value.toUpperCase())}
            className="w-24 rounded border border-card-border bg-card px-2 py-1 font-mono text-xs text-foreground placeholder:text-muted focus:border-accent focus:outline-none"
          />

          {/* Date range */}
          <div className="flex items-center gap-1.5">
            <input
              type="date"
              value={dateAfter}
              onChange={(e) => onDateAfterChange(e.target.value)}
              className="rounded border border-card-border bg-card px-2 py-1 font-mono text-xs text-foreground focus:border-accent focus:outline-none"
            />
            <span className="text-xs text-muted">→</span>
            <input
              type="date"
              value={dateBefore}
              onChange={(e) => onDateBeforeChange(e.target.value)}
              className="rounded border border-card-border bg-card px-2 py-1 font-mono text-xs text-foreground focus:border-accent focus:outline-none"
            />
          </div>

          {/* Compact toggle */}
          <label className="flex cursor-pointer items-center gap-1.5">
            <span className="font-mono text-xs text-muted">768-dim</span>
            <button
              role="switch"
              aria-checked={useCompact}
              onClick={() => onCompactChange(!useCompact)}
              className={`relative h-5 w-9 rounded-full transition-colors ${
                useCompact ? "bg-accent" : "bg-card-border"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-foreground transition-transform ${
                  useCompact ? "translate-x-4" : ""
                }`}
              />
            </button>
          </label>
        </div>
      </div>
    </div>
  );
}
