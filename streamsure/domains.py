from __future__ import annotations
from .models import Evidence, TriState

def finance_invariant(value: dict) -> TriState:
    refund=float(value.get("refund_amount",0)); settled=float(value.get("settled_amount",0))
    return TriState.PASS if refund <= settled else TriState.FAIL

def inventory_invariant(value: dict) -> TriState:
    committed=float(value.get("committed_inventory",0)); available=float(value.get("verified_available_inventory",0))
    return TriState.PASS if committed <= available else TriState.FAIL

def security_invariant(value: dict) -> TriState:
    revoked=bool(value.get("revoked_identity",False)); privileged=bool(value.get("privileged_session",False))
    return TriState.FAIL if revoked and privileged else TriState.PASS

INVARIANTS={"finance":finance_invariant,"inventory":inventory_invariant,"security":security_invariant}

def apply_domain_invariant(domain: str, value: dict, evidence: Evidence) -> Evidence:
    fn=INVARIANTS.get(domain)
    if fn is None:
        evidence.invariant=TriState.UNKNOWN
        evidence.details["invariant_error"]="UNKNOWN_DOMAIN"
    else:
        evidence.invariant=fn(value)
    return evidence
