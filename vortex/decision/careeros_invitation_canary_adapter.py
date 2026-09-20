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
OBJECTIVE_KIND = "CAREEROS_INVITATION_CANARY_V1"
ADAPTER_ID = "adapter:vortex:careeros-invitation-canary:v1"
ADAPTER_VERSION = "1.0.0"
ENGINE_ID = "vortex-reference-careeros-invitation-canary"
ENGINE_VERSION = "1.0.0"
POLICY_VERSION = "vortex-careeros-invitation-canary-policy-v1"
TOOL_NAME = "aug_business_effect"
ACTION_TYPE = "career.invitation.create_and_enqueue"
CUSTOMER_ZERO_TENANT = "customer-zero"
CANARY_RECIPIENT = "customer-zero-test@example.invalid"
CANARY_ROLE = "member"


class CareerOsInvitationCanaryDecisionError(RuntimeError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_action_input_hash(arguments: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json(dict(arguments)))


def _required_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CareerOsInvitationCanaryDecisionError(
            f"CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: {field} is required"
        )
    if value != value.strip():
        raise CareerOsInvitationCanaryDecisionError(
            f"CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: {field} must be canonical trimmed text"
        )
    return value


def _validated_arguments(
    value: Any,
    *,
    expected_resource: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: arguments must be an object"
        )
    args = dict(value)
    required = {
        "action",
        "resource_ref",
        "sponsor_user_id",
        "recipient_email",
        "role",
    }
    if set(args) != required:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: arguments must contain exactly "
            + str(sorted(required))
        )

    if args.get("action") != ACTION_TYPE:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: action must be career.invitation.create_and_enqueue"
        )
    if args.get("resource_ref") != expected_resource:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: resource_ref must bind the exact workspace invitation surface"
        )

    _required_str(args.get("sponsor_user_id"), "arguments.sponsor_user_id")
    recipient = _required_str(args.get("recipient_email"), "arguments.recipient_email")
    if recipient != recipient.lower() or recipient != CANARY_RECIPIENT:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: recipient_email must be the reserved non-deliverable canary address"
        )
    if args.get("role") != CANARY_ROLE:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: role must be exactly member"
        )

    canonical_action_input_hash(args)
    return args


def _objective(request: DecisionRequest) -> dict[str, Any]:
    objective = request.objective
    if not isinstance(objective, Mapping):
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: objective must be an object"
        )
    required = {
        "kind",
        "tenant_id",
        "workspace_id",
        "tool_name",
        "action_type",
        "resource_refs",
        "arguments",
        "reality_snapshot",
    }
    if set(objective) != required:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: objective must contain exactly "
            + str(sorted(required))
        )
    if objective.get("kind") != OBJECTIVE_KIND:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: unsupported objective kind"
        )
    if objective.get("tool_name") != TOOL_NAME:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: tool_name must be aug_business_effect"
        )
    if objective.get("action_type") != ACTION_TYPE:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: unsupported action_type"
        )

    tenant_id = _required_str(objective.get("tenant_id"), "tenant_id")
    if tenant_id != CUSTOMER_ZERO_TENANT:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: only customer-zero is eligible in v1"
        )
    workspace_id = _required_str(objective.get("workspace_id"), "workspace_id")
    expected_resource = f"careeros:{tenant_id}/workspace/{workspace_id}/invitation"
    resources = objective.get("resource_refs")
    if resources != [expected_resource]:
        raise CareerOsInvitationCanaryDecisionError(
            "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT: resource_refs must bind the exact workspace invitation surface"
        )

    arguments = _validated_arguments(
        objective.get("arguments"),
        expected_resource=expected_resource,
    )
    try:
        snapshot = _validated_reality_snapshot(
            objective.get("reality_snapshot"),
            information_cutoff=request.information_cutoff,
        )
    except DiagnosticDecisionError as exc:
        raise CareerOsInvitationCanaryDecisionError(
            str(exc).replace(
                "DIAGNOSTIC_OBJECTIVE_REJECT",
                "CAREEROS_INVITATION_CANARY_OBJECTIVE_REJECT",
            )
        ) from exc

    input_hash = canonical_action_input_hash(arguments)
    snapshot_evidence = {
        item["evidence_id"]: item for item in snapshot["evidence_refs"]
    }
    return {
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "resource_refs": [expected_resource],
        "canonical_input_hash": input_hash,
        "arguments": arguments,
        "reality_snapshot_ref": {
            "snapshot_id": snapshot["snapshot_id"],
            "snapshot_hash": snapshot["snapshot_hash"],
            "information_cutoff": snapshot["information_cutoff"],
        },
        "snapshot_evidence": snapshot_evidence,
    }


