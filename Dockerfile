# Fashion Stylist - Streamlit app (container image)
#
# Build:
#   docker build -t fashion-stylist:latest .
#
# Run (loads API keys from .env without baking them into the image):
#   docker run --rm -p 8510:8510 --env-file .env fashion-stylist:latest

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: keep minimal (most Python deps are installed from wheels)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (better layer cache)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (include Runway Director + UI template)
COPY app.py stylist_core.py prompts.py runway_director.py ./
COPY ui ./ui
COPY data ./data

# Non-root user (security best practice)
RUN useradd -ms /bin/bash appuser
USER appuser

EXPOSE 8510
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8510", "--server.address", "0.0.0.0"]

