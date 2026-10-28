from __future__ import annotations

from datetime import datetime, timezone

import pytest

from vortex.decision.reference_engine import (
    DecisionRequest,
    EvidenceItem,
    ReferenceDecisionEngine,
)
from vortex.decision.seos_adapter import (
    AdoDiagnosticDecisionAdapter,
    DiagnosticDecisionError,
    recompute_decision_hash,
    recompute_reality_snapshot_hash,
)


def _snapshot(
    *,
    agent_id="ceo",
    cutoff="2026-09-18T00:00:00Z",
    evidence_id=None,
    payload_hash="b" * 64,
    known_at="2026-09-17T23:59:59Z",
):
    evidence_id = evidence_id or f"evidence:agentops:worker-health:{agent_id}"
    value = {
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot:rig:placeholder",
        "reality_authority": "RIG",
        "information_cutoff": cutoff,
        "captured_at": "2026-09-18T00:00:01Z",
        "subject_scope": {
            "entity_ids": [agent_id],
            "entity_types": ["agent"],
            "providers": ["agentops_customerzero_diagnostic"],
            "source_classes": ["provider_observation_staging"],
            "extensions": {},
        },
        "completeness_state": "complete",
        "temporal_policy_version": "known-at-v1",
        "evidence_refs": [
            {
                "evidence_id": evidence_id,
                "payload_hash": payload_hash,
                "known_at": known_at,
                "temporal_assurance": "DERIVED_OBSERVED_INGESTED",
                "source_id": "11111111-1111-4111-8111-111111111111",
                "provenance_ref": "rig_provider_observation_staging:diagnostic:1",
                "extensions": {},
            }
        ],
        "prediction_refs": [],
        "feature_snapshot_refs": [],
        "source_state_refs": [],
        "excluded_refs": [],
        "degraded_sources": [],
        "snapshot_hash": "0" * 64,
        "proof_ref": None,
        "extensions": {},
    }
    digest = recompute_reality_snapshot_hash(value)
    value["snapshot_hash"] = digest
    value["snapshot_id"] = f"snapshot:rig:{digest}"
    return value


def _request(
    *,
    agent_id="ceo",
    cutoff="2026-09-18T00:00:00Z",
    task_hash="a" * 64,
    evidence_payload_hash="b" * 64,
    evidence_known_at="2026-09-17T23:59:59Z",
    snapshot=None,
):
    evidence_id = f"evidence:agentops:worker-health:{agent_id}"
    snapshot = snapshot or _snapshot(
        agent_id=agent_id,
        cutoff=cutoff,
        evidence_id=evidence_id,
        payload_hash=evidence_payload_hash,
        known_at=evidence_known_at,
    )
    return DecisionRequest(
        request_id=f"decision-request:ado-diagnostic:{agent_id}:0001",
        information_cutoff=cutoff,
        evidence=(
            EvidenceItem(
                evidence_id,
                evidence_known_at,
                {"worker_healthy": True, "agent_id": agent_id},
                evidence_payload_hash,
            ),
        ),
        objective={
            "kind": "ADO_DIAGNOSTIC_DISPATCH_V1",
            "diagnostic_profile": "diagnostic.v1",
            "tenant_id": "customer-zero",
            "agent_id": agent_id,
            "tool_name": "aug_agent_dispatch",
            "action_type": "ado.dispatch.diagnostic",
            "resource_refs": [f"ado:customer-zero/diagnostic/agent/{agent_id}"],
            "canonical_input_hash": task_hash,
            "reality_snapshot": snapshot,
        },
    )


def _adapter():
    return AdoDiagnosticDecisionAdapter(
        now=lambda: datetime(2026, 9, 18, 0, 0, 3, tzinfo=timezone.utc)
    )


