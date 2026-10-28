from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from vortex.decision.reference_engine import DecisionRequest, DecisionResult
from vortex.decision.cognitive_adapter import (
    COGNITIVE_ACTION_TYPE,
    COGNITIVE_PROFILE,
    COGNITIVE_TOOL,
    CUSTOMER_ZERO_TENANT,
    CognitiveDecisionError,
    _validated_dispatch_arguments,
    _validated_snapshot,
    canonical_action_input_hash,
)
from vortex.decision.seos_adapter import (
    DiagnosticDecisionError,
    _validate_decision,
    recompute_decision_hash,
)

SEOS_SCHEMA_VERSION = "1.0.0"
HITL_OBJECTIVE_KIND = "ADO_HITL_COGNITIVE_DISPATCH_V1"
ADAPTER_ID = "adapter:vortex:agentops-hitl-cognitive:v1"
ADAPTER_VERSION = "1.0.0"
ENGINE_ID = "vortex-reference-hitl-cognitive-operator"
ENGINE_VERSION = "1.0.0"
POLICY_VERSION = "vortex-ado-hitl-cognitive-policy-v1"


class HitlCognitiveDecisionError(RuntimeError):
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


def _required_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HitlCognitiveDecisionError(
            f"HITL_COGNITIVE_OBJECTIVE_REJECT: {field} is required"
        )
    if value != value.strip():
        raise HitlCognitiveDecisionError(
            f"HITL_COGNITIVE_OBJECTIVE_REJECT: {field} must be canonical trimmed text"
        )
    return value


def _objective(request: DecisionRequest) -> dict[str, Any]:
    objective = request.objective
    if not isinstance(objective, Mapping):
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: objective must be an object"
        )
    required = {
        "kind",
        "cognitive_profile",
        "tenant_id",
        "agent_id",
        "tool_name",
        "action_type",
        "resource_refs",
        "dispatch_arguments",
        "reality_snapshot",
    }
    if set(objective) != required:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: objective must contain exactly "
            + str(sorted(required))
        )
    if objective.get("kind") != HITL_OBJECTIVE_KIND:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: unsupported objective kind"
        )
    if objective.get("cognitive_profile") != COGNITIVE_PROFILE:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: unsupported cognitive profile"
        )
    if objective.get("tool_name") != COGNITIVE_TOOL:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: tool_name must be aug_agent_dispatch"
        )
    if objective.get("action_type") != COGNITIVE_ACTION_TYPE:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: action_type must be ado.dispatch"
        )

    tenant_id = _required_str(objective.get("tenant_id"), "tenant_id")
    if tenant_id != CUSTOMER_ZERO_TENANT:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: only customer-zero is eligible in v1"
        )
    agent_id = _required_str(objective.get("agent_id"), "agent_id")
    resources = objective.get("resource_refs")
    expected_resource = f"ado:{tenant_id}/hitl/agent/{agent_id}"
    if resources != [expected_resource]:
        raise HitlCognitiveDecisionError(
            "HITL_COGNITIVE_OBJECTIVE_REJECT: resource_refs must bind the exact HITL agent"
        )

    try:
        dispatch_arguments = _validated_dispatch_arguments(
            objective.get("dispatch_arguments"),
            expected_agent_id=agent_id,
        )
        snapshot = _validated_snapshot(
            objective.get("reality_snapshot"),
            information_cutoff=request.information_cutoff,
        )
    except CognitiveDecisionError as exc:
        raise HitlCognitiveDecisionError(
            str(exc).replace("COGNITIVE_OBJECTIVE_REJECT", "HITL_COGNITIVE_OBJECTIVE_REJECT")
        ) from exc

    input_hash = canonical_action_input_hash(dispatch_arguments)
    snapshot_evidence = {
        item["evidence_id"]: item for item in snapshot["evidence_refs"]
    }
    return {
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "resource_refs": [expected_resource],
        "canonical_input_hash": input_hash,
        "dispatch_arguments": dispatch_arguments,
        "reality_snapshot_ref": {
            "snapshot_id": snapshot["snapshot_id"],
            "snapshot_hash": snapshot["snapshot_hash"],
            "information_cutoff": snapshot["information_cutoff"],
        },
        "snapshot_evidence": snapshot_evidence,
    }


