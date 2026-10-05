from __future__ import annotations
from .engine import CertificationEngine
from .models import *
from .ssac import seal
from .store import SQLiteStore
from .domains import apply_domain_invariant


class StreamSureService:
    def __init__(self, db_path: str = "streamsure.db"):
        self.engine = CertificationEngine(); self.store = SQLiteStore(db_path); self._closed = False

    def _certify_no_persist(self, state: DecisionBearingState, req: DecisionRequest) -> Certificate:
        state.evidence = apply_domain_invariant(state.domain, state.value, state.evidence)
        return seal(self.engine.certify(state, req))

    def certify(self, state: DecisionBearingState, req: DecisionRequest) -> Certificate:
        cert = self._certify_no_persist(state, req)
        self.store.save_certificate(cert)
        return cert

    def certify_batch(self, items: list[tuple[DecisionBearingState, DecisionRequest]]) -> list[Certificate]:
        """Evaluate multiple independent requests and persist in one transaction."""
        certs = [self._certify_no_persist(state, req) for state, req in items]
        self.store.save_certificates(certs)
        return certs

    def repair(self, old_certificate_id: str, corrected_state: DecisionBearingState,
               req: DecisionRequest) -> tuple[Certificate, list[str]]:
        old = self.store.get_certificate(old_certificate_id)
        if old is None: raise KeyError(f"Unknown certificate {old_certificate_id}")
        corrected_state.previous_certificate = old_certificate_id
        corrected_state.evidence = apply_domain_invariant(corrected_state.domain, corrected_state.value, corrected_state.evidence)
        correction = seal(self.engine.certify(corrected_state, req, invalidates_previous=True, supersedes_certificate=old_certificate_id))
        self.store.save_certificate(correction)
        self.store.register_repair(old_certificate_id, correction.certificate_id, correction.issued_at)
        return correction, self.store.consumers(old_certificate_id)

    def close(self):
        if self._closed: return
        self.store.close(); self._closed = True
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): self.close(); return False
