"""
extractors/aadhaar_extractor.py
Extracts important fields from Aadhaar Card:
- aadhaar_number
- name
- dob (or yob)
- gender
- address (if available)
"""

import re
from .base_extractor import BaseExtractor


class AadhaarExtractor(BaseExtractor):
    def extract(self):
        aadhaar_num = self._extract_aadhaar_number()
        dob, yob = self._extract_dob_or_yob()
        gender = self.extract_gender()
        name = self._extract_name(dob_or_yob=dob or yob)
        address = self._extract_address()

        return {
            "document_type": "AADHAR CARD",
            "aadhaar_number": aadhaar_num,
            "name": name,
            "dob": dob,
            "yob": yob,
            "gender": gender,
            "address": address
        }

    def _extract_aadhaar_number(self):
        # 1. 4-4-4 format: 12 digits separated by spaces
        spaced_regex = re.compile(r"\b([2-9][0-9]{3}\s+[0-9]{4}\s+[0-9]{4})\b")
        for line in self.lines:
            m = spaced_regex.search(line)
            if m:
                # Format standardly with single space
                return re.sub(r"\s+", " ", m.group(1))

        # 2. Continuous 12 digits: [2-9][0-9]{11}
        continuous_regex = re.compile(r"\b([2-9][0-9]{11})\b")
        for line in self.lines:
            m = continuous_regex.search(line)
            if m:
                num = m.group(1)
                return f"{num[:4]} {num[4:8]} {num[8:]}"

        # 3. Search in raw text
        m = spaced_regex.search(self.raw_text)
        if m:
            return re.sub(r"\s+", " ", m.group(1))

        m = continuous_regex.search(self.raw_text)
        if m:
            num = m.group(1)
            return f"{num[:4]} {num[4:8]} {num[8:]}"

        # 4. Check for Masked Aadhaar: XXXX XXXX 1234
        masked_regex = re.compile(r"\b([XxX*]{4}\s+[XxX*]{4}\s+[0-9]{4})\b")
        m = masked_regex.search(self.raw_text)
        if m:
            return m.group(1)

        return None

    def _extract_dob_or_yob(self):
        dob = None
        yob = None

        # Look for DOB / Birth labels
        dob_label_regex = re.compile(r"(dob|d\.o\.b|birth|जन्म)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if dob_label_regex.search(line):
                dates = self.extract_dates(line)
                if dates:
                    dob = dates[0]
                    break
                # Check next line
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        dob = dates[0]
                        break

                # Check Year of birth (e.g., Year of Birth / जन्म वर्ष : 1985)
                y_match = re.search(r"\b(19[4-9][0-9]|20[0-2][0-9])\b", line)
                if y_match:
                    yob = y_match.group(1)
                    break

        if not dob and not yob:
            dates = self.extract_dates()
            if dates:
                dob = dates[0]

        if dob and not yob:
            parts = dob.split("/")
            if len(parts) == 3:
                yob = parts[2]

        return dob, yob

    def _extract_name(self, dob_or_yob=None):
        """
        On Aadhaar cards, the English name is generally located directly above the DOB line
        or below the Government/Emblem header.
        """
        dob_line_idx = -1
        for idx, line in enumerate(self.lines):
            if any(k in line.lower() for k in ["dob", "birth", "जन्म"]):
                dob_line_idx = idx
                break
            if dob_or_yob and dob_or_yob in line:
                dob_line_idx = idx
                break

        # Check the line immediately preceding the DOB line
        if dob_line_idx > 0:
            for i in range(dob_line_idx - 1, -1, -1):
                cand = self.lines[i].strip()
                # Clean candidate
                cand_clean = re.sub(r"[^A-Za-z\s]", "", cand).strip()
                if self.is_valid_name(cand_clean):
                    return cand_clean.upper()

        # Fallback: scan all lines for the first valid English name
        for line in self.lines:
            cand = re.sub(r"[^A-Za-z\s]", "", line).strip()
            if self.is_valid_name(cand):
                return cand.upper()

        return None

    def _extract_address(self):
        """
        Extract address if present (back side or e-Aadhaar).
        """
        addr_started = False
        addr_lines = []
        addr_kw = re.compile(r"\b(address|पता|c/o|s/o|w/o|d/o)[:\s]*", re.IGNORECASE)

        for line in self.lines:
            if addr_kw.search(line):
                addr_started = True
                rem = addr_kw.sub("", line).strip()
                if rem:
                    addr_lines.append(rem)
                continue

            if addr_started:
                # Stop if we hit Aadhaar number or footer
                if re.search(r"\b[2-9][0-9]{3}\b", line) or "help@uidai" in line.lower():
                    break
                addr_lines.append(line)
                if len(addr_lines) >= 4:
                    break

        if addr_lines:
            return ", ".join(addr_lines)
        return None
