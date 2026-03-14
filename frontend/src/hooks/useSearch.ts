"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { searchDocuments } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

export function useSearch() {
  const searchParams = useSearchParams();
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const query = searchParams.get("q") ?? "";
  const modalities = searchParams.get("modalities")?.split(",").filter(Boolean);
  const tickers = searchParams.get("tickers")?.split(",").filter(Boolean);
  const dateAfter = searchParams.get("date_after") ?? undefined;
  const dateBefore = searchParams.get("date_before") ?? undefined;
  const useCompact = searchParams.get("compact") === "true";
  const limit = parseInt(searchParams.get("limit") ?? "12", 10);

  const executeSearch = useCallback(async () => {
    if (!query) return;

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const data = await searchDocuments({
        query,
        modalities: modalities?.length ? modalities : undefined,
        tickers: tickers?.length ? tickers : undefined,
        date_after: dateAfter,
        date_before: dateBefore,
        use_compact: useCompact,
        limit,
      });
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, modalities?.join(","), tickers?.join(","), dateAfter, dateBefore, useCompact, limit]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  return { results, loading, error, hasSearched, query };
}
