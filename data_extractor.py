"""
data_extractor.py
Main KYC Data Extraction pipeline and orchestrator.
Handles end-to-end preprocessing, OCR, classification, and field extraction.
"""

import os
import json
import time
import logging
from typing import Union, Dict, Any

from preprocessor import ImagePreprocessor
from ocr_engine import OCREngine
from classifier import KYCClassifier
from extractors import (
    PANExtractor,
    AadhaarExtractor,
    DLExtractor,
    PassportExtractor,
    VoterExtractor
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class KYCDataExtractor:
    EXTRACTOR_MAP = {
        "PAN CARD": PANExtractor,
        "AADHAR CARD": AadhaarExtractor,
        "DRIVING LICENCE": DLExtractor,
        "PASSPORT": PassportExtractor,
        "VOTAR CARD": VoterExtractor
    }

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        
        ocr_cfg = self.config.get("ocr", {})
        cls_cfg = self.config.get("classification", {})

        self.preprocessor = ImagePreprocessor(max_dimension=ocr_cfg.get("max_image_dimension", 1800))
        self.ocr_engine = OCREngine(ocr_cfg)
        self.classifier = KYCClassifier(min_confidence=cls_cfg.get("min_confidence", 0.35))

    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        candidates = [config_path, "confing.json", "config.json"]
        for p in candidates:
            if p and os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading config {p}: {e}")
        return {}

    def process_document(
        self,
        image_source: Union[str, bytes, bytearray, Any],
        filename: str = None,
        force_type: str = None
    ) -> Dict[str, Any]:
        """
        Processes a document end-to-end:
        1. Loads and preprocesses image/PDF
        2. Performs offline OCR
        3. Classifies document into one of 5 fixed KYC types (unless force_type is provided)
        4. Extracts relevant important fields
        """
        start_time = time.time()
        try:
            # 1. Load image
            img = self.preprocessor.load_image(image_source)
            if img is None:
                return {
                    "status": "error",
                    "message": "Failed to decode image from provided source."
                }

            # 2. Preprocess (resize if oversize, enhance contrast)
            prep_img = self.preprocessor.preprocess_for_ocr(img)

            # 3. Perform OCR
            ocr_result = self.ocr_engine.extract(prep_img)
            lines = ocr_result.get("lines", [])
            raw_text = ocr_result.get("raw_text", "")
            engine_used = ocr_result.get("engine_used", "unknown")

            if not lines:
                return {
                    "status": "warning",
                    "message": "No text detected in document.",
                    "document_type": "UNKNOWN",
                    "classification_confidence": 0.0,
                    "extracted_data": {},
                    "raw_text": "",
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2)
                }

            # 4. Classification
            if force_type and force_type in self.EXTRACTOR_MAP:
                doc_type = force_type
                confidence = 1.0
                cls_details = {"forced": True}
            else:
                cls_res = self.classifier.classify(lines)
                doc_type = cls_res["document_type"]
                confidence = cls_res["confidence"]
                cls_details = cls_res

            # 5. Extraction
            extracted_fields = {}
            if doc_type in self.EXTRACTOR_MAP:
                extractor_cls = self.EXTRACTOR_MAP[doc_type]
                extractor = extractor_cls(
                    raw_text=raw_text,
                    lines=lines,
                    details=ocr_result.get("details", [])
                )
                extracted_fields = extractor.extract()
            else:
                extracted_fields = {
                    "document_type": "UNKNOWN",
                    "message": "Document could not be recognized as one of the 5 standard KYC types."
                }

            duration_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "status": "success",
                "document_type": doc_type,
                "classification_confidence": confidence,
                "classification_details": cls_details,
                "ocr_engine": engine_used,
                "extracted_data": extracted_fields,
                "lines_count": len(lines),
                "raw_text": raw_text,
                "processing_time_ms": duration_ms
            }

        except Exception as e:
            logger.exception("Error processing KYC document")
            return {
                "status": "error",
                "message": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    extractor = KYCDataExtractor()

    test_files = [
        r"PAN CARD SAMPLE\SAMPLE-3.jpg",
        r"AADHAR CARD SAMPLE\SAMPLE-2.webp",
        r"DRIVING LICENCE SAMPLE\SAMPLE-1.webp",
        r"PASSPORT SAMPLE\SAMPLE-1.webp",
        r"VOTAR CARD SAMPLE\SAMPLE-1.webp"
    ]

    for tf in test_files:
        if os.path.exists(tf):
            print("=" * 60)
            print(f"Testing: {tf}")
            res = extractor.process_document(tf)
            print(f"Type: {res.get('document_type')} (Confidence: {res.get('classification_confidence')}) in {res.get('processing_time_ms')} ms")
            print("Extracted Data:", json.dumps(res.get("extracted_data"), indent=2))
