import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from transformers import pipeline
from werkzeug.utils import secure_filename
import io

# --- Initialize Flask app ---
app = Flask(__name__)
CORS(app)

# --- Summarization model ---
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# --- Root health route (important for Render detection) ---
@app.route("/")
def home():
    return "✅ DocVibe AI Summarizer Backend is running!"

# --- Helper: extract text from PDF ---
def extract_text_from_pdf(file_bytes):
    text = ""
    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in pdf_doc:
        text += page.get_text("text")
    return text.strip()

# --- Helper: extract text from image ---
def extract_text_from_image(file_bytes):
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)
    return text.strip()

# --- Summarization endpoint ---
@app.route("/summarize", methods=["POST"])
def summarize():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    file_bytes = file.read()

    # --- Determine file type ---
    ext = filename.lower().split(".")[-1]
    text = ""

    try:
        if ext == "pdf":
            text = extract_text_from_pdf(file_bytes)
        elif ext in ["png", "jpg", "jpeg"]:
            text = extract_text_from_image(file_bytes)
        elif ext in ["txt"]:
            text = file_bytes.decode("utf-8")
        else:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

        # --- Generate summary ---
        if not text:
            return jsonify({"error": "No text found in the document"}), 400

        summary = summarizer(text[:3000], max_length=180, min_length=40, do_sample=False)
        return jsonify({
            "summary": summary[0]["summary_text"],
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Flask app entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
