import type { SearchRequest, SearchResult } from "./types";

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
