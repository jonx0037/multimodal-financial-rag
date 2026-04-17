import type { SearchRequest, SearchResult, SentimentExplainResponse, RetrievalExplainResponse, PipelineStage } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function searchDocuments(
  params: SearchRequest
): Promise<SearchResult[]> {
  const res = await fetch(`${API_URL}/api/search/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    throw new Error(`Search failed: ${res.status}`);
  }
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return res.json();
}

export async function explainSentiment(
  text: string
): Promise<SentimentExplainResponse> {
  const res = await fetch(`${API_URL}/api/explain/sentiment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`Sentiment explanation failed: ${res.status}`);
  }
  return res.json();
}

export async function explainRetrieval(
  query: string,
  resultIds: string[]
): Promise<RetrievalExplainResponse> {
  const res = await fetch(`${API_URL}/api/explain/retrieval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, result_ids: resultIds }),
  });
  if (!res.ok) {
    throw new Error(`Retrieval explanation failed: ${res.status}`);
  }
  return res.json();
}

export async function getPipelineStages(): Promise<PipelineStage[]> {
  const res = await fetch(`${API_URL}/api/explain/pipeline`);
  if (!res.ok) {
    throw new Error(`Pipeline fetch failed: ${res.status}`);
  }
  return res.json();
}
