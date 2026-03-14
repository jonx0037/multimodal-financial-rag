"use client";

import { useRouter } from "next/navigation";
import type { SearchResult, Modality } from "@/lib/types";
import { MODALITY_COLORS } from "@/lib/types";
import TextCard from "./TextCard";
import AudioCard from "./AudioCard";
import PDFCard from "./PDFCard";
import ImageCard from "./ImageCard";

function scoreColor(score: number): string {
  if (score >= 0.8) return "text-score-high";
  if (score >= 0.6) return "text-score-mid";
  return "text-score-low";
}

const CARD_COMPONENTS: Record<string, React.ComponentType<{ result: SearchResult }>> = {
  text: TextCard,
  audio: AudioCard,
  pdf: PDFCard,
  image: ImageCard,
};

export default function ResultCard({ result }: { result: SearchResult }) {
  const router = useRouter();
  const CardContent = CARD_COMPONENTS[result.modality] ?? TextCard;
  const badgeClass = MODALITY_COLORS[result.modality as Modality] ?? MODALITY_COLORS.text;

  function handleClick() {
    sessionStorage.setItem(`doc-${result.id}`, JSON.stringify(result));
    router.push(`/doc/${result.id}`);
  }

  return (
    <button
      onClick={handleClick}
      className="group w-full rounded-lg border border-card-border bg-card p-4 text-left transition-all hover:border-accent/30 hover:shadow-[0_0_20px_rgba(0,212,170,0.05)]"
    >
      <div className="flex items-start justify-between gap-2">
        <span
          className={`rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase ${badgeClass}`}
        >
          {result.modality}
        </span>
        <span className={`font-mono text-xs font-semibold ${scoreColor(result.score)}`}>
          {result.score.toFixed(3)}
        </span>
      </div>

      <CardContent result={result} />

      <div className="mt-3 flex items-center gap-2 text-[10px] text-muted">
        {result.ticker && (
          <span className="font-mono font-semibold">{result.ticker}</span>
        )}
        {result.ticker && result.date && <span>·</span>}
        {result.date && <span className="font-mono">{result.date}</span>}
      </div>
    </button>
  );
}
