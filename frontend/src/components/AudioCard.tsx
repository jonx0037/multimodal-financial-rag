import type { SearchResult } from "@/lib/types";

export default function AudioCard({ result }: { result: SearchResult }) {
  return (
    <div className="mt-2 space-y-2">
      <p className="font-mono text-xs text-muted">
        {result.source_type} — earnings call segment
      </p>
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio
        controls
        preload="none"
        className="h-8 w-full"
        src={result.storage_key}
      />
      {result.text_preview && (
        <p className="line-clamp-2 text-xs text-foreground/60">
          {result.text_preview}
        </p>
      )}
    </div>
  );
}
