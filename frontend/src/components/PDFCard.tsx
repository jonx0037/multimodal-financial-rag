import type { SearchResult } from "@/lib/types";

export default function PDFCard({ result }: { result: SearchResult }) {
  return (
    <div className="mt-2 flex items-start gap-3">
      <div className="flex h-12 w-10 shrink-0 items-center justify-center rounded border border-card-border bg-rose-500/10 font-mono text-xs text-rose-400">
        PDF
      </div>
      <div className="min-w-0">
        <p className="font-mono text-xs text-muted">{result.source_type}</p>
        {result.text_preview && (
          <p className="mt-1 line-clamp-2 text-xs text-foreground/60">
            {result.text_preview}
          </p>
        )}
      </div>
    </div>
  );
}
