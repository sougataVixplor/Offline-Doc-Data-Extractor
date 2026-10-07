"""
classifier.py
Classifies KYC documents into 5 fixed categories:
1. PAN CARD
2. AADHAR CARD
3. DRIVING LICENCE
4. PASSPORT
5. VOTAR CARD
"""

import re
import unicodedata


class KYCClassifier:
    DOC_TYPES = [
        "PAN CARD",
        "AADHAR CARD",
        "DRIVING LICENCE",
        "PASSPORT",
        "VOTAR CARD"
    ]

    # Keyword rules with individual weights
    RULES = {
        "PAN CARD": {
            "keywords": [
                ("income tax department", 4.0),
                ("incometaxdepartment", 4.0),
                ("permanent account number", 4.0),
                ("permanentaccountnumber", 4.0),
                ("govt. of india", 2.0),
                ("govt of india", 2.0),
                ("government of india", 1.5),
                ("father's name", 1.5),
                ("fathers name", 1.5),
                ("signature", 1.0),
                ("pan card", 4.0),
                ("pan", 0.8),
            ],
            "regex": [
                (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE), 4.5), # Standard PAN regex
            ]
        },
        "AADHAR CARD": {
            "keywords": [
                ("unique identification authority", 4.5),
                ("identification authority of india", 4.5),
                ("uidai", 4.0),
                ("aadhaar", 4.0),
                ("aadhar", 4.0),
                ("mera aadhaar", 3.0),
                ("meri pehchan", 3.0),
                ("enrolment no", 2.5),
                ("enrollment no", 2.5),
                ("help@uidai", 3.0),
                ("vid:", 2.0),
                ("government of india", 1.5),
                ("govt of india", 1.5),
                ("male", 0.5),
                ("female", 0.5),
            ],
            "regex": [
                (re.compile(r"\b[2-9][0-9]{3}\s[0-9]{4}\s[0-9]{4}\b"), 4.0),   # 12-digit spaced Aadhaar
                (re.compile(r"\b[2-9][0-9]{11}\b"), 3.0),                       # 12-digit unspaced Aadhaar
            ]
        },
        "DRIVING LICENCE": {
            "keywords": [
                ("driving licence", 4.5),
                ("driving license", 4.5),
                ("motor driving licence", 5.0),
                ("motor vehicle", 3.0),
                ("transport department", 3.5),
                ("union of india", 2.5),
                ("form 7", 3.0),
                ("authorisation to drive", 3.5),
                ("valid till", 2.5),
                ("validity", 1.5),
                ("cov", 1.5),
                ("lmv", 2.5),
                ("mcwg", 3.0),
                ("mcwog", 3.0),
                ("non transport", 2.0),
                ("dl no", 3.5),
                ("dlno", 3.5),
            ],
            "regex": [
                (re.compile(r"\b(dl[-\s]?no|dlno)\b", re.IGNORECASE), 3.5),
                (re.compile(r"\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7}\b", re.IGNORECASE), 4.5), # Modern DL
                (re.compile(r"\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b", re.IGNORECASE), 4.0),
                (re.compile(r"\b[A-Z]{2}[0-9]{13,15}\b", re.IGNORECASE), 3.5),
            ]
        },
        "PASSPORT": {
            "keywords": [
                ("republic of india", 4.0),
                ("passport", 4.5),
                ("bharat ganrajya", 4.0),
                ("given name", 2.5),
                ("surname", 2.5),
                ("nationality", 2.0),
                ("type p", 3.0),
                ("code ind", 3.0),
                ("place of birth", 2.0),
                ("place of issue", 2.0),
                ("date of expiry", 2.0),
                ("p<ind", 5.0),
            ],
            "regex": [
                (re.compile(r"P<IND[A-Z<]+", re.IGNORECASE), 5.0), # MRZ Line 1
                (re.compile(r"\b[A-PR-WYa-pr-wy][1-9][0-9]\s?[0-9]{4}[0-9]\b"), 4.0), # Indian Passport No
                (re.compile(r"[A-Z0-9<]{44}"), 3.5), # 44-char MRZ string
            ]
        },
        "VOTAR CARD": {
            "keywords": [
                ("election commission of india", 5.0),
                ("electioncommissionofindia", 5.0),
                ("elector photo identity card", 5.0),
                ("elector's photo identity card", 5.0),
                ("electors photo identity card", 5.0),
                ("voter identity card", 4.5),
                ("voter", 2.5),
                ("elector's name", 3.0),
                ("electors name", 3.0),
                ("elector name", 3.0),
                ("assembly constituency", 3.0),
                ("parliamentary constituency", 3.0),
                ("epic no", 3.5),
                ("epic", 2.5),
                ("bharat nirvachan ayog", 4.0),
            ],
            "regex": [
                (re.compile(r"\b[A-Z]{3}[0-9]{7}\b"), 4.5), # Modern EPIC 10-char format (3 letters + 7 numbers)
            ]
        }
    }

    def __init__(self, min_confidence=0.35):
        self.min_confidence = min_confidence

    @staticmethod
    def _normalize(text):
        if not text:
            return ""
        # Remove accents and normalize whitespace
        norm = unicodedata.normalize("NFKD", text)
        return " ".join(norm.lower().split())

    def classify(self, text_or_lines):
        """
        Classifies OCR text into one of the 5 KYC types.
        Returns:
        {
            "document_type": "PAN CARD" | ... | "UNKNOWN",
            "confidence": float (0.0 - 1.0),
            "scores": { "PAN CARD": 12.5, ... },
            "evidence": { "PAN CARD": ["income tax department", ...], ... }
        }
        """
        if isinstance(text_or_lines, (list, tuple)):
            raw_text = "\n".join(str(l) for l in text_or_lines)
        else:
            raw_text = str(text_or_lines or "")

        norm_text = self._normalize(raw_text)
        # Also create compressed string without spaces for fused OCR words
        no_space_text = re.sub(r"\s+", "", norm_text)

        scores = {doc_type: 0.0 for doc_type in self.DOC_TYPES}
        evidence = {doc_type: [] for doc_type in self.DOC_TYPES}

        for doc_type, rule in self.RULES.items():
            # Check keywords
            for kw, weight in rule.get("keywords", []):
                norm_kw = self._normalize(kw)
                no_space_kw = re.sub(r"\s+", "", norm_kw)
                
                if norm_kw in norm_text:
                    scores[doc_type] += weight
                    evidence[doc_type].append(f"kw:{kw}")
                elif no_space_kw and len(no_space_kw) > 4 and no_space_kw in no_space_text:
                    scores[doc_type] += (weight * 0.9)
                    evidence[doc_type].append(f"kw_fused:{kw}")

            # Check regex patterns
            for pattern, weight in rule.get("regex", []):
                matches = pattern.findall(raw_text)
                if matches:
                    scores[doc_type] += weight
                    evidence[doc_type].append(f"regex:{pattern.pattern} ({len(matches)} match)")

        # Disambiguate overlapping Govt of India matches:
        # If Aadhaar has "unique identification authority", reduce PAN / Voter overlap
        if "kw:unique identification authority" in evidence["AADHAR CARD"] or "kw:uidai" in evidence["AADHAR CARD"]:
            scores["AADHAR CARD"] += 3.0

        # If Election Commission is present, Voter card has very strong weight
        if any("election commission" in ev for ev in evidence["VOTAR CARD"]):
            scores["VOTAR CARD"] += 3.0

        # Sort scores descending
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_type, top_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

        # Calculate normalized confidence (0 to 1)
        if top_score <= 0.0:
            confidence = 0.0
            predicted_type = "UNKNOWN"
        else:
            # Scale confidence: 8.0+ score gives ~0.95+ confidence
            base_conf = min(top_score / (top_score + 2.5), 0.99)
            # Factor in margin over second best
            margin = (top_score - second_score) / (top_score + 1e-5)
            confidence = round(float(base_conf * (0.6 + 0.4 * margin)), 2)

            if confidence >= self.min_confidence:
                predicted_type = top_type
            else:
                predicted_type = "UNKNOWN"

        return {
            "document_type": predicted_type,
            "confidence": confidence,
            "top_score": round(top_score, 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "evidence": evidence.get(predicted_type, [])
        }
