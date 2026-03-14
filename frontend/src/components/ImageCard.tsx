import type { SearchResult } from "@/lib/types";

export default function ImageCard({ result }: { result: SearchResult }) {
  return (
    <div className="mt-2">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={result.storage_key}
        alt={result.text_preview ?? "Financial chart"}
        className="aspect-video w-full rounded border border-card-border object-cover"
        loading="lazy"
      />
      <p className="mt-1.5 font-mono text-xs text-muted">
        {result.source_type}
      </p>
    </div>
  );
}
