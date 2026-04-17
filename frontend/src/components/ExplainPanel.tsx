"use client";

import { useCallback, useState } from "react";
import { explainSentiment, explainRetrieval } from "@/lib/api";
import type { SentimentExplainResponse, ResultExplanation } from "@/lib/types";
import ShapHighlight from "./ShapHighlight";
import ShapBarChart from "./ShapBarChart";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "bg-shap-positive/20 text-shap-positive border-shap-positive/30",
  negative: "bg-shap-negative/20 text-shap-negative border-shap-negative/30",
  neutral: "bg-shap-neutral/20 text-shap-neutral border-shap-neutral/30",
};

export default function ExplainPanel({
  textPreview,
  resultId,
  query,
  score,
}: {
  textPreview: string | undefined;
  resultId: string;
  query: string;
  score: number;
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sentiment, setSentiment] = useState<SentimentExplainResponse | null>(null);
  const [retrieval, setRetrieval] = useState<ResultExplanation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExplain = useCallback(async () => {
    if (open) {
      setOpen(false);
      return;
    }

    if (sentiment) {
      setOpen(true);
      return;
    }

    setLoading(true);
    setError(null);
    setOpen(true);

    try {
      const results = await Promise.allSettled([
        textPreview ? explainSentiment(textPreview) : Promise.resolve(null),
        explainRetrieval(query, [resultId]),
      ]);

      const sentimentData =
        results[0].status === "fulfilled" ? results[0].value : null;

      let retrievalMatch: ResultExplanation | null = null;
      if (results[1].status === "fulfilled") {
        const retrievalData = results[1].value;
        retrievalMatch =
          retrievalData.results.find((r) => r.id === resultId) ?? null;
      }

      if (sentimentData) setSentiment(sentimentData);
      if (retrievalMatch) setRetrieval(retrievalMatch);

      if (!sentimentData && !retrievalMatch) {
        setError("Explanation unavailable");
      }
    } catch {
      setError("Explanation unavailable");
    } finally {
      setLoading(false);
    }
  }, [open, sentiment, textPreview, resultId, query]);

  return (
    <div className="mt-3">
      <button
        onClick={handleExplain}
        className="font-mono text-[10px] text-accent hover:text-accent/80 transition-colors"
      >
        {loading ? "Analyzing..." : open ? "Hide Explanation" : "Explain"}
      </button>

      {open && !loading && (
        <div className="mt-2 space-y-3 border-t border-card-border pt-3">
          {error && (
            <p className="font-mono text-xs text-score-low">{error}</p>
          )}

          {sentiment && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-muted uppercase">Sentiment</span>
                <span
                  className={`rounded-full border px-2 py-0.5 font-mono text-[10px] ${
                    SENTIMENT_COLORS[sentiment.label] ?? SENTIMENT_COLORS.neutral
                  }`}
                >
                  {sentiment.label} ({(sentiment.confidence * 100).toFixed(0)}%)
                </span>
              </div>
              <ShapHighlight tokens={sentiment.shap_values} />
              <ShapBarChart tokens={sentiment.shap_values} topN={8} />
            </div>
          )}

          {retrieval && (
            <div className="space-y-1.5">
              <span className="font-mono text-[10px] text-muted uppercase">Retrieval</span>
              <p className="font-mono text-[10px] text-muted">
                {retrieval.similarity_method} &middot; score: {score.toFixed(3)}
              </p>
              <div className="space-y-1">
                {retrieval.query_terms_contribution.map((c, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="w-24 truncate text-right font-mono text-[10px] text-muted">
                      &ldquo;{c.term}&rdquo;
                    </span>
                    <div className="flex-1">
                      <div
                        className="h-2 rounded-sm bg-accent-secondary/50"
                        style={{ width: `${Math.max(Math.abs(c.weight) * 100, 2)}%` }}
                      />
                    </div>
                    <span className="w-12 font-mono text-[10px] text-muted">
                      {(c.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
