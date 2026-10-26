"""Conservative Vortex reference decision engine.

This module demonstrates the public invariants that can be implemented without
private domain models: time-admissible evidence, explicit non-action outcomes,
deterministic receipts, and separation of epistemic decision from execution.

It intentionally does NOT invent a domain operator. If evidence is admissible
but no domain operator is supplied, the legal outcome is ABSTAIN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Mapping

LEGAL_NON_ACTION_OUTCOMES = {"PROBE", "WAIT", "ABSTAIN", "HUMAN_REVIEW"}


def _parse_aware_iso8601(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    known_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    provenance_sha256: str | None = None


@dataclass(frozen=True)
class DecisionRequest:
    request_id: str
    information_cutoff: str
    evidence: tuple[EvidenceItem, ...] = ()
    objective: Mapping[str, Any] = field(default_factory=dict)
    constraints: Mapping[str, Any] = field(default_factory=dict)
    mandatory_human_review: bool = False


@dataclass(frozen=True)
class DecisionResult:
    request_id: str
    decision: str
    reason: str
    admitted_evidence_ids: tuple[str, ...]
    rejected_evidence_ids: tuple[str, ...]
    information_cutoff: str
    execution_authority: bool
    receipt_sha256: str


class ReferenceDecisionEngine:
    """Minimal executable reference for public Vortex invariants.

    The engine never grants execution permission. Domain action selection is a
    separate pluggable concern and is deliberately absent from this reference
    layer until a canonical operator contract is migrated and tested.
    """

    def evaluate(self, request: DecisionRequest) -> DecisionResult:
        cutoff = _parse_aware_iso8601(request.information_cutoff)

        admitted: list[str] = []
        rejected: list[str] = []
        for item in request.evidence:
            try:
                known_at = _parse_aware_iso8601(item.known_at)
            except ValueError:
                rejected.append(item.evidence_id)
                continue
            if known_at <= cutoff:
                admitted.append(item.evidence_id)
            else:
                rejected.append(item.evidence_id)

        admitted_ids = tuple(sorted(admitted))
        rejected_ids = tuple(sorted(rejected))

        if request.mandatory_human_review:
            decision = "HUMAN_REVIEW"
            reason = "governance constraint requires explicit human review"
        elif not admitted_ids:
            decision = "WAIT"
            reason = "no time-admissible evidence is available at the information cutoff"
        else:
            decision = "ABSTAIN"
            reason = "time-admissible evidence exists but no canonical domain operator is configured"

        receipt_payload = {
            "schema": "VORTEX_REFERENCE_DECISION_RECEIPT_V1",
            "request_id": request.request_id,
            "information_cutoff": request.information_cutoff,
            "decision": decision,
            "reason": reason,
            "admitted_evidence_ids": admitted_ids,
            "rejected_evidence_ids": rejected_ids,
            "execution_authority": False,
        }

        return DecisionResult(
            request_id=request.request_id,
            decision=decision,
            reason=reason,
            admitted_evidence_ids=admitted_ids,
            rejected_evidence_ids=rejected_ids,
            information_cutoff=request.information_cutoff,
            execution_authority=False,
            receipt_sha256=_canonical_hash(receipt_payload),
        )
