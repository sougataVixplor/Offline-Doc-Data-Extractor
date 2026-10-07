# 🪪 Offline KYC Document Data Extractor & Classifier

A fast, lightweight, and **100% offline** Flask web application and REST API for automatic **KYC document classification** and **important field data extraction**. 

Engineered specifically to run efficiently on **budget 2–4 GB RAM servers** without requiring GPU acceleration or external third-party cloud APIs.

---

## ✨ Features

- **🔒 100% Offline & Private:** No sensitive customer KYC documents ever leave your machine or server.
- **⚡ 2–4 GB Server Optimized:** Memory footprint stays under **~120–160 MB RAM** during inference with optimized CPU ONNX inference and automated garbage collection.
- **🎯 5 Fixed KYC Documents Supported:**
  1. **PAN CARD** (`PAN Number`, `Name`, `Father's Name`, `Date of Birth`)
  2. **AADHAAR CARD** (`Aadhaar Number`, `Name`, `DOB/YOB`, `Gender`, `Address`)
  3. **DRIVING LICENCE** (`DL Number`, `Name`, `Father's/Husband's Name`, `DOB`, `Issue Date`, `Valid Till`, `Vehicle Classes`)
  4. **PASSPORT** (`Passport Number`, `Surname`, `Given Name`, `Nationality`, `DOB`, `Expiry Date`, `Gender`, `MRZ Lines`)
  5. **VOTAR CARD / EPIC** (`Voter ID / EPIC Number`, `Elector Name`, `Father's/Husband's Name`, `DOB / Age`, `Gender`)
- **🤖 Dual Offline OCR Engines:**
  - **RapidOCR (Default):** Runs deep-learning ONNX models directly on CPU. Requires zero external C++ binaries, highly robust against rotated/skewed phone camera photos.
  - **Tesseract-OCR (pytesseract):** Optional engine configurable via `config.json` or fallback.
- **🧠 Automatic Document Classifier:** Multi-tier keyword scoring and pattern regex anchors with confidence calculation (0–100%).
- **🎨 Glassmorphism Web Interface:** Modern dark-mode UI with drag-and-drop uploads, instant test sample chips, one-click field copy buttons, raw OCR inspector, and JSON API viewer.
- **📄 Multi-Format Input Support:** JPG, PNG, WEBP, JFIF, and PDF (via PyMuPDF).

---

## 🏗️ Architecture

```
                       ┌────────────────────────────┐
                       │   Input File / Camera Shot │
                       │    (JPG / PNG / WEBP / PDF)│
                       └─────────────┬──────────────┘
                                     │
                                     ▼
                       ┌────────────────────────────┐
                       │    Image Preprocessor      │
                       │ • Dimension normalization  │
                       │ • CLAHE contrast enhance   │
                       └─────────────┬──────────────┘
                                     │
                                     ▼
                       ┌────────────────────────────┐
                       │     Offline OCR Engine     │
                       │   RapidOCR (ONNX on CPU)   │
                       │  or Tesseract (pytesseract)│
                       └─────────────┬──────────────┘
                                     │
                                     ▼
                       ┌────────────────────────────┐
                       │    KYC Classifier Engine   │
                       │ Regex anchors + Keywords   │
                       └─────────────┬──────────────┘
                                     │
         ┌──────────────┬────────────┼────────────┬──────────────┐
         ▼              ▼            ▼            ▼              ▼
   ┌───────────┐  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
   │ PAN Card  │  │  Aadhaar  │ │  Driving  │ │ Passport  │ │   Voter   │
   │ Extractor │  │ Extractor │ │  Licence  │ │ Extractor │ │ Extractor │
   └─────┬─────┘  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
         └──────────────┴────────────┼────────────┴──────────────┘
                                     │
                                     ▼
                       ┌────────────────────────────┐
                       │   Structured JSON Output   │
                       │     Web UI / REST API      │
                       └────────────────────────────┘
```

---

## 📋 System Requirements

| Specification | Requirement |
| :--- | :--- |
| **Operating System** | Linux (Ubuntu 20.04+, Debian, CentOS) or Windows 10/11 / Windows Server |
| **Python** | Python 3.9, 3.10, 3.11, or 3.12 |
| **RAM** | 2 GB to 4 GB (Active usage ~120 MB) |
| **Disk Space** | ~200 MB for Python dependencies and ONNX models |
| **CPU** | 1 to 2 vCPU cores |

---

## 🚀 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/sougataVixplor/Offline-Doc-Data-Extractor.git
cd Offline-Doc-Data-Extractor
```

### 2. Set Up a Python Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On Linux / Ubuntu:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note on RapidOCR:** `rapidocr` and `onnxruntime` will automatically download lightweight ONNX weights (~15 MB) to your local cache upon first initialization. No external software or GPU driver is needed!

---

### (Optional) Installing Tesseract-OCR

If you choose to use `tesseract` instead of `rapidocr`, install the Tesseract system binary:

#### On Ubuntu / Debian:
```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

