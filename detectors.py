# detectors.py
import re
import hmac
import hashlib
from typing import List, Dict, Tuple

# ---------- Regex patterns (deterministic, high precision) ----------
PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # US SSN: 3-2-4 (loose)
    "SSN": re.compile(r"\b(?!000|666|9\d{2})(\d{3})[- ]?(?!00)(\d{2})[- ]?(?!0000)(\d{4})\b"),
    # Credit Card (simple Luhn-like formats)
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    # Phone (loose)
    "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"),
    # IPv4
    "IPV4": re.compile(r"\b(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d?\d)){3}\b"),
}

# ---------- Helper functions ----------
def run_regex_detectors(text: str) -> List[Dict]:
    findings = []
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            findings.append({
                "type": name,
                "span": (m.start(), m.end()),
                "text": m.group(0),
                "confidence": 0.99,
                "source": "regex"
            })
    return findings

# ---------- Pseudonymization / reversible tokenization ----------
def deterministic_pseudonymize(secret_key: str, text: str) -> str:
    """
    Deterministic pseudonymization using HMAC-SHA256.
    Returns hex digest truncated for readability.
    """
    if text is None:
        return None
    digest = hmac.new(secret_key.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"__PSEUDO_{digest[:16]}__"

def redact_spans(text: str, spans: List[Tuple[int,int]], mask: str = "[REDACTED]") -> str:
    """
    Given original text and ordered spans, produce redacted text.
    Spans must be non-overlapping and sorted.
    """
    if not spans:
        return text
    out = []
    last = 0
    for s, e in spans:
        out.append(text[last:s])
        out.append(mask)
        last = e
    out.append(text[last:])
    return "".join(out)
