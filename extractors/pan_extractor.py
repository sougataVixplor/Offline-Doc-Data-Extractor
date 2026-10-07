"""
extractors/pan_extractor.py
Extracts important fields from PAN Card:
- pan_number
- name
- father_name
- dob
"""

import re
from .base_extractor import BaseExtractor


class PANExtractor(BaseExtractor):
    def extract(self):
        pan_num = self._extract_pan_number()
        dob = self._extract_dob()
        name, father_name = self._extract_names()

        return {
            "document_type": "PAN CARD",
            "pan_number": pan_num,
            "name": name,
            "father_name": father_name,
            "dob": dob
        }

    def _extract_pan_number(self):
        # Standard PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
        pan_regex = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")
        for line in self.lines:
            m = pan_regex.search(line.upper())
            if m:
                return m.group(1)

        # Relaxed match in whole raw text
        m = pan_regex.search(self.raw_text.upper())
        if m:
            return m.group(1)

        # OCR fix: sometimes 0 is O or 1 is I in the 4 digits
        relaxed_regex = re.compile(r"\b([A-Z]{5}[0-9OIl]{4}[A-Z])\b")
        for line in self.lines:
            m = relaxed_regex.search(line.upper())
            if m:
                cand = m.group(1)
                # Correct digits
                digits = cand[5:9].replace("O", "0").replace("I", "1").replace("L", "1")
                fixed = cand[:5] + digits + cand[9:]
                if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", fixed):
                    return fixed

        return None

    def _extract_dob(self):
        # Look for dates near "Date of Birth" or anywhere in card
        dob_label_regex = re.compile(r"(date\s*of\s*birth|dob|d\.o\.b)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if dob_label_regex.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                # Check next line
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]

        # General date search
        all_dates = self.extract_dates()
        if all_dates:
            return all_dates[0]
        return None

    def _extract_names(self):
        """
        Extract holder name and father's name.
        Typical PAN format:
        [Header: Income Tax Department]
        [PAN Number: ABCDE1234F]
        [Name Label / Holder Name]
        [Father's Name Label / Father Name]
        [DOB]
        """
        holder_name = None
        father_name = None

        father_indices = []
        name_indices = []

        for idx, line in enumerate(self.lines):
            l_lower = line.lower()
            if "father" in l_lower or "f/name" in l_lower or "fthr" in l_lower or "पिता" in line:
                father_indices.append(idx)
            elif re.search(r"\bname\b", l_lower) and not any(k in l_lower for k in ["father", "account", "department"]):
                name_indices.append(idx)

        # 1. Try finding by Father's Name label
        if father_indices:
            f_idx = father_indices[0]
            # Check same line
            f_line = self.lines[f_idx]
            rem = re.sub(r".*father['’]?s?\s*name[:\s]*", "", f_line, flags=re.IGNORECASE).strip(" :/-")
            if rem and self.is_valid_name(rem):
                father_name = rem.upper()
            elif f_idx + 1 < len(self.lines):
                cand = self.lines[f_idx + 1].strip(" :/-")
                if self.is_valid_name(cand):
                    father_name = cand.upper()

        # 2. Try finding by Name label
        if name_indices:
            n_idx = name_indices[0]
            n_line = self.lines[n_idx]
            rem = re.sub(r".*name[:\s]*", "", n_line, flags=re.IGNORECASE).strip(" :/-")
            if rem and self.is_valid_name(rem):
                holder_name = rem.upper()
            elif n_idx + 1 < len(self.lines):
                cand = self.lines[n_idx + 1].strip(" :/-")
                if self.is_valid_name(cand) and cand.upper() != father_name:
                    holder_name = cand.upper()

        # 3. Heuristic fallback: search valid name lines in document
        if not holder_name or not father_name:
            candidates = []
            for line in self.lines:
                cand = re.sub(r"[^A-Za-z\s]", "", line).strip()
                if self.is_valid_name(cand):
                    # Check if line isn't already assigned
                    u = cand.upper()
                    if u not in candidates:
                        candidates.append(u)

            if not holder_name and candidates:
                holder_name = candidates[0]
            if not father_name and len(candidates) > 1:
                # If holder_name is candidates[0], father is candidate[1]
                for c in candidates:
                    if c != holder_name:
                        father_name = c
                        break

        return holder_name, father_name
