# ===============================
# ✅ DOCVIBE AI SUMMARIZER - Render Deploy (Optimized)
# ===============================
FROM python:3.10-slim

# --- Install system dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Set working directory ---
WORKDIR /app

# --- Copy dependency list ---
COPY requirements.txt .

# --- Install dependencies ---
RUN pip install --upgrade pip \
 && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# --- Copy project files ---
COPY . .

# --- Expose Render port ---
EXPOSE 10000

# --- Start Flask app with Gunicorn ---
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
