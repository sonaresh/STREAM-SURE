from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
import time, uuid

class TriState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

class Outcome(str, Enum):
    CERTIFIED = "CERTIFIED"
    PROVISIONAL = "PROVISIONAL"
    WAIT = "WAIT"
    CORRECT = "CORRECT"
    REJECT = "REJECT"

class DecisionClass(int, Enum):
    D0 = 0
    D1 = 1
    D2 = 2
    D3 = 3
    D4 = 4

@dataclass
class Evidence:
    temporal: TriState = TriState.PASS
    contract: TriState = TriState.PASS
    lineage: TriState = TriState.PASS
    freshness: TriState = TriState.PASS
    uncertainty: TriState = TriState.PASS
    invariant: TriState = TriState.PASS
    decision_policy: TriState = TriState.PASS
    details: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("temporal","contract","lineage","freshness","uncertainty","invariant","decision_policy"):
            d[k] = getattr(self, k).value
        return d

@dataclass
class DecisionRequest:
    decision_id: str
    decision_class: DecisionClass
    purpose: str
    # PROVISIONAL is never implicit. A caller must explicitly permit a lower-class
    # fallback, preserving the manuscript rule that required UNKNOWN => WAIT.
    allow_provisional_fallback: bool = False
    max_provisional_class: Optional[int] = None

@dataclass
class DecisionBearingState:
    state_id: str
    state_version: int
    domain: str
    value: Dict[str, Any]
    evidence: Evidence
    event_time_start: float
    event_time_end: float
    required_sources: List[str]
    source_freshness: Dict[str, float]
    source_completeness: Dict[str, bool]
    contract_versions: Dict[str, str]
    producer_versions: Dict[str, str]
    transformation_version: str
    lineage_reference: str
    uncertainty_context: Dict[str, Any]
    previous_certificate: Optional[str] = None

@dataclass
class Certificate:
    certificate_id: str
    state_id: str
    state_version: int
    decision_id: str
    decision_class: int
    outcome: Outcome
    reason_codes: List[str]
    max_permitted_decision_class: Optional[int]
    issued_at: float
    evidence: Dict[str, Any]
    previous_certificate: Optional[str] = None
    supersedes_certificate: Optional[str] = None
    digest: Optional[str] = None

    @staticmethod
    def new(state: DecisionBearingState, req: DecisionRequest, outcome: Outcome,
            reason_codes: List[str], max_permitted_decision_class: Optional[int] = None,
            supersedes_certificate: Optional[str] = None) -> "Certificate":
        return Certificate(
            certificate_id=f"ssac-{uuid.uuid4().hex}",
            state_id=state.state_id,
            state_version=state.state_version,
            decision_id=req.decision_id,
            decision_class=int(req.decision_class),
            outcome=outcome,
            reason_codes=reason_codes,
            max_permitted_decision_class=max_permitted_decision_class,
            issued_at=time.time(),
            evidence=state.evidence.as_dict(),
            previous_certificate=state.previous_certificate,
            supersedes_certificate=supersedes_certificate,
        )
