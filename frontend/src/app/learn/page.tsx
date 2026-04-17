"use client";

import { useCallback, useState } from "react";
import { explainSentiment } from "@/lib/api";
import type { SentimentExplainResponse } from "@/lib/types";
import PipelineDiagram from "@/components/PipelineDiagram";
import ShapHighlight from "@/components/ShapHighlight";
import ShapBarChart from "@/components/ShapBarChart";
import ShapWaterfall from "@/components/ShapWaterfall";
import { MODALITY_COLORS, type Modality } from "@/lib/types";

const EXAMPLE_SENTENCES = [
  "Apple reported record quarterly revenue of $124 billion",
  "The company warned of significant headwinds in the coming quarter",
  "Market conditions remain uncertain amid mixed economic signals",
];

const MODALITY_INFO: {
  modality: Modality;
  title: string;
  description: string;
  dataType: string;
}[] = [
  {
    modality: "text",
    title: "News & Articles",
    description:
      "Financial news articles capture market reactions, analyst opinions, and event summaries. Text embeddings excel at capturing semantic nuance -- 'revenue beat expectations' and 'earnings topped estimates' are close in vector space despite sharing few words.",
    dataType: "Text chunks (512-word sliding window, 128-word overlap)",
  },
  {
    modality: "audio",
    title: "Earnings Calls",
    description:
      "Earnings call audio captures tone, emphasis, and nuance that transcripts miss. Gemini Embedding 2 natively embeds audio -- no transcription needed -- preserving vocal cues that correlate with management confidence.",
    dataType: "Audio segments (60s with 10s overlap, MP4 format)",
  },
  {
    modality: "pdf",
    title: "SEC Filings",
    description:
      "10-K and 10-Q filings contain structured financial data, risk factors, and management discussion. PDF embedding captures both text and layout, preserving table structures and section relationships.",
    dataType: "PDF chunks (up to 6 pages per chunk)",
  },
  {
    modality: "image",
    title: "Financial Charts",
    description:
      "Candlestick charts, volume bars, and technical indicators encode price action visually. Image embeddings capture visual patterns -- a head-and-shoulders formation is recognized as a pattern, not just pixels.",
    dataType: "Single image per chunk (PNG/JPEG)",
  },
];

