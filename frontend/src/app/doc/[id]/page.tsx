"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { SearchResult, Modality } from "@/lib/types";
import { MODALITY_COLORS } from "@/lib/types";

function scoreColor(score: number): string {
  if (score >= 0.8) return "text-score-high";
  if (score >= 0.6) return "text-score-mid";
  return "text-score-low";
}

function DocumentContent({ result }: { result: SearchResult }) {
  switch (result.modality) {
    case "text":
      return (
        <div className="rounded-lg border border-card-border bg-card p-6">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
            {result.text_preview ?? "Full text content would load from storage."}
          </p>
        </div>
      );
    case "audio":
      return (
        <div className="rounded-lg border border-card-border bg-card p-6">
          <p className="mb-4 font-mono text-xs text-muted">Earnings call segment</p>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio controls className="w-full" src={result.storage_key} />
        </div>
      );
    case "pdf":
      return (
        <div className="overflow-hidden rounded-lg border border-card-border">
          <object
            data={result.storage_key}
            type="application/pdf"
            className="h-[70vh] w-full"
          >
            <div className="flex h-[70vh] items-center justify-center bg-card">
              <a
                href={result.storage_key}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-sm text-accent hover:underline"
              >
                Open PDF in new tab →
              </a>
            </div>
          </object>
        </div>
      );
    case "image":
      return (
        <div className="flex justify-center rounded-lg border border-card-border bg-card p-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={result.storage_key}
            alt={result.text_preview ?? "Financial chart"}
            className="max-h-[70vh] rounded object-contain"
          />
        </div>
      );
    default:
      return (
        <div className="rounded-lg border border-card-border bg-card p-6">
          <p className="text-sm text-muted">Unknown modality: {result.modality}</p>
        </div>
      );
  }
}

export default function DocumentViewer() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [result, setResult] = useState<SearchResult | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem(`doc-${params.id}`);
    if (stored) {
      setResult(JSON.parse(stored));
    }
  }, [params.id]);

  if (!result) {
    return (
      <div className="py-20 text-center">
        <p className="font-mono text-sm text-muted">
          Document not found. Try searching again.
        </p>
        <button
          onClick={() => router.push("/")}
          className="mt-4 font-mono text-sm text-accent hover:underline"
        >
          ← Back to search
        </button>
      </div>
    );
  }

  const badgeClass =
    MODALITY_COLORS[result.modality as Modality] ?? MODALITY_COLORS.text;

  return (
    <div>
      <button
        onClick={() => router.back()}
        className="mb-6 font-mono text-sm text-muted transition-colors hover:text-foreground"
      >
        ← back to results
      </button>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <span
          className={`rounded-full border px-3 py-1 font-mono text-xs uppercase ${badgeClass}`}
        >
          {result.modality}
        </span>
        <span className={`font-mono text-sm font-semibold ${scoreColor(result.score)}`}>
          {result.score.toFixed(4)}
        </span>
        {result.ticker && (
          <span className="font-mono text-sm font-bold text-foreground">
            {result.ticker}
          </span>
        )}
        {result.date && (
          <span className="font-mono text-sm text-muted">{result.date}</span>
        )}
        <span className="font-mono text-xs text-muted">
          {result.source_type}
        </span>
      </div>

      <DocumentContent result={result} />
    </div>
  );
}
