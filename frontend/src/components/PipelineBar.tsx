"use client";

import { useCallback, useState } from "react";
import { getPipelineStages } from "@/lib/api";
import type { PipelineStage } from "@/lib/types";

export default function PipelineBar() {
  const [open, setOpen] = useState(false);
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [animated, setAnimated] = useState(false);

  const loadStages = useCallback(async () => {
    if (stages.length > 0) {
      setOpen((o) => !o);
      return;
    }
    try {
      const data = await getPipelineStages();
      setStages(data);
      setOpen(true);
      for (let i = 0; i < data.length; i++) {
        await new Promise((r) => setTimeout(r, 200));
        setActiveStep(i);
      }
      setAnimated(true);
    } catch {
      // Silently fail -- pipeline is educational, not critical
    }
  }, [stages]);

  return (
    <div className="mb-4 rounded-lg border border-card-border bg-card">
      <button
        onClick={loadStages}
        className="flex w-full items-center justify-between px-4 py-2 font-mono text-xs text-muted hover:text-foreground transition-colors"
      >
        <span>&#9881; See how this search works</span>
        <span className="text-[10px]">{open ? "&#9650;" : "&#9660;"}</span>
      </button>

      {open && stages.length > 0 && (
        <div className="border-t border-card-border px-4 py-3">
          <div className="flex items-center gap-1 overflow-x-auto pb-3">
            {stages.map((stage, i) => {
              const isActive = animated || (activeStep !== null && i <= activeStep);
              return (
                <div key={stage.step} className="flex items-center">
                  <button
                    onClick={() => setActiveStep(i)}
                    className={`whitespace-nowrap rounded-full border px-2.5 py-1 font-mono text-[10px] transition-all ${
                      activeStep === i
                        ? "border-accent bg-accent/10 text-accent"
                        : isActive
                          ? "border-card-border text-foreground/70"
                          : "border-transparent text-muted/40"
                    }`}
                  >
                    {stage.name}
                  </button>
                  {i < stages.length - 1 && (
                    <span className={`mx-0.5 font-mono text-[10px] ${isActive ? "text-accent/50" : "text-muted/20"}`}>
                      &rarr;
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {activeStep !== null && stages[activeStep] && (
            <div className="rounded-md border border-card-border bg-background p-3">
              <p className="font-mono text-xs font-semibold text-foreground">
                Step {stages[activeStep].step}: {stages[activeStep].name}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                {stages[activeStep].description}
              </p>
              {stages[activeStep].details && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(stages[activeStep].details!).map(([key, val]) => (
                    <span
                      key={key}
                      className="rounded bg-accent/5 px-1.5 py-0.5 font-mono text-[10px] text-accent/70"
                    >
                      {key}: {typeof val === "object" ? JSON.stringify(val) : String(val)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
