# Use an official lightweight Python image
FROM python:3.12-slim

# Install system packages including tesseract and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      tesseract-ocr \
      libtesseract-dev \
      poppler-utils \
      build-essential \
      git \
      && rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose the port Render will use
ENV PORT 10000
EXPOSE ${PORT}

# Use gunicorn to serve app in production
# 'app:app' expects app.py with Flask app named 'app'
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