def test_builds_schema_valid_action_recommendation_without_execution_authority():
    request = _request()
    result = ReferenceDecisionEngine().evaluate(request)
    assert result.decision == "ABSTAIN"

    artifact = _adapter().build(request=request, reference_result=result)
    assert artifact["decision_authority"] == "SOVEREIGN_VORTEX"
    assert artifact["epistemic_disposition"] == "ACTION_RECOMMENDATION"
    assert artifact["execution_authority"] is False
    assert artifact["subject"]["tenant_id"] == "customer-zero"
    assert artifact["subject"]["subject_id"] == "ceo"
    assert artifact["inputs"]["reality_snapshot_ref"]["snapshot_id"].startswith(
        "snapshot:rig:"
    )
    assert artifact["recommended_action"] == {
        "action_type": "ado.dispatch.diagnostic",
        "resource_refs": ["ado:customer-zero/diagnostic/agent/ceo"],
        "canonical_input_hash": "a" * 64,
        "extensions": {
            "mcp_tool": "aug_agent_dispatch",
            "diagnostic_profile": "diagnostic.v1",
        },
    }
    assert artifact["decision_hash"] == recompute_decision_hash(artifact)
    assert artifact["integrity"]["body_hash"] == artifact["decision_hash"]
    assert artifact["integrity"]["assurance_level"] == "HASH_ONLY"


def test_rejects_resource_scope_that_does_not_bind_exact_agent():
    request = _request()
    request.objective["resource_refs"] = ["ado:customer-zero/diagnostic/agent/cto"]
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="resource_refs must bind the exact agent"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_tampered_snapshot_hash():
    snapshot = _snapshot()
    snapshot["evidence_refs"][0]["payload_hash"] = "c" * 64
    request = _request(snapshot=snapshot)
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="snapshot_hash does not match"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_non_content_addressed_snapshot_id():
    snapshot = _snapshot()
    snapshot["snapshot_id"] = "snapshot:rig:not-the-content-hash"
    request = _request(snapshot=snapshot)
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="snapshot_id is not content-addressed"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_snapshot_cutoff_drift():
    snapshot = _snapshot(cutoff="2026-09-17T23:59:00Z")
    request = _request(snapshot=snapshot)
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="snapshot cutoff"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_incomplete_snapshot():
    snapshot = _snapshot()
    snapshot["completeness_state"] = "degraded"
    snapshot["degraded_sources"] = ["agentops_customerzero_diagnostic"]
    digest = recompute_reality_snapshot_hash(snapshot)
    snapshot["snapshot_hash"] = digest
    snapshot["snapshot_id"] = f"snapshot:rig:{digest}"
    request = _request(snapshot=snapshot)
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="completeness_state must be complete"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_admitted_evidence_absent_from_snapshot():
    snapshot = _snapshot(evidence_id="evidence:other")
    request = _request(snapshot=snapshot)
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="absent from RealitySnapshot"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_payload_hash_mismatch_with_snapshot():
    snapshot = _snapshot(payload_hash="c" * 64)
    request = _request(snapshot=snapshot, evidence_payload_hash="b" * 64)
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="payload hash differs"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_known_at_mismatch_with_snapshot():
    snapshot = _snapshot(known_at="2026-09-17T23:59:58Z")
    request = _request(snapshot=snapshot, evidence_known_at="2026-09-17T23:59:59Z")
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="known_at differs"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_any_future_or_rejected_evidence():
    request = _request()
    request = DecisionRequest(
        request_id=request.request_id,
        information_cutoff=request.information_cutoff,
        evidence=request.evidence
        + (
            EvidenceItem(
                "evidence:future",
                "2026-09-18T00:00:01Z",
                {},
                "d" * 64,
            ),
        ),
        objective=request.objective,
    )
    result = ReferenceDecisionEngine().evaluate(request)
    assert result.rejected_evidence_ids == ("evidence:future",)
    with pytest.raises(DiagnosticDecisionError, match="rejected/future evidence"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_mandatory_human_review():
    base = _request()
    request = DecisionRequest(
        request_id=base.request_id,
        information_cutoff=base.information_cutoff,
        evidence=base.evidence,
        objective=base.objective,
        mandatory_human_review=True,
    )
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="mandatory human review"):
        _adapter().build(request=request, reference_result=result)
