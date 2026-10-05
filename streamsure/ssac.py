from __future__ import annotations
from dataclasses import asdict
from .models import Certificate
import hashlib, json

CANONICAL_EXCLUDE = {"digest"}

def canonical_payload(cert: Certificate) -> bytes:
    d = asdict(cert)
    d["outcome"] = cert.outcome.value
    for k in CANONICAL_EXCLUDE:
        d.pop(k, None)
    return json.dumps(d, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")

def digest_certificate(cert: Certificate) -> str:
    return hashlib.sha256(canonical_payload(cert)).hexdigest()

def seal(cert: Certificate) -> Certificate:
    cert.digest = digest_certificate(cert)
    return cert

def verify(cert: Certificate) -> bool:
    return bool(cert.digest) and cert.digest == digest_certificate(cert)
