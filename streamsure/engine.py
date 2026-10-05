from __future__ import annotations
from .models import TriState, Outcome, DecisionRequest, DecisionBearingState, Certificate, DecisionClass

ALL_PREDICATES = ("temporal","contract","lineage","freshness","uncertainty","invariant","decision_policy")

# Default decision profiles. Enterprises can externalize these later; the prototype keeps them explicit and deterministic.
REQUIRED_BY_CLASS = {
    DecisionClass.D0: ("contract","invariant","decision_policy"),
    DecisionClass.D1: ("temporal","contract","lineage","invariant","decision_policy"),
    DecisionClass.D2: ALL_PREDICATES,
    DecisionClass.D3: ALL_PREDICATES,
    DecisionClass.D4: ALL_PREDICATES,
}

class CertificationEngine:
    """Deterministic implementation of STREAM-SURE decision-relative three-valued semantics."""

    def certify(self, state: DecisionBearingState, req: DecisionRequest,
                invalidates_previous: bool = False,
                supersedes_certificate: str | None = None) -> Certificate:
        if invalidates_previous:
            return Certificate.new(state, req, Outcome.CORRECT,
                                   ["PREVIOUS_CERTIFICATE_INVALIDATED"],
                                   supersedes_certificate=supersedes_certificate)

        values = {name: getattr(state.evidence, name) for name in ALL_PREDICATES}
        required = REQUIRED_BY_CLASS[req.decision_class]
        failed = [k.upper() + "_FAIL" for k in required if values[k] == TriState.FAIL]
        unknown = [k.upper() + "_UNKNOWN" for k in required if values[k] == TriState.UNKNOWN]

        if failed:
            return Certificate.new(state, req, Outcome.REJECT, failed)

        if unknown:
            # Canonical STREAM-SURE semantics: a required UNKNOWN blocks the
            # requested decision. PROVISIONAL is allowed only when the decision
            # policy explicitly opts into a lower-consequence fallback.
            if req.allow_provisional_fallback:
                lower = self._highest_passing_lower_class(req.decision_class, values)
                if lower is not None:
                    if req.max_provisional_class is not None:
                        lower = DecisionClass(min(int(lower), int(req.max_provisional_class)))
                        if not all(values[k] == TriState.PASS for k in REQUIRED_BY_CLASS[lower]):
                            return Certificate.new(state, req, Outcome.WAIT, unknown)
                    return Certificate.new(state, req, Outcome.PROVISIONAL, unknown, int(lower))
            return Certificate.new(state, req, Outcome.WAIT, unknown)

        return Certificate.new(state, req, Outcome.CERTIFIED,
                               ["ALL_REQUIRED_PREDICATES_PASS"], int(req.decision_class))

    @staticmethod
    def _highest_passing_lower_class(requested: DecisionClass, values: dict[str, TriState]) -> DecisionClass | None:
        for raw in range(int(requested)-1, -1, -1):
            dc=DecisionClass(raw)
            required=REQUIRED_BY_CLASS[dc]
            if all(values[k] == TriState.PASS for k in required):
                return dc
        return None