class AdoHitlCognitiveDecisionAdapter:
    """Bounded Vortex operator for cognitive-only dispatch that requires HITL.

    It recommends the same no-tools cognitive.v1 AgentOps execution lane as the
    standard cognitive operator, but binds the recommendation to the dedicated
    /hitl/ resource namespace and requires mandatory_human_review=True. Vortex
    still has no execution or approval authority.
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
            raise HitlCognitiveDecisionError(
                "HITL_COGNITIVE_ACTION_REJECT: mandatory_human_review must be true"
            )
        if not reference_result.admitted_evidence_ids:
            raise HitlCognitiveDecisionError(
                "HITL_COGNITIVE_ACTION_REJECT: at least one time-admissible evidence item is required"
            )
        if reference_result.rejected_evidence_ids:
            raise HitlCognitiveDecisionError(
                "HITL_COGNITIVE_ACTION_REJECT: rejected/future evidence makes HITL dispatch ineligible"
            )
        if reference_result.information_cutoff != request.information_cutoff:
            raise HitlCognitiveDecisionError(
                "HITL_COGNITIVE_ACTION_REJECT: reference engine cutoff drift"
            )
        if reference_result.execution_authority is not False:
            raise HitlCognitiveDecisionError(
                "CONSTITUTION_REJECT: reference engine unexpectedly has execution authority"
            )

        request_evidence = {item.evidence_id: item for item in request.evidence}
        snapshot_evidence = objective["snapshot_evidence"]
        for evidence_id in reference_result.admitted_evidence_ids:
            if evidence_id not in snapshot_evidence:
                raise HitlCognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from RealitySnapshot"
                )
            item = request_evidence.get(evidence_id)
            if item is None:
                raise HitlCognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from request"
                )
            ref = snapshot_evidence[evidence_id]
            if item.provenance_sha256 != ref["payload_hash"]:
                raise HitlCognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: payload hash differs from RealitySnapshot"
                )
            try:
                item_known = datetime.fromisoformat(item.known_at.replace("Z", "+00:00"))
                ref_known = datetime.fromisoformat(ref["known_at"].replace("Z", "+00:00"))
            except ValueError as exc:
                raise HitlCognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: invalid known_at timestamp"
                ) from exc
            if item_known != ref_known:
                raise HitlCognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: known_at differs from RealitySnapshot"
                )

        created_at = self.now().astimezone(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
        decision_id_material = {
            "profile": HITL_OBJECTIVE_KIND,
            "request_id": request.request_id,
            "agent_id": objective["agent_id"],
            "canonical_input_hash": objective["canonical_input_hash"],
            "information_cutoff": request.information_cutoff,
        }
        decision_id = "decision:vortex:ado-hitl:" + _sha256(
            _canonical_json(decision_id_material)
        )[:32]

        artifact: dict[str, Any] = {
            "schema_version": SEOS_SCHEMA_VERSION,
            "decision_id": decision_id,
            "decision_authority": "SOVEREIGN_VORTEX",
            "decision_request_id": request.request_id,
            "domain": "agentops_hitl_cognitive",
            "subject": {
                "subject_type": "agent",
                "subject_id": objective["agent_id"],
                "tenant_id": objective["tenant_id"],
                "extensions": {
                    "cognitive_profile": COGNITIVE_PROFILE,
                    "cognitive_output_only": True,
                    "human_approval_required": True,
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
                "action_type": COGNITIVE_ACTION_TYPE,
                "resource_refs": objective["resource_refs"],
                "canonical_input_hash": objective["canonical_input_hash"],
                "extensions": {
                    "mcp_tool": COGNITIVE_TOOL,
                    "cognitive_profile": COGNITIVE_PROFILE,
                    "cognitive_output_only": True,
                    "human_approval_required": True,
                },
            },
            "reason": (
                "Time-admissible RIG-bound evidence supports exactly one bounded "
                "cognitive-only AgentOps inference request, but the selected resource "
                "scope requires an independently issued one-time human ApprovalProof "
                "before AuthorizationAuthority may grant execution."
            ),
            "reason_codes": [
                "TIME_ADMISSIBLE",
                "RIG_SNAPSHOT_BOUND",
                "ADO_HITL_COGNITIVE_OPERATOR",
                "COGNITIVE_OUTPUT_ONLY",
                "HUMAN_APPROVAL_REQUIRED",
                "AUTONOMY_OVERRIDE_DISABLED",
            ],
            "uncertainty": {
                "semantics": (
                    "The epistemic recommendation is non-executing. Human approval is "
                    "an independent authorization precondition, not evidence that the "
                    "model output is correct."
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
                    "cognitive_output_only": True,
                    "autonomy_override": 0,
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
                    "cognitive_output_only": True,
                    "human_approval_required": True,
                },
            },
            "proof_ref": None,
            "extensions": {
                "cognitive_profile": COGNITIVE_PROFILE,
                "tool_name": COGNITIVE_TOOL,
                "cognitive_output_only": True,
                "human_approval_required": True,
            },
        }
        digest = recompute_decision_hash(artifact)
        artifact["decision_hash"] = digest
        artifact["integrity"]["body_hash"] = digest
        try:
            _validate_decision(artifact)
        except DiagnosticDecisionError as exc:
            raise HitlCognitiveDecisionError(str(exc)) from exc
        return artifact
