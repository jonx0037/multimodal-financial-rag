"use client";

import { Suspense, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import ResultCard from "@/components/ResultCard";
import { useSearch } from "@/hooks/useSearch";
import { MODALITIES, type Modality } from "@/lib/types";

function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { results, loading, error, hasSearched, query } = useSearch();

  const modalities = (
    searchParams.get("modalities")?.split(",").filter(Boolean) ?? [...MODALITIES]
  ) as Modality[];
  const ticker = searchParams.get("tickers") ?? "";
  const dateAfter = searchParams.get("date_after") ?? "";
  const dateBefore = searchParams.get("date_before") ?? "";
  const useCompact = searchParams.get("compact") === "true";

  const updateParams = useCallback(
    (updates: Record<string, string>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value) {
          params.set(key, value);
        } else {
          params.delete(key);
        }
      }
      router.push(`?${params.toString()}`);
    },
    [router, searchParams]
  );

  function handleSearch(q: string) {
    updateParams({ q });
  }

  return (
    <div>
      <div className="mb-8 text-center">
        <div className="mb-3 flex justify-center">
          <Image
            src="/images/finrag-logo.png"
            alt="FinRAG"
            width={72}
            height={72}
            className="rounded-xl"
          />
        </div>
        <h1 className="font-mono text-2xl font-bold tracking-tight">
          finrag.io
        </h1>
        <p className="mt-1 text-sm text-muted">
          Semantic search across earnings calls, SEC filings, charts, and news
        </p>
      </div>

      <SearchBar
        defaultValue={query}
        loading={loading}
        onSearch={handleSearch}
      />

      <FilterBar
        modalities={modalities}
        ticker={ticker}
        dateAfter={dateAfter}
        dateBefore={dateBefore}
        useCompact={useCompact}
        onModalitiesChange={(m) =>
          updateParams({ modalities: m.join(",") })
        }
        onTickerChange={(t) => updateParams({ tickers: t })}
        onDateAfterChange={(d) => updateParams({ date_after: d })}
        onDateBeforeChange={(d) => updateParams({ date_before: d })}
        onCompactChange={(c) =>
          updateParams({ compact: c ? "true" : "" })
        }
      />

      {/* Results */}
      <div className="mt-6">
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 font-mono text-sm text-red-400">
            {error}
          </div>
        )}

        {loading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-40 animate-pulse rounded-lg border border-card-border bg-card"
              />
            ))}
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {results.map((result) => (
              <ResultCard key={result.id} result={result} />
            ))}
          </div>
        )}

        {!loading && hasSearched && results.length === 0 && !error && (
          <div className="py-12 text-center">
            <p className="font-mono text-sm text-muted">
              No results found. Try adjusting your filters or query.
            </p>
          </div>
        )}

        {!hasSearched && !loading && (
          <div className="py-16 text-center">
            <p className="font-mono text-lg text-muted/50">
              ↑ Enter a query to search
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense>
      <SearchPage />
    </Suspense>
  );
}
