"""
extractors/dl_extractor.py
Extracts important fields from Driving Licence:
- dl_number
- name
- father_or_husband_name
- dob
- issue_date
- valid_till
- vehicle_classes
"""

import re
from .base_extractor import BaseExtractor


class DLExtractor(BaseExtractor):
    def extract(self):
        dl_number = self._extract_dl_number()
        dob = self._extract_dob()
        issue_date = self._extract_issue_date()
        valid_till = self._extract_valid_till()
        name, relation_name = self._extract_names()
        vehicle_classes = self._extract_vehicle_classes()

        return {
            "document_type": "DRIVING LICENCE",
            "dl_number": dl_number,
            "name": name,
            "father_or_husband_name": relation_name,
            "dob": dob,
            "issue_date": issue_date,
            "valid_till": valid_till,
            "vehicle_classes": vehicle_classes
        }

    def _extract_dl_number(self):
        # Common formats:
        # 1. State code (2 letters) followed by 13-16 digits/characters (e.g. MH1220010149313 or DL-0420110012345)
        dl_patterns = [
            r"\b([A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7})\b", # Modern 16-char format
            r"\b([A-Z]{2}[0-9]{2}\s?[0-9]{11})\b",                         # 15-char continuous
            r"\b([A-Z]{2}[0-9]{13,15})\b",                                 # Continuous
            r"\b(DL[-\s]?NO[:\s]*([A-Z0-9\-\/]{8,20}))\b",                # Labeled DL NO
        ]

        # Check line with "DL NO"
        for line in self.lines:
            if "dl no" in line.lower() or "dlno" in line.lower() or "licence no" in line.lower():
                # Extract alphanumeric code
                m = re.search(r"(?:DL\s*NO|DLNO|LICENCE\s*NO)[\s.:]*([A-Z0-9\-\/]{8,20})", line, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip(" -/:.")
                    if len(cand) >= 8:
                        return cand

        for p in dl_patterns[:3]:
            for line in self.lines:
                m = re.search(p, line.upper())
                if m:
                    return m.group(1)

        for p in dl_patterns[:3]:
            m = re.search(p, self.raw_text.upper())
            if m:
                return m.group(1)

        return None

    def _extract_dob(self):
        dob_label_regex = re.compile(r"(dob|d\.o\.b|date\s*of\s*birth)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if dob_label_regex.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]

        # Search all dates and return the one likely to be DOB (usually earlier date)
        all_dates = self.extract_dates()
        if all_dates:
            return all_dates[0]
        return None

    def _extract_issue_date(self):
        # Look for DOI / Date of Issue
        doi_regex = re.compile(r"(doi|d\.o\.i|issue\s*date|date\s*of\s*issue|issued)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if doi_regex.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]
        return None

    def _extract_valid_till(self):
        # Look for Valid Till / Validity / Expiry
        val_regex = re.compile(r"(valid\s*till|validity|valid\s*up\s*to|val\s*till|exp|expiry)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if val_regex.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]
        return None

    def _extract_names(self):
        holder_name = None
        relation_name = None

        name_regex = re.compile(r"\bname[:\s]*", re.IGNORECASE)
        relation_regex = re.compile(r"\b(s[\/\w]*w\s*of|s\/d\/w|s\/o|d\/o|w\/o|son\s*of|daughter\s*of|wife\s*of)[:\s]*", re.IGNORECASE)

        for idx, line in enumerate(self.lines):
            # Check Relation: S/D/W
            clean_l = line.strip(" :.-_")
            rel_m = relation_regex.search(clean_l)
            if rel_m:
                rem = clean_l[rel_m.end():].strip(" :/-")
                if rem and self.is_valid_name(rem):
                    relation_name = rem.upper()
                elif idx + 1 < len(self.lines):
                    cand = self.lines[idx + 1].strip(" :/-")
                    if self.is_valid_name(cand):
                        relation_name = cand.upper()

            # Check Name label
            if name_regex.search(line) and not any(k in line.lower() for k in ["father", "mother", "husband"]):
                rem = name_regex.sub("", line).strip(" :/-")
                if rem and self.is_valid_name(rem):
                    holder_name = rem.upper()
                elif idx + 1 < len(self.lines):
                    cand = self.lines[idx + 1].strip(" :/-")
                    if self.is_valid_name(cand):
                        holder_name = cand.upper()

        # Fallback if name label was separate
        if not holder_name:
            for line in self.lines:
                cand = re.sub(r"[^A-Za-z\s]", "", line).strip()
                if self.is_valid_name(cand) and cand.upper() != relation_name:
                    holder_name = cand.upper()
                    break

        return holder_name, relation_name

    def _extract_vehicle_classes(self):
        known_classes = ["MCWG", "MCWOG", "LMV", "LMV-NT", "TRANS", "HGMV", "HPMV", "3W", "INV", "E-RICKSHAW"]
        found = []
        upper_text = self.raw_text.upper()
        for vc in known_classes:
            if re.search(rf"\b{vc}\b", upper_text):
                found.append(vc)
        return found if found else None
