"""
extractors/base_extractor.py
Base class and utilities for KYC document extraction.
"""

import re
from datetime import datetime

class BaseExtractor:
    NAME_BLACKLIST = {
        "INDIA", "GOVERNMENT", "GOVT", "INCOME", "TAX", "DEPARTMENT", "PERMANENT",
        "ACCOUNT", "NUMBER", "CARD", "DATE", "BIRTH", "FATHER", "NAME", "SIGNATURE",
        "MALE", "FEMALE", "TRANSGENDER", "AADHAAR", "UNIQUE", "IDENTIFICATION",
        "AUTHORITY", "UNION", "DRIVING", "LICENCE", "LICENSE", "MOTOR", "VEHICLE",
        "PASSPORT", "REPUBLIC", "ELECTION", "COMMISSION", "ELECTOR", "PHOTO",
        "IDENTITY", "EPIC", "BHARAT", "SARKAR", "YEAR", "DOB", "DOI", "VALID",
        "TILL", "ADDRESS", "HOUSE", "ROAD", "STREET", "VILLAGE", "POST", "DISTRICT",
        "PIN", "PINCODE", "STATE", "COV", "LMV", "MCWG", "NT", "TR"
    }

    def __init__(self, raw_text="", lines=None, details=None):
        self.raw_text = raw_text or ""
        self.lines = [l.strip() for l in (lines or []) if l.strip()]
        self.details = details or []

    def clean_string(self, s):
        if not s:
            return ""
        # Remove non-ascii or odd symbols except basic punctuation
        cleaned = re.sub(r"[^\w\s\-\/\.,#@:]", " ", s)
        return " ".join(cleaned.split())

    def extract_dates(self, text=None):
        """
        Extract dates matching DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY.
        Returns list of matched normalized date strings.
        """
        target = text if text is not None else self.raw_text
        patterns = [
            r"\b([0-3]?[0-9][/\-\.][0-1]?[0-9][/\-\.](?:19|20)[0-9]{2})\b", # DD/MM/YYYY
            r"\b((?:19|20)[0-9]{2}[/\-\.][0-1]?[0-9][/\-\.][0-3]?[0-9])\b", # YYYY-MM-DD
        ]
        dates = []
        for p in patterns:
            found = re.findall(p, target)
            for d in found:
                norm_d = d.replace("-", "/").replace(".", "/")
                # Validate date components
                parts = norm_d.split("/")
                if len(parts) == 3:
                    try:
                        if len(parts[0]) == 4: # YYYY/MM/DD
                            y, m, day = int(parts[0]), int(parts[1]), int(parts[2])
                        else: # DD/MM/YYYY
                            day, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                        if 1 <= day <= 31 and 1 <= m <= 12 and 1900 <= y <= 2050:
                            formatted = f"{day:02d}/{m:02d}/{y:04d}"
                            if formatted not in dates:
                                dates.append(formatted)
                    except ValueError:
                        continue
        return dates

    def extract_gender(self, text=None):
        """
        Detect gender: MALE, FEMALE, or TRANSGENDER.
        """
        target = (text if text is not None else self.raw_text).upper()
        # Look for full words or gender labels
        if re.search(r"\bTRANSGENDER\b", target):
            return "TRANSGENDER"
        if re.search(r"\b(FEMALE|WOMAN)\b", target) or re.search(r"\bSEX\s*[:\/]?\s*F\b", target):
            return "FEMALE"
        if re.search(r"\b(MALE|MAN)\b", target) or re.search(r"\bSEX\s*[:\/]?\s*M\b", target):
            return "MALE"
        return None

    def is_valid_name(self, candidate):
        """
        Validates if a string looks like a legitimate human name.
        """
        if not candidate:
            return False
        # Remove surrounding punctuation
        candidate = candidate.strip(" .:-/\\_")
        cleaned = re.sub(r"[^A-Za-z\s]", "", candidate).strip()
        words = cleaned.split()
        if len(words) == 0 or len(cleaned) < 3:
            return False

        # Reject if too many words (> 5)
        if len(words) > 5:
            return False

        # Check if words are blacklisted
        upper_words = [w.upper() for w in words]
        blacklisted_count = sum(1 for w in upper_words if w in self.NAME_BLACKLIST)
        if blacklisted_count >= 1:
            return False

        # Check length of each word (at least 2 letters, except single middle initial)
        for w in words:
            if len(w) == 1 and w not in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]:
                return False

        return True

    def find_field_after_label(self, label_pattern, max_lookahead=2):
        """
        Find text immediately following or on subsequent lines after a label pattern.
        """
        regex = re.compile(label_pattern, re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            m = regex.search(line)
            if m:
                # First check same line after match
                remaining = line[m.end():].strip(" :/.-")
                if remaining and len(remaining) > 2:
                    return remaining
                # Check next line
                for lookahead in range(1, max_lookahead + 1):
                    if idx + lookahead < len(self.lines):
                        nxt = self.lines[idx + lookahead].strip(" :/.-")
                        if nxt and not any(kw.lower() in nxt.lower() for kw in ["father", "date of birth", "dob", "signature", "address"]):
                            return nxt
        return None
