"""
extractors/voter_extractor.py
Extracts important fields from Voter Card (EPIC):
- voter_id (EPIC Number)
- name (Elector's Name)
- relation_name (Father's/Husband's Name)
- dob_or_age
- gender
"""

import re
from .base_extractor import BaseExtractor


class VoterExtractor(BaseExtractor):
    def extract(self):
        epic_number = self._extract_epic_number()
        name, relation_name = self._extract_names()
        dob_or_age = self._extract_dob_or_age()
        gender = self.extract_gender()

        return {
            "document_type": "VOTAR CARD",
            "voter_id": epic_number,
            "name": name,
            "relation_name": relation_name,
            "dob_or_age": dob_or_age,
            "gender": gender
        }

    def _extract_epic_number(self):
        # Modern EPIC pattern: 3 letters + 7 digits (e.g., ZVF2036291, GDN0225185)
        epic_regex = re.compile(r"\b([A-Z]{3}[0-9]{7})\b")
        for line in self.lines:
            m = epic_regex.search(line.upper())
            if m:
                return m.group(1)

        m = epic_regex.search(self.raw_text.upper())
        if m:
            return m.group(1)

        # Older format: [State 2-3 chars]/[0-9]{2,3}/[0-9]{3}/[0-9]{6}
        old_epic_regex = re.compile(r"\b([A-Z]{2,3}\/[0-9]{2,3}\/[0-9]{3}\/[0-9]{5,7})\b")
        for line in self.lines:
            m = old_epic_regex.search(line.upper())
            if m:
                return m.group(1)

        # Loose alphanumeric search after EPIC NO label
        label_regex = re.compile(r"(epic\s*no|epic|card\s*no)[:\s]*([A-Z0-9\-\/]{8,15})", re.IGNORECASE)
        for line in self.lines:
            m = label_regex.search(line)
            if m:
                return m.group(2).strip(" -/:.")

        return None

    def _extract_names(self):
        holder_name = None
        relation_name = None

        name_kw = re.compile(r"(elector['’]?s?\s*name|voter['’]?s?\s*name|निर्वाचक\s*का\s*नाम|name)[:\s]*", re.IGNORECASE)
        rel_kw = re.compile(r"(father['’]?s?\s*name|husband['’]?s?\s*name|पिता\s*का\s*नाम|पति\s*का\s*नाम)[:\s]*", re.IGNORECASE)

        for idx, line in enumerate(self.lines):
            # Check Relation Name first (so it doesn't conflict with 'Name')
            if rel_kw.search(line):
                rem = rel_kw.sub("", line).strip(" :/-")
                if rem and self.is_valid_name(rem):
                    relation_name = rem.upper()
                elif idx + 1 < len(self.lines):
                    cand = self.lines[idx + 1].strip(" :/-")
                    if self.is_valid_name(cand):
                        relation_name = cand.upper()

            # Check Elector Name
            elif name_kw.search(line) and not any(k in line.lower() for k in ["father", "husband", "mother", "elector photo", "identity"]):
                rem = name_kw.sub("", line).strip(" :/-")
                if rem and self.is_valid_name(rem):
                    holder_name = rem.upper()
                elif idx + 1 < len(self.lines):
                    cand = self.lines[idx + 1].strip(" :/-")
                    if self.is_valid_name(cand):
                        holder_name = cand.upper()

        # Fallback heuristic
        if not holder_name or not relation_name:
            candidates = []
            for line in self.lines:
                cand = re.sub(r"[^A-Za-z\s]", "", line).strip()
                if self.is_valid_name(cand):
                    u = cand.upper()
                    if u not in candidates:
                        candidates.append(u)

            if not holder_name and candidates:
                holder_name = candidates[0]
            if not relation_name and len(candidates) > 1:
                for c in candidates:
                    if c != holder_name:
                        relation_name = c
                        break

        return holder_name, relation_name

    def _extract_dob_or_age(self):
        # 1. Search for explicit date
        dob_kw = re.compile(r"(date\s*of\s*birth|dob|birth|age|आयु|जन्म)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if dob_kw.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]

                # Check for Age: e.g. "Age: 25" or "25 Years"
                age_m = re.search(r"\b([1-9][0-9])\s*(?:years|yrs|वर्ष)?\b", line, re.IGNORECASE)
                if age_m:
                    return f"{age_m.group(1)} Years"

        # General dates
        dates = self.extract_dates()
        if dates:
            return dates[0]

        # Search for age in whole text
        age_m = re.search(r"(?:age|आयु)[:\s]*([1-9][0-9])", self.raw_text, re.IGNORECASE)
        if age_m:
            return f"{age_m.group(1)} Years"

        return None
