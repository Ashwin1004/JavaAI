import os
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyMuPDF as fitz
import pytesseract
from PIL import Image
from transformers import pipeline
from pptx import Presentation
import docx
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Use a lighter summarization model by default for faster CPU inference
MODEL_NAME = os.environ.get("SUMMARIZER_MODEL", "sshleifer/distilbart-cnn-12-6")

print("Loading summarizer model:", MODEL_NAME)
summarizer = pipeline("summarization", model=MODEL_NAME, device=-1)

def chunk_text(text, max_len=800):
    words = text.split()
    for i in range(0, len(words), max_len):
        yield ' '.join(words[i:i + max_len])

def summarize_text(text):
    summaries = []
    for chunk in chunk_text(text):
        if len(chunk.split()) < 20:
            continue
        try:
            # adjust max/min lengths to taste
            result = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(result[0]['summary_text'])
        except Exception as e:
            app.logger.error("Summarize error: %s", e)
    return " ".join(summaries) if summaries else "No significant text found."

def clean_text(text):
    return ' '.join(text.split())

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/summarize", methods=["POST"])
def summarize():
    # Accept file via multipart/form-data key 'file'
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower()
    results = {}

    try:
        # PDF
        if ext == "pdf":
            doc = fitz.open(stream=file.read(), filetype="pdf")
            pages = []
            for i, page in enumerate(doc):
                text = clean_text(page.get_text("text"))
                if len(text.strip()) > 10:
                    pages.append((i+1, text))
            # ensure pages ordered by page number
            pages.sort(key=lambda x: x[0])
            for num, text in pages:
                results[f"Page {num}"] = summarize_text(text)

        # Image
        elif ext in ["jpg", "jpeg", "png"]:
            image = Image.open(io.BytesIO(file.read()))
            text = clean_text(pytesseract.image_to_string(image))
            if text:
                results["Summary"] = summarize_text(text)
            else:
                results["Summary"] = "No readable text found in the image."

        # PPTX
        elif ext == "pptx":
            prs = Presentation(io.BytesIO(file.read()))
            slides = []
            for i, slide in enumerate(prs.slides):
                txt = ""
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        txt += shape.text + " "
                txt = clean_text(txt)
                if txt:
                    slides.append((i+1, txt))
            slides.sort(key=lambda x: x[0])
            for num, text in slides:
                results[f"Slide {num}"] = summarize_text(text)

        # DOCX
        elif ext == "docx":
            doc = docx.Document(io.BytesIO(file.read()))
            # Option: gather paragraphs into chunks to avoid one-sentence summaries
            all_text = []
            for para in doc.paragraphs:
                t = clean_text(para.text)
                if t:
                    all_text.append(t)
            # combine paragraphs into larger sections (e.g., grouping every 5 paras)
            if not all_text:
                results["Summary"] = "No readable text found in the document."
            else:
                joined = "\n\n".join(all_text)
                results["Summary"] = summarize_text(joined)

        else:
            return jsonify({"error": "Unsupported file type"}), 400

        return jsonify({"summaries": results})

    except Exception as e:
        app.logger.exception("Failed to process file")
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

if __name__ == "__main__":
    # Only for local debug; on Render we run via gunicorn
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
