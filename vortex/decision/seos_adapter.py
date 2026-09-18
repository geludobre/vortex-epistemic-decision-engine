from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from vortex.decision.reference_engine import DecisionRequest, DecisionResult

SEOS_SCHEMA_VERSION = "1.0.0"
ADAPTER_ID = "adapter:vortex:agentops-diagnostic:v1"
ADAPTER_VERSION = "1.0.0"
ENGINE_ID = "vortex-reference-diagnostic-operator"
ENGINE_VERSION = "1.0.0"
POLICY_VERSION = "vortex-ado-diagnostic-policy-v1"
DIAGNOSTIC_OBJECTIVE_KIND = "ADO_DIAGNOSTIC_DISPATCH_V1"
DIAGNOSTIC_PROFILE = "diagnostic.v1"
DIAGNOSTIC_TOOL = "aug_agent_dispatch"
DIAGNOSTIC_ACTION_TYPE = "ado.dispatch.diagnostic"

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "schemas" / "seos" / "v1"
_HEX64 = set("0123456789abcdef")


class DiagnosticDecisionError(RuntimeError):
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


def _decision_hash_material(value: Mapping[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(dict(value))
    body.pop("decision_hash", None)
    body.pop("integrity", None)
    body.pop("proof_ref", None)
    return body


def recompute_decision_hash(value: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json(_decision_hash_material(value)))


def _reality_snapshot_hash_material(value: Mapping[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(dict(value))
    body.pop("snapshot_id", None)
    body.pop("captured_at", None)
    body.pop("snapshot_hash", None)
    body.pop("proof_ref", None)
    return body


def recompute_reality_snapshot_hash(value: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json(_reality_snapshot_hash_material(value)))


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


_COMMON_SCHEMA = _load_schema("common.schema.json")
_SCHEMA_REGISTRY = Registry().with_resource(
    "common.schema.json", Resource.from_contents(_COMMON_SCHEMA)
)
_DECISION_VALIDATOR = Draft202012Validator(
    _load_schema("decision-artifact.schema.json"),
    registry=_SCHEMA_REGISTRY,
    format_checker=FormatChecker(),
)
_REALITY_SNAPSHOT_VALIDATOR = Draft202012Validator(
    _load_schema("reality-snapshot.schema.json"),
    registry=_SCHEMA_REGISTRY,
    format_checker=FormatChecker(),
)


def _validate_decision(value: Mapping[str, Any]) -> None:
    errors = sorted(_DECISION_VALIDATOR.iter_errors(value), key=lambda e: list(e.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
            for error in errors[:8]
        )
        raise DiagnosticDecisionError("SEOS_DECISION_CONTRACT_REJECT: " + detail)


def _validated_reality_snapshot(
    value: Any,
    *,
    information_cutoff: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DiagnosticDecisionError(
            "DIAGNOSTIC_OBJECTIVE_REJECT: reality_snapshot must be an object"
        )
    snapshot = copy.deepcopy(dict(value))
    errors = sorted(
        _REALITY_SNAPSHOT_VALIDATOR.iter_errors(snapshot),
        key=lambda e: list(e.path),
    )
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
            for error in errors[:8]
        )
        raise DiagnosticDecisionError(
            "RIG_REALITY_SNAPSHOT_CONTRACT_REJECT: " + detail
        )
    if snapshot["completeness_state"] != "complete":
        raise DiagnosticDecisionError(
            "RIG_REALITY_SNAPSHOT_REJECT: completeness_state must be complete"
        )
    if snapshot["information_cutoff"] != information_cutoff:
        raise DiagnosticDecisionError(
            "RIG_REALITY_SNAPSHOT_REJECT: snapshot cutoff must equal decision cutoff"
        )
    expected_hash = recompute_reality_snapshot_hash(snapshot)
    if snapshot["snapshot_hash"] != expected_hash:
        raise DiagnosticDecisionError(
            "RIG_REALITY_SNAPSHOT_REJECT: snapshot_hash does not match canonical content"
        )
    if snapshot["snapshot_id"] != f"snapshot:rig:{expected_hash}":
        raise DiagnosticDecisionError(
            "RIG_REALITY_SNAPSHOT_REJECT: snapshot_id is not content-addressed"
        )
    return snapshot


def _required_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiagnosticDecisionError(f"DIAGNOSTIC_OBJECTIVE_REJECT: {field} is required")
    return value.strip()


def _hex64(value: Any, field: str) -> str:
    value = _required_str(value, field)
    if len(value) != 64 or any(ch not in _HEX64 for ch in value):
        raise DiagnosticDecisionError(
            f"DIAGNOSTIC_OBJECTIVE_REJECT: {field} must be lower-case SHA-256 hex"
        )
    return value


def _objective(request: DecisionRequest) -> dict[str, Any]:
    objective = request.objective
    if not isinstance(objective, Mapping):
        raise DiagnosticDecisionError("DIAGNOSTIC_OBJECTIVE_REJECT: objective must be an object")
    required = {
        "kind",
        "diagnostic_profile",
        "tenant_id",
        "agent_id",
        "tool_name",
        "action_type",
        "resource_refs",
        "canonical_input_hash",
        "reality_snapshot",
    }
    if set(objective) != required:
        raise DiagnosticDecisionError(
            "DIAGNOSTIC_OBJECTIVE_REJECT: objective must contain exactly "
            + str(sorted(required))
        )
    if objective.get("kind") != DIAGNOSTIC_OBJECTIVE_KIND:
        raise DiagnosticDecisionError("DIAGNOSTIC_OBJECTIVE_REJECT: unsupported objective kind")
    if objective.get("diagnostic_profile") != DIAGNOSTIC_PROFILE:
        raise DiagnosticDecisionError("DIAGNOSTIC_OBJECTIVE_REJECT: unsupported diagnostic profile")
    if objective.get("tool_name") != DIAGNOSTIC_TOOL:
        raise DiagnosticDecisionError("DIAGNOSTIC_OBJECTIVE_REJECT: tool_name must be aug_agent_dispatch")
    if objective.get("action_type") != DIAGNOSTIC_ACTION_TYPE:
        raise DiagnosticDecisionError("DIAGNOSTIC_OBJECTIVE_REJECT: action_type must be ado.dispatch.diagnostic")

    tenant_id = _required_str(objective.get("tenant_id"), "tenant_id")
    agent_id = _required_str(objective.get("agent_id"), "agent_id")
    resources = objective.get("resource_refs")
    expected_resource = f"ado:{tenant_id}/diagnostic/agent/{agent_id}"
    if resources != [expected_resource]:
        raise DiagnosticDecisionError(
            "DIAGNOSTIC_OBJECTIVE_REJECT: resource_refs must bind the exact agent"
        )
    input_hash = _hex64(objective.get("canonical_input_hash"), "canonical_input_hash")

    snapshot = _validated_reality_snapshot(
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
        "reality_snapshot_ref": {
            "snapshot_id": snapshot["snapshot_id"],
            "snapshot_hash": snapshot["snapshot_hash"],
            "information_cutoff": snapshot["information_cutoff"],
        },
        "snapshot_evidence": snapshot_evidence,
    }


class AdoDiagnosticDecisionAdapter:
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
            raise DiagnosticDecisionError(
                "DIAGNOSTIC_ACTION_REJECT: mandatory human review forbids diagnostic action recommendation"
            )
        if not reference_result.admitted_evidence_ids:
            raise DiagnosticDecisionError(
                "DIAGNOSTIC_ACTION_REJECT: at least one time-admissible evidence item is required"
            )
        if reference_result.rejected_evidence_ids:
            raise DiagnosticDecisionError(
                "DIAGNOSTIC_ACTION_REJECT: rejected/future evidence makes diagnostic action ineligible"
            )
        if reference_result.information_cutoff != request.information_cutoff:
            raise DiagnosticDecisionError(
                "DIAGNOSTIC_ACTION_REJECT: reference engine cutoff drift"
            )

        request_evidence = {item.evidence_id: item for item in request.evidence}
        snapshot_evidence = objective["snapshot_evidence"]
        for evidence_id in reference_result.admitted_evidence_ids:
            if evidence_id not in snapshot_evidence:
                raise DiagnosticDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from RealitySnapshot"
                )
            item = request_evidence.get(evidence_id)
            if item is None:
                raise DiagnosticDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: admitted evidence is absent from request"
                )
            ref = snapshot_evidence[evidence_id]
            if item.provenance_sha256 != ref["payload_hash"]:
                raise DiagnosticDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: payload hash differs from RealitySnapshot"
                )
            try:
                item_known = datetime.fromisoformat(item.known_at.replace("Z", "+00:00"))
                ref_known = datetime.fromisoformat(ref["known_at"].replace("Z", "+00:00"))
            except ValueError as exc:
                raise DiagnosticDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: invalid known_at timestamp"
                ) from exc
            if item_known != ref_known:
                raise DiagnosticDecisionError(
                    "RIG_EVIDENCE_BINDING_REJECT: known_at differs from RealitySnapshot"
                )

        created = self.now().astimezone(timezone.utc)
        created_at = created.isoformat(timespec="seconds").replace("+00:00", "Z")
        decision_id_material = {
            "profile": DIAGNOSTIC_OBJECTIVE_KIND,
            "request_id": request.request_id,
            "agent_id": objective["agent_id"],
            "canonical_input_hash": objective["canonical_input_hash"],
            "information_cutoff": request.information_cutoff,
        }
        decision_id = "decision:vortex:ado-diagnostic:" + _sha256(
            _canonical_json(decision_id_material)
        )[:32]

        artifact: dict[str, Any] = {
            "schema_version": SEOS_SCHEMA_VERSION,
            "decision_id": decision_id,
            "decision_authority": "SOVEREIGN_VORTEX",
            "decision_request_id": request.request_id,
            "domain": "agentops_diagnostic",
            "subject": {
                "subject_type": "agent",
                "subject_id": objective["agent_id"],
                "tenant_id": objective["tenant_id"],
                "extensions": {
                    "diagnostic_profile": DIAGNOSTIC_PROFILE,
                    "non_customer_effect": True,
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
                "action_type": DIAGNOSTIC_ACTION_TYPE,
                "resource_refs": objective["resource_refs"],
                "canonical_input_hash": objective["canonical_input_hash"],
                "extensions": {
                    "mcp_tool": DIAGNOSTIC_TOOL,
                    "diagnostic_profile": DIAGNOSTIC_PROFILE,
                },
            },
            "reason": (
                "Time-admissible RIG-bound evidence supports a bounded, non-customer "
                "ADO worker diagnostic for exactly one canonical agent."
            ),
            "reason_codes": [
                "TIME_ADMISSIBLE",
                "RIG_SNAPSHOT_BOUND",
                "ADO_DIAGNOSTIC_OPERATOR",
                "NON_CUSTOMER_DIAGNOSTIC",
            ],
            "uncertainty": {
                "semantics": (
                    "Synthetic diagnostic recommendation; uncertainty values are "
                    "engineering diagnostics, not calibrated business probabilities."
                ),
                "dimensions": {},
                "extensions": {},
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
                "extensions": {"diagnostic_only": True},
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
                    "diagnostic_only": True,
                },
            },
            "proof_ref": None,
            "extensions": {
                "diagnostic_profile": DIAGNOSTIC_PROFILE,
                "tool_name": DIAGNOSTIC_TOOL,
            },
        }
        digest = recompute_decision_hash(artifact)
        artifact["decision_hash"] = digest
        artifact["integrity"]["body_hash"] = digest
        _validate_decision(artifact)
        return artifact
