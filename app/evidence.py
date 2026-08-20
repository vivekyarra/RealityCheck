from __future__ import annotations

import hashlib
import re

from app.domain import EvidenceRef

SENSITIVE_PATTERNS = (
    re.compile(r"\b\d{12,19}\b"),
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact(text: str) -> str:
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def make_evidence(
    evidence_id: str, filename: str, text: str, quote: str, span: str = "full document"
) -> EvidenceRef:
    return EvidenceRef(
        id=evidence_id,
        filename=filename,
        sha256=sha256_text(text),
        span=span,
        quote=redact(quote),
    )
