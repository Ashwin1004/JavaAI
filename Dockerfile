# ===============================
# ✅ DOCVIBE AI SUMMARIZER - Render Deploy
# ===============================
FROM python:3.12-slim

# --- Install system dependencies (Tesseract OCR + utils) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- Set working directory ---
WORKDIR /app

# --- Copy requirements file and install dependencies ---
COPY requirements.txt .

# Upgrade pip and install PyTorch from official CPU index first, then others
RUN pip install --upgrade pip \
 && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# --- Copy app files ---
COPY . .

# --- Expose Render port ---
ENV PORT=10000
EXPOSE ${PORT}

# --- Run app with gunicorn (for production) ---
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
