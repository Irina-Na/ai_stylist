# ────────────────────────────────────────────────────────────────────
# Streamlit Fashion-Stylist – container image
# Build:   docker build -t fashion-stylist:latest .
# Run:     docker run --rm -p 8501:8501 \
#                    -e OPENAI_API_KEY=sk-... \
#                    -v /host/path/df_enriched.parquet:/data/df_enriched.parquet \
#                    fashion-stylist:latest
# ────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# 1. System-level deps (numpy / pandas need gcc & libpq for pyarrow)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy and install Python deps first (layer-cache friendly)
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy source code
COPY stylist_core.py app.py prompts.py ./
COPY data ./data
COPY .env ./

# 4. Create non-root user (security best-practice)
RUN useradd -ms /bin/bash appuser
USER appuser

# 5. Default command → Streamlit on port 8510
ENV PORT=8510
EXPOSE 8510
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8510", "--server.address", "0.0.0.0"]
