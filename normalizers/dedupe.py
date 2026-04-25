from __future__ import annotations

import hashlib
import re


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def compute_canonical_hash(title: str | None, company_name: str | None, location: str | None, url: str | None) -> str:
    raw = "|".join([
        _normalize(title),
        _normalize(company_name),
        _normalize(location),
        _normalize(url),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
