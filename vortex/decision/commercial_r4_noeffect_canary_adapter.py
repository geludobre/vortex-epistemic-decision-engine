from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from vortex.decision.reference_engine import DecisionRequest, DecisionResult
from vortex.decision.seos_adapter import (
    DiagnosticDecisionError,
    _validate_decision,
    _validated_reality_snapshot,
    recompute_decision_hash,
)

SEOS_SCHEMA_VERSION = "1.0.0"
OBJECTIVE_KIND = "COMMERCIAL_R4_NOEFFECT_CANARY_V1"
ADAPTER_ID = "adapter:vortex:commercial-r4-noeffect-canary:v1"
ADAPTER_VERSION = "1.0.0"
ENGINE_ID = "vortex-reference-commercial-r4-noeffect-canary"
ENGINE_VERSION = "1.0.0"
POLICY_VERSION = "vortex-commercial-r4-noeffect-canary-policy-v1"
TOOL_NAME = "aug_commercial_effect"
ACTION_TYPE = "SEND_COMMERCIAL_EMAIL"
DOMAIN = "COMMERCIAL_REVENUE"
TENANT = "customer-zero"
EFFECT_CLASS = "CUSTOMER_COMMUNICATION"
RESOURCE_REF = "commercial:customer-zero/canary/r4-noeffect-20260927/event-2"
RECIPIENT = "buyer@example.invalid"
SUBJECT = "FinBridge Commercial R4 no-effect canary"
CONTENT_REF = "draft:commercial-r4-noeffect-20260927-2"


class CommercialR4NoEffectCanaryDecisionError(RuntimeError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_action_input() -> dict[str, Any]:
    return {
        "domain": DOMAIN,
        "tenantId": TENANT,
        "effectClass": EFFECT_CLASS,
        "actionType": ACTION_TYPE,
        "resourceRefs": [RESOURCE_REF],
        "payload": {
            "recipient": RECIPIENT,
            "subject": SUBJECT,
            "contentRef": CONTENT_REF,
        },
        "executor": "SOVEREIGN_AGENTOPS",
        "directProviderExecution": False,
    }


def canonical_action_input_hash(arguments: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json(dict(arguments)))


def _objective(request: DecisionRequest) -> dict[str, Any]:
    objective = request.objective
    if not isinstance(objective, Mapping):
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: objective must be an object"
        )
    required = {
        "kind",
        "tenant_id",
        "tool_name",
        "action_type",
        "resource_refs",
        "arguments",
        "reality_snapshot",
    }
    if set(objective) != required:
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: objective fields are not exact"
        )
    if objective.get("kind") != OBJECTIVE_KIND:
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: objective kind mismatch"
        )
    if objective.get("tenant_id") != TENANT:
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: tenant must be customer-zero"
        )
    if objective.get("tool_name") != TOOL_NAME or objective.get("action_type") != ACTION_TYPE:
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: tool/action mismatch"
        )
    if objective.get("resource_refs") != [RESOURCE_REF]:
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: resource scope mismatch"
        )
    arguments = objective.get("arguments")
    if arguments != canonical_action_input():
        raise CommercialR4NoEffectCanaryDecisionError(
            "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT: canonical action input mismatch"
        )
    try:
        snapshot = _validated_reality_snapshot(
            objective.get("reality_snapshot"),
            information_cutoff=request.information_cutoff,
        )
    except DiagnosticDecisionError as exc:
        raise CommercialR4NoEffectCanaryDecisionError(
            str(exc).replace(
                "DIAGNOSTIC_OBJECTIVE_REJECT",
                "COMMERCIAL_R4_NOEFFECT_OBJECTIVE_REJECT",
            )
        ) from exc
    return {
        "arguments": dict(arguments),
        "canonical_input_hash": canonical_action_input_hash(arguments),
        "reality_snapshot_ref": {
            "snapshot_id": snapshot["snapshot_id"],
            "snapshot_hash": snapshot["snapshot_hash"],
            "information_cutoff": snapshot["information_cutoff"],
        },
        "snapshot_evidence": {
            item["evidence_id"]: item for item in snapshot["evidence_refs"]
        },
    }


