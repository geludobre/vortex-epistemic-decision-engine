from __future__ import annotations

import copy
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
ADAPTER_ID = "adapter:vortex:agentops-cognitive:v1"
ADAPTER_VERSION = "1.0.0"
ENGINE_ID = "vortex-reference-cognitive-operator"
ENGINE_VERSION = "1.0.0"
POLICY_VERSION = "vortex-ado-cognitive-policy-v1"
COGNITIVE_OBJECTIVE_KIND = "ADO_COGNITIVE_DISPATCH_V1"
COGNITIVE_PROFILE = "cognitive.v1"
COGNITIVE_TOOL = "aug_agent_dispatch"
COGNITIVE_ACTION_TYPE = "ado.dispatch"
CUSTOMER_ZERO_TENANT = "customer-zero"
MAX_TASK_CHARS = 32768


class CognitiveDecisionError(RuntimeError):
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
    """SEOS-CJ-1 hash of the exact aug_agent_dispatch argument object."""
    return _sha256(_canonical_json(dict(arguments)))


def _required_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CognitiveDecisionError(
            f"COGNITIVE_OBJECTIVE_REJECT: {field} is required"
        )
    if value != value.strip():
        raise CognitiveDecisionError(
            f"COGNITIVE_OBJECTIVE_REJECT: {field} must be canonical trimmed text"
        )
    return value


def _validated_dispatch_arguments(
    value: Any,
    *,
    expected_agent_id: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: dispatch_arguments must be an object"
        )
    args = dict(value)
    required = {"agent_id", "task", "autonomy_override"}
    if set(args) != required:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: dispatch_arguments must contain exactly "
            + str(sorted(required))
        )

    agent_id = _required_str(args.get("agent_id"), "dispatch_arguments.agent_id")
    if agent_id != expected_agent_id:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: dispatch agent_id must match objective agent_id"
        )

    task = _required_str(args.get("task"), "dispatch_arguments.task")
    if len(task) > MAX_TASK_CHARS:
        raise CognitiveDecisionError(
            f"COGNITIVE_OBJECTIVE_REJECT: task exceeds {MAX_TASK_CHARS} characters"
        )

    autonomy_override = args.get("autonomy_override")
    if (
        isinstance(autonomy_override, bool)
        or not isinstance(autonomy_override, int)
        or autonomy_override != 0
    ):
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: autonomy_override must be exactly 0"
        )

    # Force canonical JSON serializability now; this must hash identically to
    # AgentOps canonical_action_input_hash at the execution boundary.
    canonical_action_input_hash(args)
    return args


def _validated_snapshot(value: Any, *, information_cutoff: str) -> dict[str, Any]:
    try:
        return _validated_reality_snapshot(
            value,
            information_cutoff=information_cutoff,
        )
    except DiagnosticDecisionError as exc:
        detail = str(exc).replace(
            "DIAGNOSTIC_OBJECTIVE_REJECT",
            "COGNITIVE_OBJECTIVE_REJECT",
        )
        raise CognitiveDecisionError(detail) from exc


def _objective(request: DecisionRequest) -> dict[str, Any]:
    objective = request.objective
    if not isinstance(objective, Mapping):
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: objective must be an object"
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
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: objective must contain exactly "
            + str(sorted(required))
        )
    if objective.get("kind") != COGNITIVE_OBJECTIVE_KIND:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: unsupported objective kind"
        )
    if objective.get("cognitive_profile") != COGNITIVE_PROFILE:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: unsupported cognitive profile"
        )
    if objective.get("tool_name") != COGNITIVE_TOOL:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: tool_name must be aug_agent_dispatch"
        )
    if objective.get("action_type") != COGNITIVE_ACTION_TYPE:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: action_type must be ado.dispatch"
        )

    tenant_id = _required_str(objective.get("tenant_id"), "tenant_id")
    if tenant_id != CUSTOMER_ZERO_TENANT:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: only customer-zero is eligible in v1"
        )
    agent_id = _required_str(objective.get("agent_id"), "agent_id")
    resources = objective.get("resource_refs")
    expected_resource = f"ado:{tenant_id}/cognitive/agent/{agent_id}"
    if resources != [expected_resource]:
        raise CognitiveDecisionError(
            "COGNITIVE_OBJECTIVE_REJECT: resource_refs must bind the exact cognitive agent"
        )

    dispatch_arguments = _validated_dispatch_arguments(
        objective.get("dispatch_arguments"),
        expected_agent_id=agent_id,
    )
    input_hash = canonical_action_input_hash(dispatch_arguments)

    snapshot = _validated_snapshot(
        objective.get("reality_snapshot"),
        information_cutoff=request.information_cutoff,
    )
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


