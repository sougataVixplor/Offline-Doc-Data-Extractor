"""
extractors/passport_extractor.py
Extracts important fields from Passport:
- passport_number
- surname
- given_name
- nationality
- dob
- expiry_date
- gender
- mrz
"""

import re
from .base_extractor import BaseExtractor


class PassportExtractor(BaseExtractor):
    def extract(self):
        mrz_data = self._parse_mrz()
        passport_num = self._extract_passport_number(mrz_data)
        surname, given_name = self._extract_names(mrz_data)
        dob = self._extract_dob(mrz_data)
        expiry_date = self._extract_expiry(mrz_data)
        gender = self._extract_gender(mrz_data)
        nationality = mrz_data.get("nationality") or ("INDIAN" if "IND" in self.raw_text.upper() else "INDIAN")

        return {
            "document_type": "PASSPORT",
            "passport_number": passport_num,
            "surname": surname,
            "given_name": given_name,
            "nationality": nationality,
            "dob": dob,
            "expiry_date": expiry_date,
            "gender": gender,
            "mrz": mrz_data.get("raw_lines")
        }

    def _parse_mrz(self):
        """
        Search for 44-character MRZ lines:
        Line 1: P<IND[SURNAME]<<[GIVEN_NAMES]<<<<<<...
        Line 2: [PASSPORT_NO][CHECK_DIGIT][IND][DOB_YYMMDD][CHECK][GENDER][EXPIRY_YYMMDD]...
        """
        mrz_lines = []
        for line in self.lines:
            # Clean spaces
            clean = re.sub(r"\s+", "", line).upper()
            if "<" in clean and len(clean) >= 28:
                mrz_lines.append(clean)

        res = {"raw_lines": mrz_lines if mrz_lines else None}
        if len(mrz_lines) >= 2:
            l1, l2 = mrz_lines[0], mrz_lines[1]
            if not l1.startswith("P") and l2.startswith("P"):
                l1, l2 = l2, l1

            # Fix common OCR character confusion in header
            l1_fixed = l1.replace("P<1ND", "P<IND").replace("P<IND5", "P<IND")
            # Parse Line 1: P<IND[SURNAME]<<[GIVEN_NAMES]
            m1 = re.match(r"P<[A-Z0-9]{3}([A-Z0-9<]+)", l1_fixed)
            if m1:
                res["country"] = "IND"
                name_part = m1.group(1)
                parts = name_part.split("<<")
                raw_surname = parts[0].replace("<", " ").strip()
                # Clean OCR digit confusions in surname
                clean_surname = re.sub(r"[^A-Za-z\s]", "", raw_surname).strip()
                if clean_surname:
                    res["surname"] = clean_surname
                if len(parts) > 1:
                    raw_given = parts[1].replace("<", " ").strip()
                    clean_given = re.sub(r"[^A-Za-z\s]", "", raw_given).strip()
                    if clean_given:
                        res["given_name"] = clean_given

            # Parse Line 2: [Pass No: ~8-9 chars][Check][Country 3 chars][DOB: 6 chars][Check][Sex: 1 char][Exp: 6 chars]
            # Example: SP003369<21ND9407015F3409028...
            m2 = re.search(r"([A-Z0-9<]{8,9})<?([A-Z0-9]{3})?([0-9]{6})[0-9]([MF<])([0-9]{6})", l2)
            if m2:
                res["passport_number"] = m2.group(1).replace("<", "")
                res["dob_raw"] = m2.group(3)
                res["gender"] = "FEMALE" if m2.group(4) == "F" else ("MALE" if m2.group(4) == "M" else None)
                res["expiry_raw"] = m2.group(5)

        return res

    def _extract_passport_number(self, mrz_data):
        if mrz_data.get("passport_number"):
            return mrz_data["passport_number"]

        # Indian Passport pattern: 1 capital letter (often P, A, J, K, L, M, S, T, V, Z) + 7 digits
        # Can also have 2 letters + 6-7 digits in some diplomatic/official cards
        pattern = re.compile(r"\b([A-Z]{1,2}[0-9]{7})\b")
        for line in self.lines:
            m = pattern.search(line.upper())
            if m:
                return m.group(1)

        m = pattern.search(self.raw_text.upper())
        if m:
            return m.group(1)

        return None

    def _extract_names(self, mrz_data):
        surname = mrz_data.get("surname")
        given_name = mrz_data.get("given_name")

        surname_kw = re.compile(r"(surname|उप\s*नाम)[:\s]*", re.IGNORECASE)
        given_kw = re.compile(r"(given\s*name|दिया\s*गया\s*नाम)[:\s]*", re.IGNORECASE)

        for idx, line in enumerate(self.lines):
            if not surname and surname_kw.search(line):
                rem = surname_kw.sub("", line).strip(" :/-")
                if rem and self.is_valid_name(rem):
                    surname = rem.upper()
                elif idx + 1 < len(self.lines):
                    cand = self.lines[idx + 1].strip(" :/-")
                    if self.is_valid_name(cand):
                        surname = cand.upper()

            if not given_name and given_kw.search(line):
                rem = given_kw.sub("", line).strip(" :/-")
                if rem and self.is_valid_name(rem):
                    given_name = rem.upper()
                elif idx + 1 < len(self.lines):
                    cand = self.lines[idx + 1].strip(" :/-")
                    if self.is_valid_name(cand):
                        given_name = cand.upper()

        return surname, given_name

    def _extract_dob(self, mrz_data):
        if mrz_data.get("dob_raw"):
            raw = mrz_data["dob_raw"]
            if len(raw) == 6 and raw.isdigit():
                yy = int(raw[:2])
                mm = raw[2:4]
                dd = raw[4:6]
                year = f"19{yy}" if yy > 40 else f"20{yy}"
                return f"{dd}/{mm}/{year}"

        dob_kw = re.compile(r"(date\s*of\s*birth|dob|birth)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if dob_kw.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]

        dates = self.extract_dates()
        if dates:
            return dates[0]

        return None

    def _extract_expiry(self, mrz_data):
        if mrz_data.get("expiry_raw"):
            raw = mrz_data["expiry_raw"]
            if len(raw) == 6 and raw.isdigit():
                yy = int(raw[:2])
                mm = raw[2:4]
                dd = raw[4:6]
                year = f"20{yy:02d}"
                return f"{dd}/{mm}/{year}"

        exp_kw = re.compile(r"(date\s*of\s*expiry|expiry|valid\s*until)", re.IGNORECASE)
        for idx, line in enumerate(self.lines):
            if exp_kw.search(line):
                dates = self.extract_dates(line)
                if dates:
                    return dates[0]
                if idx + 1 < len(self.lines):
                    dates = self.extract_dates(self.lines[idx + 1])
                    if dates:
                        return dates[0]

        dates = self.extract_dates()
        if len(dates) > 1:
            # Expiry date is usually the latest date
            return dates[-1]

        return None

    def _extract_gender(self, mrz_data):
        if mrz_data.get("gender"):
            return mrz_data["gender"]
        return self.extract_gender()