class CommercialR4NoEffectCanaryDecisionAdapter:
    """One exact non-deliverable Commercial integration canary recommendation.

    This adapter is epistemic only. It cannot approve, authorize, execute,
    deliver email, mutate provider/customer state, or grant execution authority.
    """

    def __init__(self, *, now=None) -> None:
        self.now = now or (lambda: datetime.now(timezone.utc))

    def build(
        self,
        *,
        request: DecisionRequest,
        reference_result: DecisionResult,
    ) -> dict[str, Any]:
        objective = _objective(request)
        if request.mandatory_human_review is not True:
            raise CommercialR4NoEffectCanaryDecisionError(
                "COMMERCIAL_R4_NOEFFECT_REJECT: mandatory_human_review must be true"
            )
        if not reference_result.admitted_evidence_ids:
            raise CommercialR4NoEffectCanaryDecisionError(
                "COMMERCIAL_R4_NOEFFECT_REJECT: time-admissible evidence is required"
            )
        if reference_result.rejected_evidence_ids:
            raise CommercialR4NoEffectCanaryDecisionError(
                "COMMERCIAL_R4_NOEFFECT_REJECT: rejected/future evidence is forbidden"
            )
        if reference_result.information_cutoff != request.information_cutoff:
            raise CommercialR4NoEffectCanaryDecisionError(
                "COMMERCIAL_R4_NOEFFECT_REJECT: information cutoff drift"
            )
        if reference_result.execution_authority is not False:
            raise CommercialR4NoEffectCanaryDecisionError(
                "CONSTITUTION_REJECT: Vortex unexpectedly has execution authority"
            )

        request_evidence = {item.evidence_id: item for item in request.evidence}
        for evidence_id in reference_result.admitted_evidence_ids:
            ref = objective["snapshot_evidence"].get(evidence_id)
            item = request_evidence.get(evidence_id)
            if ref is None or item is None:
                raise CommercialR4NoEffectCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence missing from snapshot/request"
                )
            if item.provenance_sha256 != ref["payload_hash"]:
                raise CommercialR4NoEffectCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: evidence payload hash mismatch"
                )
            if item.known_at != ref["known_at"]:
                raise CommercialR4NoEffectCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: evidence known_at mismatch"
                )

        created_at = self.now().astimezone(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
        decision_id = "decision:vortex:commercial-r4-noeffect:" + _sha256(
            _canonical_json(
                {
                    "request_id": request.request_id,
                    "canonical_input_hash": objective["canonical_input_hash"],
                    "information_cutoff": request.information_cutoff,
                }
            )
        )[:32]

        artifact: dict[str, Any] = {
            "schema_version": SEOS_SCHEMA_VERSION,
            "decision_id": decision_id,
            "decision_authority": "SOVEREIGN_VORTEX",
            "decision_request_id": request.request_id,
            "domain": DOMAIN,
            "subject": {
                "subject_type": "commercial_canary",
                "subject_id": "r4-noeffect-20260927-event-2",
                "tenant_id": TENANT,
                "extensions": {
                    "canary_only": True,
                    "human_approval_required": True,
                    "recipient_class": "example.invalid",
                    "provider_effect_forbidden": True,
                },
            },
            "information_cutoff": request.information_cutoff,
            "created_at": created_at,
            "inputs": {
                "reality_snapshot_ref": objective["reality_snapshot_ref"],
                "forecast_refs": [],
                "additional_artifact_refs": [],
            },
            "evidence_admission": {
                "admitted_evidence_ids": list(reference_result.admitted_evidence_ids),
                "rejected_evidence_ids": list(reference_result.rejected_evidence_ids),
            },
            "epistemic_disposition": "ACTION_RECOMMENDATION",
            "recommended_action": {
                "action_type": ACTION_TYPE,
                "resource_refs": [RESOURCE_REF],
                "canonical_input_hash": objective["canonical_input_hash"],
                "extensions": {
                    "mcp_tool": TOOL_NAME,
                    "canary_only": True,
                    "human_approval_required": True,
                    "recipient_class": "example.invalid",
                    "direct_provider_execution": False,
                    "max_attempts": 1,
                },
            },
            "reason": (
                "Time-admissible RIG-bound evidence supports exactly one bounded "
                "Commercial R4 integration canary to a reserved non-deliverable address. "
                "Vortex recommends the action and grants no execution authority."
            ),
            "reason_codes": [
                "TIME_ADMISSIBLE",
                "RIG_SNAPSHOT_BOUND",
                "COMMERCIAL_R4_NOEFFECT_CANARY",
                "NON_DELIVERABLE_RECIPIENT",
                "HUMAN_APPROVAL_REQUIRED",
                "PROVIDER_EFFECT_FORBIDDEN",
            ],
            "uncertainty": {
                "semantics": "Bounded integration-canary recommendation only.",
                "dimensions": {},
                "extensions": {
                    "reference_decision": reference_result.decision,
                    "mandatory_human_review": True,
                },
            },
            "engine": {
                "engine_id": ENGINE_ID,
                "engine_version": ENGINE_VERSION,
                "policy_version": POLICY_VERSION,
                "adapter_id": ADAPTER_ID,
                "adapter_version": ADAPTER_VERSION,
                "extensions": {
                    "reference_decision": reference_result.decision,
                    "reference_receipt_sha256": reference_result.receipt_sha256,
                },
            },
            "risk_assessment": {
                "utility": None,
                "catastrophe_probability": None,
                "catastrophe_threshold": None,
                "admissible": True,
                "extensions": {
                    "canary_only": True,
                    "non_deliverable_recipient": True,
                    "human_approval_required": True,
                    "provider_effect_forbidden": True,
                },
            },
            "execution_authority": False,
            "decision_hash": "0" * 64,
            "integrity": {
                "assurance_level": "HASH_ONLY",
                "algorithm": "SHA-256",
                "body_hash": "0" * 64,
                "key_id": None,
                "signature": None,
                "extensions": {
                    "profile": "SEOS-CJ-1",
                    "canary_only": True,
                    "human_approval_required": True,
                },
            },
            "proof_ref": None,
            "extensions": {
                "tool_name": TOOL_NAME,
                "canary_only": True,
                "human_approval_required": True,
            },
        }
        digest = recompute_decision_hash(artifact)
        artifact["decision_hash"] = digest
        artifact["integrity"]["body_hash"] = digest
        try:
            _validate_decision(artifact)
        except DiagnosticDecisionError as exc:
            raise CommercialR4NoEffectCanaryDecisionError(str(exc)) from exc
        return artifact