export default function LearnPage() {
  const [demoText, setDemoText] = useState(EXAMPLE_SENTENCES[0]);
  const [demoResult, setDemoResult] =
    useState<SentimentExplainResponse | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);

  const runDemo = useCallback(async () => {
    if (!demoText.trim()) {
      setDemoError("Please enter some text to analyze");
      return;
    }
    setDemoLoading(true);
    setDemoError(null);
    try {
      const result = await explainSentiment(demoText);
      setDemoResult(result);
    } catch {
      setDemoError("Analysis failed. Make sure the backend is running.");
    } finally {
      setDemoLoading(false);
    }
  }, [demoText]);

  return (
    <div className="space-y-16">
      <div className="text-center">
        <h1 className="font-mono text-2xl font-bold tracking-tight">
          How FinRAG Works
        </h1>
        <p className="mt-2 text-sm text-muted">
          An educational companion to the capstone project at{" "}
          <a
            href="https://www.market-sentiment.io"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            market-sentiment.io
          </a>
        </p>
      </div>

      <section>
        <h2 className="font-mono text-lg font-semibold">What is RAG?</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          <strong className="text-foreground">
            Retrieval-Augmented Generation (RAG)
          </strong>{" "}
          is a technique that combines search with AI. Instead of relying solely
          on a model&apos;s training data, RAG retrieves relevant documents
          first, then uses them to inform responses. In financial research, this
          means searching across earnings calls, SEC filings, charts, and news
          -- using semantic understanding, not just keywords.
        </p>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Traditional keyword search fails for finance: &ldquo;revenue beat
          expectations&rdquo; and &ldquo;earnings topped estimates&rdquo; mean
          the same thing but share almost no words. Embedding-based search
          captures this semantic similarity. Click each stage below to see how:
        </p>
        <div className="mt-6">
          <PipelineDiagram />
        </div>
      </section>

      <section>
        <h2 className="font-mono text-lg font-semibold">
          How Sentiment Analysis Works
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          <strong className="text-foreground">FinBERT</strong> is a language
          model fine-tuned specifically for financial text. It classifies text as
          positive, negative, or neutral. But knowing the label isn&apos;t
          enough -- we need to understand <em>why</em>.
        </p>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          <strong className="text-foreground">
            SHAP (SHapley Additive exPlanations)
          </strong>{" "}
          uses game theory to attribute the prediction to individual tokens. Each
          token gets a SHAP value showing how much it pushed the prediction
          toward or away from a given class. This is critical for trust in
          financial AI -- you need to know if the model is responding to
          meaningful signals or noise.
        </p>

        <div className="mt-6 rounded-lg border border-card-border bg-card p-4">
          <p className="font-mono text-xs text-muted uppercase">
            Interactive Demo
          </p>
          <p className="mt-1 text-xs text-muted">
            Type or paste any financial sentence and see how FinBERT classifies
            it, with SHAP explanations showing which words drove the prediction.
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {EXAMPLE_SENTENCES.map((sentence, i) => (
              <button
                key={i}
                onClick={() => {
                  setDemoText(sentence);
                  setDemoResult(null);
                }}
                className={`rounded-full border px-2 py-0.5 font-mono text-[10px] transition-colors ${
                  demoText === sentence
                    ? "border-accent text-accent"
                    : "border-card-border text-muted hover:border-accent/30"
                }`}
              >
                Example {i + 1}
              </button>
            ))}
          </div>

          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={demoText}
              onChange={(e) => {
                setDemoText(e.target.value);
                setDemoResult(null);
              }}
              className="flex-1 rounded-md border border-card-border bg-background px-3 py-2 font-mono text-xs text-foreground placeholder:text-muted/50 focus:border-accent focus:outline-none"
              placeholder="Enter a financial sentence..."
            />
            <button
              onClick={runDemo}
              disabled={demoLoading}
              className="rounded-md bg-accent px-4 py-2 font-mono text-xs font-semibold text-background hover:bg-accent/90 disabled:opacity-50"
            >
              {demoLoading ? "Analyzing..." : "Analyze"}
            </button>
          </div>

          {demoError && (
            <p className="mt-2 font-mono text-xs text-score-low">
              {demoError}
            </p>
          )}

          {demoResult && (
            <div className="mt-4 space-y-4">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs text-muted">
                  Prediction:
                </span>
                <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-mono text-sm font-semibold text-accent">
                  {demoResult.label} (
                  {(demoResult.confidence * 100).toFixed(0)}%)
                </span>
              </div>

              <div className="flex gap-4">
                {Object.entries(demoResult.probabilities).map(
                  ([label, prob]) => (
                    <div key={label} className="text-center">
                      <div className="font-mono text-lg font-bold text-foreground">
                        {(prob * 100).toFixed(0)}%
                      </div>
                      <div className="font-mono text-[10px] text-muted">
                        {label}
                      </div>
                    </div>
                  )
                )}
              </div>

              <div>
                <p className="mb-1 font-mono text-[10px] uppercase text-muted">
                  Token Attribution (highlighted text)
                </p>
                <p className="mb-1 text-[10px] text-muted">
                  Green = pushes toward {demoResult.label}, Red = pushes away.
                  Darker = stronger effect.
                </p>
                <ShapHighlight tokens={demoResult.shap_values} />
              </div>

              <div>
                <p className="mb-1 font-mono text-[10px] uppercase text-muted">
                  Top Feature Contributions (bar chart)
                </p>
                <ShapBarChart tokens={demoResult.shap_values} topN={10} />
              </div>

              <div>
                <p className="mb-1 font-mono text-[10px] uppercase text-muted">
                  Waterfall Plot
                </p>
                <p className="mb-1 text-[10px] text-muted">
                  Shows how each token pushes the prediction from the base value
                  ({(demoResult.base_value * 100).toFixed(0)}% for a 3-class
                  model) to the final prediction (
                  {(demoResult.confidence * 100).toFixed(0)}%).
                </p>
                <ShapWaterfall
                  tokens={demoResult.shap_values}
                  baseValue={demoResult.base_value}
                  prediction={demoResult.confidence}
                  topN={10}
                />
              </div>
            </div>
          )}
        </div>
      </section>

      <section>
        <h2 className="font-mono text-lg font-semibold">Why Multimodal?</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Financial events produce data across multiple formats. An earnings
          report generates an audio recording (the call), a PDF filing (the
          10-K), news articles (analyst reactions), and chart movements (price
          action). Analyzing only one modality means missing context from the
          others. FinRAG embeds all four using a single model, enabling
          cross-modal search.
        </p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {MODALITY_INFO.map((info) => (
            <div
              key={info.modality}
              className="rounded-lg border border-card-border p-4"
            >
              <span
                className={`inline-block rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase ${MODALITY_COLORS[info.modality]}`}
              >
                {info.modality}
              </span>
              <h3 className="mt-2 font-mono text-sm font-semibold">
                {info.title}
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                {info.description}
              </p>
              <p className="mt-2 font-mono text-[10px] text-accent/70">
                {info.dataType}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="border-t border-card-border pt-8 text-center">
        <p className="text-sm text-muted">
          This project is the companion application to the capstone research at{" "}
          <a
            href="https://www.market-sentiment.io"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            market-sentiment.io
          </a>
        </p>
      </div>
    </div>
  );
}
