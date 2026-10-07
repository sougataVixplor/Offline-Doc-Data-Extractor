"""
api.py
Flask REST API and Web Interface for Offline KYC Document Classification & Data Extraction.
Optimized for 2-4GB RAM servers.
"""

import os
import sys
import json
import psutil
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

from data_extractor import KYCDataExtractor

app = Flask(__name__, template_folder="templates", static_folder="static")

# Configuration
CONFIG_PATH = "confing.json" if os.path.exists("confing.json") else "config.json"
extractor = KYCDataExtractor(config_path=CONFIG_PATH)

app.config["MAX_CONTENT_LENGTH"] = extractor.config.get("server", {}).get("max_content_length_mb", 16) * 1024 * 1024
UPLOAD_FOLDER = os.path.abspath("uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    """Main Web Application Dashboard."""
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def extract_document():
    """
    Extracts important KYC fields and classifies document.
    Accepts:
    1. multipart/form-data: 'file' (uploaded file)
    2. multipart/form-data: 'sample_path' (relative path to workspace sample)
    3. json payload: {'image': '<base64>', 'force_type': 'PAN CARD'}
    """
    force_type = request.form.get("force_type") or None

    # Option A: Sample path from test suite
    sample_path = request.form.get("sample_path")
    if sample_path:
        # Sanitize path to prevent traversal
        safe_path = os.path.abspath(sample_path)
        base_dir = os.path.abspath(os.getcwd())
        if not safe_path.startswith(base_dir) or not os.path.exists(safe_path):
            return jsonify({"status": "error", "message": "Invalid sample file path."}), 400

        result = extractor.process_document(safe_path, force_type=force_type)
        return jsonify(result)

    # Option B: Uploaded file
    if "file" in request.files:
        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            return jsonify({"status": "error", "message": "No selected file."}), 400

        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return jsonify({"status": "error", "message": "Uploaded file is empty."}), 400

        result = extractor.process_document(
            file_bytes,
            filename=secure_filename(uploaded_file.filename),
            force_type=force_type
        )
        return jsonify(result)

    # Option C: Base64 JSON
    if request.is_json:
        data = request.get_json()
        b64_str = data.get("image")
        force_type = data.get("force_type")
        if not b64_str:
            return jsonify({"status": "error", "message": "Missing 'image' base64 data."}), 400

        import base64
        try:
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]
            file_bytes = base64.b64decode(b64_str)
            result = extractor.process_document(file_bytes, force_type=force_type)
            return jsonify(result)
        except Exception as e:
            return jsonify({"status": "error", "message": f"Base64 decode failed: {str(e)}"}), 400

    return jsonify({"status": "error", "message": "No file or image payload provided."}), 400


@app.route("/api/classify", methods=["POST"])
def classify_document():
    """Classify document only without extracting all fields."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400

    uploaded_file = request.files["file"]
    file_bytes = uploaded_file.read()

    img = extractor.preprocessor.load_image(file_bytes)
    prep_img = extractor.preprocessor.preprocess_for_ocr(img)
    ocr_res = extractor.ocr_engine.extract(prep_img)
    lines = ocr_res.get("lines", [])

    cls_res = extractor.classifier.classify(lines)
    return jsonify({
        "status": "success",
        "document_type": cls_res["document_type"],
        "confidence": cls_res["confidence"],
        "details": cls_res
    })


@app.route("/api/sample/<path:filepath>", methods=["GET"])
def get_sample_file(filepath):
    """Serve sample file for preview in frontend."""
    safe_path = os.path.abspath(filepath)
    base_dir = os.path.abspath(os.getcwd())
    if not safe_path.startswith(base_dir) or not os.path.exists(safe_path):
        return jsonify({"status": "error", "message": "File not found."}), 404
    return send_file(safe_path)


@app.route("/api/samples", methods=["GET"])
def list_samples():
    """List available sample KYC documents."""
    sample_dirs = [
        "PAN CARD SAMPLE",
        "AADHAR CARD SAMPLE",
        "DRIVING LICENCE SAMPLE",
        "PASSPORT SAMPLE",
        "VOTAR CARD SAMPLE"
    ]
    samples_found = {}
    for d in sample_dirs:
        if os.path.exists(d):
            samples_found[d] = [
                f"{d}/{fname}" for fname in os.listdir(d)
                if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".jfif", ".pdf"))
            ]
    return jsonify({"status": "success", "samples": samples_found})


@app.route("/api/health", methods=["GET"])
def health_check():
    """Returns system memory and service status."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = round(mem_info.rss / (1024 * 1024), 2)

    return jsonify({
        "status": "ok",
        "ocr_engine": extractor.ocr_engine.preferred_engine,
        "memory_mb": mem_mb,
        "python_version": sys.version.split()[0],
        "allowed_kyc_types": extractor.classifier.DOC_TYPES
    })


if __name__ == "__main__":
    server_cfg = extractor.config.get("server", {})
    host = server_cfg.get("host", "0.0.0.0")
    port = int(server_cfg.get("port", 5000))
    debug = server_cfg.get("debug", False)

    print(f"\n* Starting KYC Document Extraction Server at http://127.0.0.1:{port}")
    print(f"* OCR Engine: {extractor.ocr_engine.preferred_engine.upper()} (Offline)")
    print(f"* Memory Optimized for 2-4GB RAM Servers\n")

    app.run(host=host, port=port, debug=debug)