#### On Windows:
1. Download the Windows installer from [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install to `C:\Program Files\Tesseract-OCR`.
3. Ensure the path is set in `config.json` (`"tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`).

---

## ⚙️ Configuration (`config.json` / `confing.json`)

You can tune OCR preferences and server settings in `config.json`:

```json
{
  "ocr": {
    "engine": "rapidocr",
    "fallback_engine": "tesseract",
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "language": "eng",
    "max_image_dimension": 1800,
    "confidence_threshold": 0.5
  },
  "classification": {
    "min_confidence": 0.35,
    "allowed_types": [
      "PAN CARD",
      "AADHAR CARD",
      "DRIVING LICENCE",
      "PASSPORT",
      "VOTAR CARD"
    ]
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "max_content_length_mb": 16
  }
}
```

---

## 🏃 Running the Application

### Development Server

Run with either entrypoint:

```bash
python api.py
```
*or:*
```bash
python applicatiom.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

### Production Deployment (2–4 GB Server)

For production, run using a production WSGI server.

#### On Linux (using Gunicorn with 2 workers):
```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 api:app --timeout 60
```

#### On Windows (using Waitress):
```bash
pip install waitress
waitress-serve --listen=0.0.0.0:5000 api:app
```

---

## 🔌 REST API Documentation

### 1. Extract Document Data
**`POST /api/extract`**

Extracts text, classifies document type, and extracts all key fields.

#### A. Form-data Upload
- `file`: (Binary file) The image or PDF file.
- `force_type`: (Optional string) Manually force a type (`PAN CARD`, `AADHAR CARD`, `DRIVING LICENCE`, `PASSPORT`, `VOTAR CARD`).

```bash
curl -X POST http://127.0.0.1:5000/api/extract \
  -F "file=@/path/to/pan_card.jpg"
```

#### B. Base64 JSON Payload
```bash
curl -X POST http://127.0.0.1:5000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64_string>", "force_type": null}'
```

#### C. Sample File Path
```bash
curl -X POST http://127.0.0.1:5000/api/extract \
  -F "sample_path=PAN CARD SAMPLE/SAMPLE-3.jpg"
```

#### Example Response:
```json
{
  "status": "success",
  "document_type": "PAN CARD",
  "classification_confidence": 0.91,
  "ocr_engine": "rapidocr",
  "processing_time_ms": 284.15,
  "extracted_data": {
    "document_type": "PAN CARD",
    "pan_number": "GQBPK8700C",
    "name": "KOCHERLA SRIKANTH",
    "father_name": "MUKKANTIKOCHERLA",
    "dob": "04/05/1997"
  },
  "raw_text": "INCOMETAXDEPARTMENT\nGOVT. OF INDIA\n..."
}
```

---

### 2. Document Classification Only
**`POST /api/classify`**

Quickly classifies the document type without full field extraction.

```bash
curl -X POST http://127.0.0.1:5000/api/classify \
  -F "file=@/path/to/aadhar.jpg"
```

#### Example Response:
```json
{
  "status": "success",
  "document_type": "AADHAR CARD",
  "confidence": 0.90,
  "details": {
    "top_score": 14.5,
    "scores": {
      "AADHAR CARD": 14.5,
      "PAN CARD": 1.5,
      "DRIVING LICENCE": 0.0,
      "PASSPORT": 0.0,
      "VOTAR CARD": 0.0
    }
  }
}
```

---

### 3. Health & Memory Check
**`GET /api/health`**

Returns server health, active OCR engine, and exact RAM usage in megabytes.

```bash
curl http://127.0.0.1:5000/api/health
```

#### Example Response:
```json
{
  "status": "ok",
  "memory_mb": 112.82,
  "ocr_engine": "rapidocr",
  "python_version": "3.12.0",
  "allowed_kyc_types": [
    "PAN CARD",
    "AADHAR CARD",
    "DRIVING LICENCE",
    "PASSPORT",
    "VOTAR CARD"
  ]
}
```

---

## 🗂️ Project Directory Structure

```
Offline-Doc-Data-Extractor/
├── api.py                    # Flask application & REST API routes
├── applicatiom.py            # Entrypoint alias
├── config.json               # Server & OCR engine configuration
├── confing.json              # Configuration file
├── data_extractor.py         # Main pipeline orchestrator
├── preprocessor.py           # CLAHE contrast, deskewing & PDF loader
├── ocr_engine.py             # RapidOCR & Tesseract unified wrapper
├── classifier.py             # KYC classifier with regex & keyword scoring
├── requirements.txt          # Python dependency specifications
├── README.md                 # Project documentation & guide
│
├── extractors/               # Specialized field extractors
│   ├── __init__.py
│   ├── base_extractor.py     # Base date/name/regex normalization
│   ├── pan_extractor.py      # PAN Card fields
│   ├── aadhaar_extractor.py  # Aadhaar Card fields
│   ├── dl_extractor.py       # Driving Licence fields
│   ├── passport_extractor.py # Passport & MRZ fields
│   └── voter_extractor.py    # Voter Card (EPIC) fields
│
├── templates/
│   └── index.html            # Web UI dashboard
│
├── static/
│   ├── css/
│   │   └── style.css         # Modern dark glassmorphism design system
│   └── js/
│       └── app.js            # Drag-and-drop, sample chips, and copy logic
│
└── * SAMPLE/                 # Test sample KYC documents
    ├── AADHAR CARD SAMPLE/
    ├── DRIVING LICENCE SAMPLE/
    ├── PAN CARD SAMPLE/
    ├── PASSPORT SAMPLE/
    └── VOTAR CARD SAMPLE/
```

---

## 📄 License

This project is licensed under the MIT License.
