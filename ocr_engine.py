"""
ocr_engine.py
Unified Offline OCR Engine supporting RapidOCR (ONNX Runtime) and Tesseract-OCR (pytesseract).
Designed for low memory (2-4GB RAM) environments.
"""

import os
import shutil
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Lazy singleton instances
_RAPID_OCR_INSTANCE = None
_RAPID_OCR_INIT_TRIED = False


class OCREngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.preferred_engine = self.config.get("engine", "rapidocr").lower()
        self.fallback_engine = self.config.get("fallback_engine", "tesseract").lower()
        self.tesseract_cmd = self.config.get("tesseract_cmd", "tesseract")
        self.confidence_threshold = float(self.config.get("confidence_threshold", 0.5))

        self._setup_tesseract()

    def _setup_tesseract(self):
        """Configure pytesseract path if binary exists."""
        try:
            import pytesseract
            # Check custom configured path
            if os.path.exists(self.tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            elif shutil.which("tesseract"):
                pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")
        except ImportError:
            pass

    def _get_rapid_ocr(self):
        global _RAPID_OCR_INSTANCE, _RAPID_OCR_INIT_TRIED
        if _RAPID_OCR_INSTANCE is None and not _RAPID_OCR_INIT_TRIED:
            _RAPID_OCR_INIT_TRIED = True
            try:
                from rapidocr import RapidOCR
                _RAPID_OCR_INSTANCE = RapidOCR()
                logger.info("RapidOCR initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize RapidOCR: {e}")
                _RAPID_OCR_INSTANCE = None
        return _RAPID_OCR_INSTANCE

    def extract(self, img_bgr):
        """
        Extract text from BGR image.
        Returns a dict:
        {
            "engine_used": "rapidocr" | "tesseract",
            "lines": [ "line 1", "line 2", ... ],
            "raw_text": "line 1\nline 2...",
            "details": [
                {"text": "...", "score": 0.95, "box": [[x,y],...]}
            ]
        }
        """
        if img_bgr is None:
            return {"engine_used": "none", "lines": [], "raw_text": "", "details": []}

        if self.preferred_engine == "rapidocr":
            res = self._run_rapidocr(img_bgr)
            if res and res.get("lines"):
                return res
            if self.fallback_engine == "tesseract":
                return self._run_tesseract(img_bgr)
            return res

        elif self.preferred_engine == "tesseract":
            res = self._run_tesseract(img_bgr)
            if res and res.get("lines"):
                return res
            if self.fallback_engine == "rapidocr":
                return self._run_rapidocr(img_bgr)
            return res

        # Default fallback
        return self._run_rapidocr(img_bgr)

    def _run_rapidocr(self, img_bgr):
        engine = self._get_rapid_ocr()
        if engine is None:
            return {"engine_used": "rapidocr_unavailable", "lines": [], "raw_text": "", "details": []}

        try:
            # RapidOCR accepts numpy BGR or RGB array
            output = engine(img_bgr)
            if output is None:
                return {"engine_used": "rapidocr", "lines": [], "raw_text": "", "details": []}

            lines = []
            details = []

            # RapidOCR 3.x returns RapidOCROutput object or tuple in earlier versions
            if hasattr(output, "txts") and output.txts is not None:
                txts = output.txts
                scores = output.scores if hasattr(output, "scores") and output.scores is not None else [1.0] * len(txts)
                boxes = output.boxes if hasattr(output, "boxes") and output.boxes is not None else [[]] * len(txts)

                for txt, score, box in zip(txts, scores, boxes):
                    clean_txt = str(txt).strip()
                    if clean_txt:
                        lines.append(clean_txt)
                        details.append({
                            "text": clean_txt,
                            "score": float(score) if score is not None else 1.0,
                            "box": box.tolist() if hasattr(box, "tolist") else box
                        })
            elif isinstance(output, (list, tuple)) and len(output) > 0:
                # In rapidocr older versions: output is [[box, txt, score], ...]
                first = output[0]
                if isinstance(first, (list, tuple)) and len(first) >= 2:
                    for item in output:
                        txt = str(item[1]).strip()
                        score = float(item[2]) if len(item) > 2 else 1.0
                        box = item[0]
                        if txt:
                            lines.append(txt)
                            details.append({
                                "text": txt,
                                "score": score,
                                "box": box
                            })

            raw_text = "\n".join(lines)
            return {
                "engine_used": "rapidocr",
                "lines": lines,
                "raw_text": raw_text,
                "details": details
            }
        except Exception as e:
            logger.error(f"RapidOCR execution error: {e}")
            return {"engine_used": "rapidocr_error", "lines": [], "raw_text": "", "details": [], "error": str(e)}

    def _run_tesseract(self, img_bgr):
        try:
            import pytesseract
            # Convert BGR to RGB for PIL / tesseract
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            
            # Extract line text and data with confidence
            data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
            lines = []
            details = []
            
            current_line_num = -1
            current_line_words = []
            
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = float(data["conf"][i])
                line_num = data["line_num"][i]
                
                if text:
                    if line_num != current_line_num:
                        if current_line_words:
                            lines.append(" ".join(current_line_words))
                            current_line_words = []
                        current_line_num = line_num
                    current_line_words.append(text)
                    details.append({
                        "text": text,
                        "score": conf / 100.0 if conf >= 0 else 0.5,
                        "box": [
                            [data["left"][i], data["top"][i]],
                            [data["left"][i] + data["width"][i], data["top"][i] + data["height"][i]]
                        ]
                    })
            if current_line_words:
                lines.append(" ".join(current_line_words))

            raw_text = pytesseract.image_to_string(img_rgb).strip()
            return {
                "engine_used": "tesseract",
                "lines": lines,
                "raw_text": raw_text,
                "details": details
            }
        except Exception as e:
            logger.warning(f"Tesseract execution error: {e}")
            return {"engine_used": "tesseract_unavailable", "lines": [], "raw_text": "", "details": [], "error": str(e)}
