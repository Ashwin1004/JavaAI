# ===============================
# ✅ DOCVIBE AI SUMMARIZER - Render Deploy (Final Stable)
# ===============================
FROM python:3.12-slim

# --- Install required system packages ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- Set working directory ---
WORKDIR /app

# --- Copy dependency list first (for Docker caching) ---
COPY requirements.txt .

# --- Install dependencies ---
RUN pip install --upgrade pip \
 && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# --- Copy project files ---
COPY . .

# --- Set environment variables ---
ENV PORT=10000
EXPOSE ${PORT}

# --- Preload summarization model (optional) ---
RUN python -c "from transformers import pipeline; pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')"

# --- Start Flask app with Gunicorn ---
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
