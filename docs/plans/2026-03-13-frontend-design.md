# Frontend Design — Multimodal Financial RAG

**Date:** 2026-03-13
**Status:** Approved

---

## Decisions

- **Single-page search** with inline results on `/`, separate `/doc/[id]` for full viewer
- **Dark finance terminal** aesthetic (default) with light theme toggle
- **URL search params** as single source of truth — no state library
- **Deferred WaveformPlayer** — styled `<audio>` for v1, wavesurfer.js later

---

## Architecture & Routing

Two routes, URL-driven state.

```
frontend/src/
├── app/
│   ├── layout.tsx            # Root layout, dark default, header + theme toggle
│   ├── page.tsx              # SearchPage: search bar + filters + inline results
│   └── doc/[id]/page.tsx     # DocumentViewer: modality-specific full rendering
├── components/
│   ├── SearchBar.tsx          # Query input with submit
│   ├── FilterBar.tsx          # Modality toggles, ticker, date range, compact toggle
│   ├── ResultCard.tsx         # Dispatcher → modality-specific card
│   ├── TextCard.tsx
│   ├── AudioCard.tsx
│   ├── PDFCard.tsx
│   ├── ImageCard.tsx
│   └── ThemeToggle.tsx
├── lib/
│   ├── api.ts                # Fetch wrapper for backend
│   └── types.ts              # TypeScript interfaces matching backend schemas
└── hooks/
    └── useSearch.ts           # Reads URL params → calls API → returns results + loading
```

**Data flow:** User submits query → `useSearch` pushes params to URL → reads them back → calls `POST /api/search` → renders ResultCard list. Refresh re-runs the search.

---

## Theme System

CSS variables toggled via `dark` class on `<html>`.

### Dark theme (default)
- Background: `#0a0a0f`, card surfaces: `#12121a`
- Borders: `#1e1e2e`
- Primary accent: terminal green `#00d4aa` (scores, active states, search button)
- Secondary accent: cyan `#38bdf8` (links, modality badges)
- Text: `#e2e8f0` body, `#94a3b8` secondary

### Modality badge colors (both themes)
- Text: emerald
- Audio: violet
- PDF: rose
- Image: amber

### Typography
- System font stack for body
- Monospace for scores, tickers, dates

### Layout
- Full-width search bar, filter bar below
- Responsive grid: 1 col mobile, 2 cols tablet, 3 cols desktop
- Subtle hover glow on cards in dark mode

---

## Component Behavior

### SearchBar
- Terminal-style placeholder: "Search across earnings calls, filings, charts, and news..."
- Submit on Enter or click
- Loading spinner replaces search icon during requests

### FilterBar
- Collapses on mobile behind "Filters" toggle
- **Modality toggles:** Four colored pills, multi-select, all active by default
- **Ticker input:** Text input with uppercase enforcement, no autocomplete for v1
- **Date range:** Two native date inputs (from / to)
- **Compact toggle:** Switch labeled "768-dim", off by default, monospace label

### ResultCard
- Modality badge (top-left, colored pill)
- Relevance score (top-right, monospace, color-coded: green >0.8, yellow 0.6-0.8, red <0.6)
- Ticker + date (bottom, dimmed)
- Click → `/doc/[id]`

### Card variants
- **TextCard:** 3-line text preview, truncated with ellipsis
- **AudioCard:** Styled `<audio>`, segment timestamp (e.g. "2:30 – 3:30")
- **PDFCard:** PDF icon with source type label (e.g. "10-K Filing")
- **ImageCard:** `<img>` thumbnail from presigned URL, aspect-ratio preserved

### Empty / loading states
- Skeleton cards while loading
- "No results found" with filter adjustment suggestion

---

## DocumentViewer (`/doc/[id]`)

Result data passed via sessionStorage on card click. Renders modality-specific full content from presigned URL:
- Text: full text display
- Audio: audio player
- PDF: embedded via `<iframe>`/`<object>`
- Image: full-size image

---

## API Layer

### `lib/api.ts`
Minimal fetch wrapper, no axios. `NEXT_PUBLIC_API_URL` env var, defaults to `http://localhost:8000`.

### `lib/types.ts`
Direct mirror of backend Pydantic models: `SearchRequest`, `SearchResult`, `HealthResponse`.

### `hooks/useSearch.ts`
Reads `useSearchParams()`, calls `searchDocuments()`, returns `{ results, loading, error }`. Triggered by URL param changes.
