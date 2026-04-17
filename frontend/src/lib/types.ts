export interface SearchRequest {
  query: string;
  modalities?: string[];
  tickers?: string[];
  date_after?: string;
  date_before?: string;
  limit?: number;
  use_compact?: boolean;
}

export interface SearchResult {
  id: string;
  score: number;
  modality: string;
  source_type: string;
  ticker?: string;
  date?: string;
  text_preview?: string;
  storage_key: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  qdrant_connected: boolean;
  postgres_connected: boolean;
}

export type Modality = "text" | "audio" | "pdf" | "image";

export const MODALITIES: Modality[] = ["text", "audio", "pdf", "image"];

export const MODALITY_COLORS: Record<Modality, string> = {
  text: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  audio: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  pdf: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  image: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

export const MODALITY_COLORS_LIGHT: Record<Modality, string> = {
  text: "bg-emerald-100 text-emerald-700 border-emerald-200",
  audio: "bg-violet-100 text-violet-700 border-violet-200",
  pdf: "bg-rose-100 text-rose-700 border-rose-200",
  image: "bg-amber-100 text-amber-700 border-amber-200",
};

// --- Explainability types ---

export interface ShapToken {
  token: string;
  value: number;
}

export interface SentimentExplainResponse {
  label: string;
  confidence: number;
  probabilities: Record<string, number>;
  shap_values: ShapToken[];
  base_value: number;
}

export interface QueryTermContribution {
  term: string;
  weight: number;
}

export interface ResultExplanation {
  id: string;
  score: number;
  query_terms_contribution: QueryTermContribution[];
  modality: string;
  similarity_method: string;
}

export interface RetrievalExplainResponse {
  results: ResultExplanation[];
}

export interface PipelineStage {
  step: number;
  name: string;
  description: string;
  details?: Record<string, unknown>;
}