class AdoCognitiveDecisionAdapter:
    """Bounded Vortex operator for cognitive-only AgentOps inference dispatch.

    This operator may recommend a durable model-inference request, but it never
    grants execution authority and never recommends a downstream business side
    effect. The exact aug_agent_dispatch arguments are inspected in Vortex and
    bound by SEOS-CJ-1 hash into the DecisionArtifact.
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

        if request.mandatory_human_review:
            raise CognitiveDecisionError(
                "COGNITIVE_ACTION_REJECT: mandatory human review forbids cognitive dispatch recommendation"
            )
        if not reference_result.admitted_evidence_ids:
            raise CognitiveDecisionError(
                "COGNITIVE_ACTION_REJECT: at least one time-admissible evidence item is required"
            )
        if reference_result.rejected_evidence_ids:
            raise CognitiveDecisionError(
                "COGNITIVE_ACTION_REJECT: rejected/future evidence makes cognitive dispatch ineligible"
            )
        if reference_result.information_cutoff != request.information_cutoff:
            raise CognitiveDecisionError(
                "COGNITIVE_ACTION_REJECT: reference engine cutoff drift"
            )
        if reference_result.execution_authority is not False:
            raise CognitiveDecisionError(
                "CONSTITUTION_REJECT: reference engine unexpectedly has execution authority"
            )

        request_evidence = {item.evidence_id: item for item in request.evidence}
        snapshot_evidence = objective["snapshot_evidence"]
        for evidence_id in reference_result.admitted_evidence_ids:
            if evidence_id not in snapshot_evidence:
                raise CognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from RealitySnapshot"
                )
            item = request_evidence.get(evidence_id)
            if item is None:
                raise CognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from request"
                )
            ref = snapshot_evidence[evidence_id]
            if item.provenance_sha256 != ref["payload_hash"]:
                raise CognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: payload hash differs from RealitySnapshot"
                )
            try:
                item_known = datetime.fromisoformat(
                    item.known_at.replace("Z", "+00:00")
                )
                ref_known = datetime.fromisoformat(
                    ref["known_at"].replace("Z", "+00:00")
                )
            except ValueError as exc:
                raise CognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: invalid known_at timestamp"
                ) from exc
            if item_known != ref_known:
                raise CognitiveDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: known_at differs from RealitySnapshot"
                )

        created = self.now().astimezone(timezone.utc)
        created_at = created.isoformat(timespec="seconds").replace("+00:00", "Z")
        decision_id_material = {
            "profile": COGNITIVE_OBJECTIVE_KIND,
            "request_id": request.request_id,
            "agent_id": objective["agent_id"],
            "canonical_input_hash": objective["canonical_input_hash"],
            "information_cutoff": request.information_cutoff,
        }
        decision_id = "decision:vortex:ado-cognitive:" + _sha256(
            _canonical_json(decision_id_material)
        )[:32]

        artifact: dict[str, Any] = {
            "schema_version": SEOS_SCHEMA_VERSION,
            "decision_id": decision_id,
            "decision_authority": "SOVEREIGN_VORTEX",
            "decision_request_id": request.request_id,
            "domain": "agentops_cognitive",
            "subject": {
                "subject_type": "agent",
                "subject_id": objective["agent_id"],
                "tenant_id": objective["tenant_id"],
                "extensions": {
                    "cognitive_profile": COGNITIVE_PROFILE,
                    "cognitive_output_only": True,
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
                },
            },
            "reason": (
                "Time-admissible RIG-bound evidence supports a bounded cognitive-only "
                "inference request for exactly one canonical AgentOps role. The worker "
                "can return analysis or text but has no execution tools or business-action authority."
            ),
            "reason_codes": [
                "TIME_ADMISSIBLE",
                "RIG_SNAPSHOT_BOUND",
                "ADO_COGNITIVE_OPERATOR",
                "COGNITIVE_OUTPUT_ONLY",
                "AUTONOMY_OVERRIDE_DISABLED",
            ],
            "uncertainty": {
                "semantics": (
                    "This recommendation authorizes information-gathering inference only; "
                    "it is not a calibrated claim that the model output is correct."
                ),
                "dimensions": {},
                "extensions": {
                    "reference_decision": reference_result.decision,
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
                },
            },
            "proof_ref": None,
            "extensions": {
                "cognitive_profile": COGNITIVE_PROFILE,
                "tool_name": COGNITIVE_TOOL,
                "cognitive_output_only": True,
            },
        }
        digest = recompute_decision_hash(artifact)
        artifact["decision_hash"] = digest
        artifact["integrity"]["body_hash"] = digest
        try:
            _validate_decision(artifact)
        except DiagnosticDecisionError as exc:
            raise CognitiveDecisionError(str(exc)) from exc
        return artifact
