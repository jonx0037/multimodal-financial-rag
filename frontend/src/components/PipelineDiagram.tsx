"use client";

import { useState } from "react";

interface DiagramNode {
  id: string;
  label: string;
  description: string;
  example: string;
}

const NODES: DiagramNode[] = [
  {
    id: "raw",
    label: "Raw Data",
    description:
      "Financial data comes in four modalities: earnings call audio, SEC filing PDFs, stock chart images, and news articles.",
    example:
      "An Apple Q4 2024 earnings call is a 45-minute audio file. A 10-K filing is a 200-page PDF. A candlestick chart is a PNG image.",
  },
  {
    id: "chunk",
    label: "Chunking",
    description:
      "Each document is split into smaller pieces so embeddings capture focused meaning. Strategy varies by modality.",
    example:
      "Text: 512-word sliding window with 128-word overlap. Audio: 60-second segments with 10-second overlap. PDF: up to 6 pages. Images: single chunk.",
  },
  {
    id: "embed",
    label: "Embedding",
    description:
      "Each chunk is converted into a dense vector (a list of numbers) using Google Gemini Embedding 2. This model handles all four modalities natively.",
    example:
      "The sentence 'Apple beat earnings expectations' becomes a 3072-dimensional vector like [0.023, -0.117, 0.891, ...]. Similar sentences produce similar vectors.",
  },
  {
    id: "store",
    label: "Vector Store",
    description:
      "Vectors are stored in Qdrant, a vector database optimized for fast similarity search. Each vector is stored with metadata (ticker, date, modality).",
    example:
      "Every chunk gets both a 3072-dim (full) and 768-dim (compact) vector. The compact version trades accuracy for speed.",
  },
  {
    id: "query",
    label: "Query",
    description:
      "When you search, your query text is embedded using the same model, producing a vector in the same space as the documents.",
    example:
      "'Apple earnings growth' becomes a query vector. Because it was embedded by the same model, it lives in the same mathematical space as the document vectors.",
  },
  {
    id: "retrieve",
    label: "Retrieval",
    description:
      "The query vector is compared against all document vectors using cosine similarity. The closest vectors -- meaning the most semantically similar documents -- are returned.",
    example:
      "Cosine similarity measures the angle between two vectors. A score of 1.0 means identical direction (perfect match), 0.0 means orthogonal (unrelated).",
  },
  {
    id: "results",
    label: "Results",
    description:
      "Results are balanced across modalities, ranked by score, and returned with presigned URLs for accessing the original files.",
    example:
      "A search for 'Apple revenue' might return: a news article (text), an earnings call segment (audio), a 10-K excerpt (PDF), and a revenue chart (image).",
  },
];

export default function PipelineDiagram() {
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const active = NODES.find((n) => n.id === activeNode);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {NODES.map((node, i) => (
          <div key={node.id} className="flex items-center">
            <button
              onClick={() =>
                setActiveNode(activeNode === node.id ? null : node.id)
              }
              className={`rounded-lg border px-3 py-2 font-mono text-xs transition-all ${
                activeNode === node.id
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-card-border text-muted hover:border-accent/30 hover:text-foreground"
              }`}
            >
              {node.label}
            </button>
            {i < NODES.length - 1 && (
              <span className="mx-1 font-mono text-muted/30">&rarr;</span>
            )}
          </div>
        ))}
      </div>

      {active && (
        <div className="mt-4 rounded-lg border border-accent/20 bg-accent/5 p-4">
          <h4 className="font-mono text-sm font-semibold text-accent">
            {active.label}
          </h4>
          <p className="mt-1 text-sm leading-relaxed text-foreground/80">
            {active.description}
          </p>
          <div className="mt-3 rounded-md bg-card p-3">
            <p className="font-mono text-[10px] uppercase text-muted">Example</p>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              {active.example}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
