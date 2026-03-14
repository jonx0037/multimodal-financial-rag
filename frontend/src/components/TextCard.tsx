import type { SearchResult } from "@/lib/types";

export default function TextCard({ result }: { result: SearchResult }) {
  return (
    <div className="mt-2">
      <p className="line-clamp-3 text-sm leading-relaxed text-foreground/80">
        {result.text_preview ?? "No preview available"}
      </p>
      <p className="mt-2 font-mono text-xs text-muted">
        {result.source_type}
      </p>
    </div>
  );
}
