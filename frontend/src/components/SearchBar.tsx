"use client";

interface SearchBarProps {
  defaultValue?: string;
  loading?: boolean;
  onSearch: (query: string) => void;
}

export default function SearchBar({
  defaultValue = "",
  loading = false,
  onSearch,
}: SearchBarProps) {
  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const query = (form.get("query") as string).trim();
    if (query) onSearch(query);
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        name="query"
        type="text"
        defaultValue={defaultValue}
        placeholder="Search across earnings calls, filings, charts, and news..."
        disabled={loading}
        className="w-full rounded-lg border border-card-border bg-card px-4 py-3 pr-12 font-mono text-sm text-foreground placeholder:text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={loading}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-2 text-muted transition-colors hover:text-accent disabled:opacity-50"
        aria-label="Search"
      >
        {loading ? (
          <svg
            className="h-4 w-4 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="3"
              className="opacity-25"
            />
            <path
              d="M4 12a8 8 0 018-8"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        )}
      </button>
    </form>
  );
}
