"""
preprocessor.py
Image preprocessing module for KYC documents.
Designed to be lightweight and fast for 2-4GB RAM environments.
"""

import io
import cv2
import numpy as np
from PIL import Image

try:
    import fitz  # PyMuPDF for PDF support
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class ImagePreprocessor:
    def __init__(self, max_dimension=1800):
        self.max_dimension = max_dimension

    def load_image(self, file_source):
        """
        Load an image from filepath, bytes, file-like object, or PDF.
        Returns a numpy array in BGR format.
        """
        if isinstance(file_source, np.ndarray):
            return file_source

        if isinstance(file_source, str):
            # Check if PDF
            if file_source.lower().endswith(".pdf"):
                return self._load_from_pdf(file_source)
            
            # Use OpenCV to read file with unicode path support
            img = cv2.imdecode(np.fromfile(file_source, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                # Fallback to PIL
                with Image.open(file_source) as pil_img:
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img

        if isinstance(file_source, (bytes, bytearray)):
            # Check for PDF magic bytes (%PDF)
            if file_source.startswith(b"%PDF"):
                return self._load_from_pdf_bytes(file_source)
            
            nparr = np.frombuffer(file_source, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                # Fallback to PIL
                with Image.open(io.BytesIO(file_source)) as pil_img:
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img

        if hasattr(file_source, "read"):
            data = file_source.read()
            return self.load_image(data)

        raise ValueError("Unsupported image source type")

    def _load_from_pdf(self, pdf_path):
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF is required to process PDF files.")
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            raise ValueError("PDF is empty")
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        doc.close()
        return img

    def _load_from_pdf_bytes(self, pdf_bytes):
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF is required to process PDF files.")
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0:
            raise ValueError("PDF is empty")
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        doc.close()
        return img

    def resize_if_needed(self, img):
        """
        Keep image within max_dimension to preserve low RAM and fast inference.
        """
        if img is None:
            return None
        h, w = img.shape[:2]
        longest_edge = max(h, w)
        if longest_edge > self.max_dimension:
            scale = self.max_dimension / float(longest_edge)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img

    def preprocess_for_ocr(self, img, enhance_contrast=True):
        """
        Lightweight preprocessing pipeline:
        1. Resize if image is oversized
        2. Denoise and enhance contrast using CLAHE
        """
        if img is None:
            return None

        # Resize for performance
        processed = self.resize_if_needed(img)

        # Enhance contrast if color image
        if enhance_contrast and len(processed.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            processed = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        return processed

    def get_deskew_angle(self, img):
        """
        Calculate skew angle of document text.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return 0.0
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        return angle
