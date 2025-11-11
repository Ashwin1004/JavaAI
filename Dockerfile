# ===============================
# ✅ DOCVIBE AI SUMMARIZER - Render Deploy
# ===============================
FROM python:3.12-slim

# --- Install system dependencies (Tesseract OCR + Build tools + PDF libs) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libmupdf-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- Set working directory ---
WORKDIR /app

# --- Copy requirements file and install dependencies ---
COPY requirements.txt .

# Upgrade pip, install PyTorch CPU, then the rest
RUN pip install --upgrade pip \
 && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# --- Copy app files ---
COPY . .

# --- Expose Render port ---
ENV PORT=10000
EXPOSE ${PORT}

# --- Pre-download summarizer model (optional but speeds up startup) ---
RUN python -c "from transformers import pipeline; pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')"

# --- Start app with Gunicorn (production server) ---
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
