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
)


def _request(*, agent_id="ceo", cutoff="2026-09-18T00:00:00Z", task_hash="a" * 64):
    return DecisionRequest(
        request_id="decision-request:ado-diagnostic:ceo:0001",
        information_cutoff=cutoff,
        evidence=(
            EvidenceItem(
                "evidence:agentops:worker-health:ceo",
                "2026-09-17T23:59:59Z",
                {"worker_healthy": True, "agent_id": agent_id},
                "b" * 64,
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
            "reality_snapshot_ref": {
                "snapshot_id": "snapshot:rig:agentops-diagnostic:0001",
                "snapshot_hash": "c" * 64,
                "information_cutoff": cutoff,
            },
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


def test_rejects_non_rig_snapshot():
    request = _request()
    request.objective["reality_snapshot_ref"]["snapshot_id"] = "snapshot:local:fake"
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="RIG-owned"):
        _adapter().build(request=request, reference_result=result)


def test_rejects_snapshot_cutoff_drift():
    request = _request()
    request.objective["reality_snapshot_ref"]["information_cutoff"] = "2026-09-17T23:59:00Z"
    result = ReferenceDecisionEngine().evaluate(request)
    with pytest.raises(DiagnosticDecisionError, match="snapshot cutoff"):
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
