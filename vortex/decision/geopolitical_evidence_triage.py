"""Native geopolitical evidence triage inside the existing Sovereign Vortex API.

No network, model inference, provider effects, signing, execution, authorization
or world-event certification occurs in this domain operator. It consumes a
canonical RIG RealitySnapshot, not raw private LMint research artifacts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from vortex.decision.reference_engine import DecisionRequest, DecisionResult
from vortex.decision.seos_adapter import (
    DiagnosticDecisionError,
    _validated_reality_snapshot,
    _validate_decision,
    recompute_decision_hash,
)

DOMAIN = "GLOBAL_GEOPOLITICAL_INTELLIGENCE"
OBJECTIVE_KIND = "GEOPOLITICAL_EVIDENCE_TRIAGE_V1"
ADAPTER_ID = "adapter:vortex:geopolitical-evidence-triage:v1"
VERSION = "1.0.0"
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
CASE_ID = re.compile(r"geo:[a-z0-9][a-z0-9._:-]{2,100}\Z")
GROUP = re.compile(r"[a-z0-9][a-z0-9._:-]{2,100}\Z")
ALLOWED_EVIDENCE_CLASS = {
    "MEDIA_INDEX",
    "OFFICIAL_PRIMARY_RECORD",
    "INDEPENDENT_INCIDENT_RECORD",
}
ALLOWED_EVENT_STATUS = {"MEDIA_MENTION_ONLY", "EVENT_REPORTED", "EVENT_OBSERVED"}
MAX_EVIDENCE = 40


class GeopoliticalDecisionError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise GeopoliticalDecisionError(reason)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GeopoliticalDecisionError("GEO_INVALID_CANONICAL_PAYLOAD") from exc


class GeopoliticalEvidenceTriageAdapter:
    """Converts bounded source evidence into a canonical non-effect decision."""

    def __init__(self, *, now=None):
        self.now = now or (lambda: datetime.now(timezone.utc))

    def build(self, *, request: DecisionRequest, reference_result: DecisionResult) -> dict:
        obj = request.objective
        _require(isinstance(obj, Mapping), "GEO_OBJECTIVE_NOT_OBJECT")
        _require(set(obj) == {"kind", "case_id", "reality_snapshot"},
                 "GEO_OBJECTIVE_FIELDS_INVALID")
        _require(obj.get("kind") == OBJECTIVE_KIND, "GEO_OBJECTIVE_KIND_INVALID")
        case = obj.get("case_id")
        _require(isinstance(case, str) and CASE_ID.fullmatch(case) is not None,
                 "GEO_CASE_ID_INVALID")
        try:
            snapshot = _validated_reality_snapshot(
                obj.get("reality_snapshot"),
                information_cutoff=request.information_cutoff,
            )
        except DiagnosticDecisionError as exc:
            raise GeopoliticalDecisionError("GEO_RIG_SNAPSHOT_REJECT: " + str(exc)) from exc

        _require(reference_result.information_cutoff == request.information_cutoff,
                 "GEO_REFERENCE_CUTOFF_DRIFT")
        _require(reference_result.execution_authority is False,
                 "GEO_EXECUTION_AUTHORITY_FORBIDDEN")
        _require(not reference_result.rejected_evidence_ids,
                 "GEO_FUTURE_OR_INVALID_SOURCE_EVIDENCE")
        _require(0 < len(request.evidence) <= MAX_EVIDENCE,
                 "GEO_EVIDENCE_BOUNDED_REQUIRED")
        ids = [e.evidence_id for e in request.evidence]
        _require(len(set(ids)) == len(ids), "GEO_DUPLICATE_EVIDENCE_ID")
        _require(set(ids) == set(reference_result.admitted_evidence_ids),
                 "GEO_ADMITTED_REFERENCE_SET_MISMATCH")

        refs = {ref["evidence_id"]: ref for ref in snapshot["evidence_refs"]}
        _require(len(refs) == len(snapshot["evidence_refs"]) == len(ids)
                 and set(refs) == set(ids), "GEO_RIG_EVIDENCE_SET_MISMATCH")
        by_group: dict[str, set[str]] = {}
        classes: set[str] = set()
        event_states: set[str] = set()
        for item in request.evidence:
            value = item.payload
            _require(isinstance(value, Mapping) and set(value) == {
                "evidence_class", "correlation_group", "source_ref",
                "event_status", "claim_id",
            }, "GEO_EVIDENCE_FIELDS_INVALID")
            kind = value.get("evidence_class")
            status = value.get("event_status")
            group = value.get("correlation_group")
            ref = value.get("source_ref")
            claim_id = value.get("claim_id")
            _require(kind in ALLOWED_EVIDENCE_CLASS and status in ALLOWED_EVENT_STATUS,
                     "GEO_EVIDENCE_TYPE_INVALID")
            _require(isinstance(group, str) and GROUP.fullmatch(group) is not None,
                     "GEO_CORRELATION_GROUP_INVALID")
            _require(isinstance(ref, str) and 5 <= len(ref) <= 250
                     and not any(ord(c) < 32 for c in ref),
                     "GEO_SOURCE_REF_INVALID")
            _require(isinstance(claim_id, str) and 3 <= len(claim_id) <= 128,
                     "GEO_CLAIM_ID_INVALID")
            digest = sha256(_canonical(value)).hexdigest()
            r = refs[item.evidence_id]
            _require(HEX64.fullmatch(item.provenance_sha256 or "") is not None,
                     "GEO_MISSING_SHA256")
            _require(digest == item.provenance_sha256 == r["payload_hash"],
                     "GEO_PAYLOAD_CUSTODY_MISMATCH")
            _require(item.known_at == r["known_at"], "GEO_KNOWN_AT_DRIFT")
            _require(ref == r["provenance_ref"], "GEO_SOURCE_CUSTODY_DRIFT")
            classes.add(kind)
            event_states.add(status)
            by_group.setdefault(group, set()).add(item.evidence_id)

        # Distinct correlation groups are NOT certified independent sources.
        # Even multiple real-event report claims cannot authorize effects.
        groups = len(by_group)
        if request.mandatory_human_review:
            disposition = "HUMAN_REVIEW"
            reasons = ["FOUNDER_OR_POLICY_HUMAN_REVIEW_REQUIRED"]
        elif groups < 2 or classes == {"MEDIA_INDEX"}:
            disposition = "PROBE"
            reasons = ["UNVERIFIED_OR_CORRELATED_GEOPOLITICAL_EVIDENCE"]
        elif "OFFICIAL_PRIMARY_RECORD" in classes and (
            "INDEPENDENT_INCIDENT_RECORD" in classes
        ) and "EVENT_OBSERVED" in event_states:
            disposition = "HUMAN_REVIEW"
            reasons = ["MULTI_SOURCE_EVENT_CLAIM_REQUIRES_EXPERT_ADJUDICATION"]
        else:
            disposition = "PROBE"
            reasons = ["INSUFFICIENT_INDEPENDENT_WORLD_EVENT_ADJUDICATION"]

        created = self.now()
        _require(isinstance(created, datetime) and created.tzinfo is not None,
                 "GEO_VERIFIER_CLOCK_INVALID")
        created_at = created.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        digest = sha256(_canonical({
            "request_id": request.request_id,
            "snapshot_hash": snapshot["snapshot_hash"],
            "information_cutoff": request.information_cutoff,
            "case_id": case,
        })).hexdigest()
        artifact = {
            "schema_version": "1.0.0",
            "decision_id": "decision:vortex:geo:" + digest[:32],
            "decision_authority": "SOVEREIGN_VORTEX",
            "decision_request_id": request.request_id,
            "domain": DOMAIN,
            "subject": {
                "subject_type": "geopolitical_case",
                "subject_id": case,
                "tenant_id": "customer-zero",
            },
            "information_cutoff": request.information_cutoff,
            "created_at": created_at,
            "inputs": {
                "reality_snapshot_ref": {
                    "snapshot_id": snapshot["snapshot_id"],
                    "snapshot_hash": snapshot["snapshot_hash"],
                    "information_cutoff": snapshot["information_cutoff"],
                },
                "forecast_refs": [],
                "additional_artifact_refs": [],
            },
            "evidence_admission": {
                "admitted_evidence_ids": list(reference_result.admitted_evidence_ids),
                "rejected_evidence_ids": [],
            },
            "epistemic_disposition": disposition,
            "recommended_action": None,
            "reason": "RIG snapshot-bound geopolitical evidence triage; no independent world-event certification.",
            "reason_codes": reasons + [
                "RIG_SOURCE_BOUND", "GEO_INFORMATION_CUTOFF_ENFORCED", "NO_EXECUTION",
            ],
            "uncertainty": {
                "semantics": "Source correlation groups are not independent validation or calibrated event probabilities.",
                "dimensions": {
                    "observed_correlation_group_count": groups,
                    "real_world_events_independently_adjudicated": 0,
                },
                "extensions": {
                    "real_world_truth_certified": False,
                    "calibrated_confidence": False,
                    "media_mentions_are_events": False,
                },
            },
            "engine": {
                "engine_id": "vortex-native-geopolitical-evidence-triage",
                "engine_version": VERSION,
                "policy_version": "geo-evidence-triage-v1",
                "adapter_id": ADAPTER_ID,
                "adapter_version": VERSION,
                "extensions": {
                    "reference_receipt_sha256": reference_result.receipt_sha256,
                },
            },
            "risk_assessment": None,
            "execution_authority": False,
            "decision_hash": "0" * 64,
            "integrity": {
                "assurance_level": "HASH_ONLY",
                "algorithm": "SHA-256",
                "body_hash": "0" * 64,
                "key_id": None,
                "signature": None,
            },
            "proof_ref": None,
            "extensions": {
                "case_id": case,
                "world_event_corroboration_certified": False,
                "provider_effects": False,
            },
        }
        body_hash = recompute_decision_hash(artifact)
        artifact["decision_hash"] = body_hash
        artifact["integrity"]["body_hash"] = body_hash
        try:
            _validate_decision(artifact)
        except DiagnosticDecisionError as exc:
            raise GeopoliticalDecisionError("GEO_SEOS_DECISION_SCHEMA_REJECT: " + str(exc)) from exc
        return artifact
