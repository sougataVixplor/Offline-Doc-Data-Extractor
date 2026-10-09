"""
masker.py
Confidential Data Coordinate Locator & Image Masking Engine.
Hides 80% of confidential KYC numbers with black rectangles for security and privacy.
Ensures original unmasked images are permanently purged from disk.
"""

import os
import re
import uuid
import base64
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ConfidentialMasker:
    def __init__(self, mask_ratio: float = 0.80):
        """
        mask_ratio: fraction of the confidential number bounding box to cover with black box (default 0.80 = 80%).
        """
        self.mask_ratio = mask_ratio

    def find_confidential_boxes(self, ocr_details, extracted_data, doc_type):
        """
        Locates the exact bounding boxes for confidential numbers in ocr_details.
        Returns a list of dicts with box coordinates and mask dimensions.
        """
        if not ocr_details or not extracted_data:
            return []

        # Identify targets per document type
        targets = []
        if doc_type == "PAN CARD":
            pan = extracted_data.get("pan_number")
            if pan:
                targets.append(("pan_number", pan))

        elif doc_type == "AADHAR CARD":
            aadhaar = extracted_data.get("aadhaar_number")
            if aadhaar:
                # Raw 12 digits
                clean_aadhaar = re.sub(r"\s+", "", aadhaar)
                targets.append(("aadhaar_number", clean_aadhaar))
                # Also blocks of 4 digits
                blocks = aadhaar.split()
                for b in blocks:
                    if len(b) == 4 and b.isdigit():
                        targets.append(("aadhaar_block", b))

        elif doc_type == "DRIVING LICENCE":
            dl = extracted_data.get("dl_number")
            if dl:
                targets.append(("dl_number", dl))

        elif doc_type == "PASSPORT":
            pass_num = extracted_data.get("passport_number")
            if pass_num:
                targets.append(("passport_number", pass_num))

        elif doc_type == "VOTAR CARD":
            voter = extracted_data.get("voter_id")
            if voter:
                targets.append(("voter_id", voter))

        # Scan OCR details for matching boxes
        matched_boxes = []
        seen_rects = set()

        for field_name, target_val in targets:
            clean_target = re.sub(r"[^\w]", "", target_val).upper()
            if not clean_target:
                continue

            for item in ocr_details:
                text = item.get("text", "")
                clean_text = re.sub(r"[^\w]", "", text).upper()
                box = item.get("box", [])

                if not box or len(box) < 4:
                    continue

                # Match full string or substring
                is_match = False
                if clean_target in clean_text:
                    is_match = True
                elif clean_text in clean_target and len(clean_text) >= 4:
                    is_match = True

                if is_match:
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    x_min, x_max = int(min(xs)), int(max(xs))
                    y_min, y_max = int(min(ys)), int(max(ys))
                    w = x_max - x_min
                    h = y_max - y_min

                    rect_key = (round(x_min, -1), round(y_min, -1), round(w, -1), round(h, -1))
                    if rect_key in seen_rects:
                        continue
                    seen_rects.add(rect_key)

                    # Compute 80% masking box
                    mask_w = int(w * self.mask_ratio)

                    matched_boxes.append({
                        "field": field_name,
                        "detected_text": text,
                        "raw_box": box,
                        "bounding_rect": {
                            "x": x_min,
                            "y": y_min,
                            "width": w,
                            "height": h
                        },
                        "mask_rect_80": {
                            "x": x_min,
                            "y": y_min,
                            "width": mask_w,
                            "height": h,
                            "mask_ratio": self.mask_ratio
                        }
                    })

        return matched_boxes

    def apply_mask(self, img_bgr, confidential_boxes):
        """
        Draws solid black rectangles covering 80% of confidential bounding boxes.
        Returns a masked copy of the image.
        """
        if img_bgr is None:
            return None

        masked_img = img_bgr.copy()
        img_h, img_w = masked_img.shape[:2]

        for item in confidential_boxes:
            m = item["mask_rect_80"]
            x = max(0, m["x"] - 1)
            y = max(0, m["y"] - 2)
            mw = min(img_w - x, m["width"] + 2)
            mh = min(img_h - y, m["height"] + 4)

            # Draw solid black rectangle (80% hidden)
            cv2.rectangle(
                masked_img,
                (x, y),
                (x + mw, y + mh),
                (0, 0, 0),
                thickness=-1
            )

        return masked_img

    def to_base64_data_url(self, img_bgr, quality=90):
        """Encodes BGR image to base64 JPEG data URL for instant frontend display."""
        if img_bgr is None:
            return ""
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, buffer = cv2.imencode(".jpg", img_bgr, encode_params)
        if not success:
            return ""
        b64_str = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"

    def secure_save_and_purge(self, masked_img, temp_original_path=None, output_dir="uploads/processed"):
        """
        Saves ONLY the masked image to output_dir and securely deletes the original image file.
        Returns (saved_filename, saved_filepath).
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"masked_{uuid.uuid4().hex[:12]}.jpg"
        masked_path = os.path.join(output_dir, filename)

        # 1. Save masked image
        if masked_img is not None:
            cv2.imwrite(masked_path, masked_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

        # 2. Securely purge original unmasked file if one was saved on disk
        if temp_original_path and os.path.exists(temp_original_path):
            try:
                # Overwrite bytes before unlinking for extra security
                file_size = os.path.getsize(temp_original_path)
                with open(temp_original_path, "wb") as f:
                    f.write(os.urandom(min(file_size, 4096)))
                os.remove(temp_original_path)
                logger.info(f"Securely purged original unmasked file: {temp_original_path}")
            except Exception as e:
                logger.warning(f"Could not purge temporary original file {temp_original_path}: {e}")

        return filename, masked_path
