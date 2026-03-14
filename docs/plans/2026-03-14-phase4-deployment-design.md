# Phase 4: Deployment Design

## Architecture
- Fly.io: FastAPI backend (Docker), Fly Postgres (metadata)
- Qdrant Cloud: vector search
- Cloudflare R2: S3-compatible object storage (replaces MinIO)
- Vercel: Next.js frontend

## Files to create
- backend/Dockerfile
- backend/fly.toml
- backend/.dockerignore
- backend/.env.production.example

## Deployment order
1. Qdrant Cloud — create cluster (manual)
2. Cloudflare R2 — create bucket + API keys (manual)
3. Fly.io — Dockerfile, fly.toml, fly launch, attach Postgres, set secrets, deploy
4. Vercel — connect repo, set NEXT_PUBLIC_API_URL, deploy
5. Seed production — run seed scripts against Fly backend URL

## Production env vars (Fly secrets)
- GEMINI_API_KEY
- QDRANT_URL (Qdrant Cloud)
- QDRANT_API_KEY (Qdrant Cloud)
- DATABASE_URL (auto from fly postgres attach)
- S3_ENDPOINT_URL (R2)
- S3_ACCESS_KEY_ID (R2)
- S3_SECRET_ACCESS_KEY (R2)
- S3_BUCKET_NAME=financial-docs
- CORS_ORIGINS=["https://rag.datasalt.ai"]

## Vercel env var
- NEXT_PUBLIC_API_URL=https://multimodal-rag-api.fly.dev
