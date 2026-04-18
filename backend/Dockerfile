FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install base deps + [explain] extras (torch, transformers, shap)
COPY pyproject.toml .
RUN uv pip install --system -e ".[explain]" --no-cache

# Pre-download FinBERT weights so first request doesn't pay a ~440MB download
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    AutoTokenizer.from_pretrained('ProsusAI/finbert'); \
    AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')"

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

# Railway sets $PORT; fall back to 8000 for local docker run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