class CareerOsInvitationCanaryDecisionAdapter:
    """Bounded Vortex operator for exactly one non-deliverable CareerOS invitation canary.

    The adapter may recommend the exact canary action after time-admissible,
    RIG-bound evidence is present. It never grants execution or approval
    authority. AuthorizationAuthority plus a one-time ApprovalProof remain
    mandatory downstream.
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
            raise CareerOsInvitationCanaryDecisionError(
                "CAREEROS_INVITATION_CANARY_REJECT: mandatory_human_review must be true"
            )
        if not reference_result.admitted_evidence_ids:
            raise CareerOsInvitationCanaryDecisionError(
                "CAREEROS_INVITATION_CANARY_REJECT: at least one time-admissible evidence item is required"
            )
        if reference_result.rejected_evidence_ids:
            raise CareerOsInvitationCanaryDecisionError(
                "CAREEROS_INVITATION_CANARY_REJECT: rejected/future evidence makes the business-effect canary ineligible"
            )
        if reference_result.information_cutoff != request.information_cutoff:
            raise CareerOsInvitationCanaryDecisionError(
                "CAREEROS_INVITATION_CANARY_REJECT: reference engine cutoff drift"
            )
        if reference_result.execution_authority is not False:
            raise CareerOsInvitationCanaryDecisionError(
                "CONSTITUTION_REJECT: reference engine unexpectedly has execution authority"
            )

        request_evidence = {item.evidence_id: item for item in request.evidence}
        snapshot_evidence = objective["snapshot_evidence"]
        for evidence_id in reference_result.admitted_evidence_ids:
            if evidence_id not in snapshot_evidence:
                raise CareerOsInvitationCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from RealitySnapshot"
                )
            item = request_evidence.get(evidence_id)
            if item is None:
                raise CareerOsInvitationCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from request"
                )
            ref = snapshot_evidence[evidence_id]
            if item.provenance_sha256 != ref["payload_hash"]:
                raise CareerOsInvitationCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: payload hash differs from RealitySnapshot"
                )
            try:
                item_known = datetime.fromisoformat(item.known_at.replace("Z", "+00:00"))
                ref_known = datetime.fromisoformat(ref["known_at"].replace("Z", "+00:00"))
            except ValueError as exc:
                raise CareerOsInvitationCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: invalid known_at timestamp"
                ) from exc
            if item_known != ref_known:
                raise CareerOsInvitationCanaryDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: known_at differs from RealitySnapshot"
                )

        created_at = self.now().astimezone(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
        decision_id_material = {
            "profile": OBJECTIVE_KIND,
            "request_id": request.request_id,
            "workspace_id": objective["workspace_id"],
            "canonical_input_hash": objective["canonical_input_hash"],
            "information_cutoff": request.information_cutoff,
        }
        decision_id = "decision:vortex:careeros-invitation-canary:" + _sha256(
            _canonical_json(decision_id_material)
        )[:32]

        artifact: dict[str, Any] = {
            "schema_version": SEOS_SCHEMA_VERSION,
            "decision_id": decision_id,
            "decision_authority": "SOVEREIGN_VORTEX",
            "decision_request_id": request.request_id,
            "domain": "careeros_invitation_canary",
            "subject": {
                "subject_type": "workspace",
                "subject_id": objective["workspace_id"],
                "tenant_id": objective["tenant_id"],
                "extensions": {
                    "canary_only": True,
                    "human_approval_required": True,
                    "recipient_class": "example.invalid",
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
                "resource_refs": objective["resource_refs"],
                "canonical_input_hash": objective["canonical_input_hash"],
                "extensions": {
                    "mcp_tool": TOOL_NAME,
                    "canary_only": True,
                    "human_approval_required": True,
                    "recipient_class": "example.invalid",
                },
            },
            "reason": (
                "Time-admissible RIG-bound evidence supports exactly one bounded "
                "CareerOS invitation canary to the reserved non-deliverable recipient. "
                "Vortex recommends the action but grants no execution or approval authority."
            ),
            "reason_codes": [
                "TIME_ADMISSIBLE",
                "RIG_SNAPSHOT_BOUND",
                "CAREEROS_INVITATION_CANARY",
                "NON_DELIVERABLE_RECIPIENT",
                "HUMAN_APPROVAL_REQUIRED",
            ],
            "uncertainty": {
                "semantics": (
                    "This is a bounded integration canary recommendation. Human approval "
                    "is an independent authorization precondition and the recipient is "
                    "reserved for non-delivery."
                ),
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
            raise CareerOsInvitationCanaryDecisionError(str(exc)) from exc
        return artifact
