from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from vortex.decision.cognitive_adapter import canonical_action_input_hash
from vortex.decision.seos_adapter import recompute_reality_snapshot_hash

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "services" / "decision-api" / "app.py"

os.environ["VORTEX_REQUIRE_EXACT_SOURCE"] = "false"
spec = importlib.util.spec_from_file_location("vortex_decision_api", APP_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
client = module.app.test_client()


def test_health_and_ready_are_shadow_and_non_executing():
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json()["mode"] == "SHADOW_REFERENCE"

    ready = client.get("/readyz")
    assert ready.status_code == 200
    body = ready.get_json()
    assert body["status"] == "ready"
    assert body["execution_authority"] is False
    assert body["ado_cognitive_action_enabled"] is False


def test_future_evidence_is_rejected_by_known_at_firewall():
    response = client.post(
        "/v1/decision/evaluate",
        json={
            "request_id": "req-1",
            "information_cutoff": "2026-09-15T00:00:00Z",
            "evidence": [
                {
                    "evidence_id": "past",
                    "known_at": "2026-09-14T23:59:59Z",
                    "payload": {"value": 1},
                },
                {
                    "evidence_id": "future",
                    "known_at": "2026-09-15T00:00:01Z",
                    "payload": {"value": 2},
                },
            ],
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["admitted_evidence_ids"] == ["past"]
    assert body["rejected_evidence_ids"] == ["future"]
    assert body["execution_authority"] is False
    assert body["decision"] == "ABSTAIN"


def test_no_admissible_evidence_waits():
    response = client.post(
        "/v1/decision/evaluate",
        json={
            "request_id": "req-2",
            "information_cutoff": "2026-09-15T00:00:00Z",
            "evidence": [],
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["decision"] == "WAIT"
    assert body["execution_authority"] is False


def test_mandatory_human_review_is_preserved():
    response = client.post(
        "/v1/decision/evaluate",
        json={
            "request_id": "req-3",
            "information_cutoff": "2026-09-15T00:00:00Z",
            "mandatory_human_review": True,
            "evidence": [
                {
                    "evidence_id": "e1",
                    "known_at": "2026-09-14T23:00:00Z",
                    "payload": {},
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["decision"] == "HUMAN_REVIEW"
    assert body["execution_authority"] is False


def test_schema_rejects_unknown_fields():
    response = client.post(
        "/v1/decision/evaluate",
        json={
            "request_id": "req-4",
            "information_cutoff": "2026-09-15T00:00:00Z",
            "evidence": [],
            "unexpected": True,
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "REQUEST_CONTRACT_REJECT"


def _diagnostic_snapshot(agent_id="ceo"):
    evidence_id = f"evidence:agentops:worker-health:{agent_id}"
    value = {
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot:rig:placeholder",
        "reality_authority": "RIG",
        "information_cutoff": "2026-09-18T00:00:00Z",
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
                "payload_hash": "b" * 64,
                "known_at": "2026-09-17T23:59:59Z",
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


def _diagnostic_request(agent_id="ceo"):
    return {
        "request_id": f"decision-request:ado-diagnostic:{agent_id}:0001",
        "information_cutoff": "2026-09-18T00:00:00Z",
        "evidence": [
            {
                "evidence_id": f"evidence:agentops:worker-health:{agent_id}",
                "known_at": "2026-09-17T23:59:59Z",
                "payload": {"worker_healthy": True, "agent_id": agent_id},
                "provenance_sha256": "b" * 64,
            }
        ],
        "objective": {
            "kind": "ADO_DIAGNOSTIC_DISPATCH_V1",
            "diagnostic_profile": "diagnostic.v1",
            "tenant_id": "customer-zero",
            "agent_id": agent_id,
            "tool_name": "aug_agent_dispatch",
            "action_type": "ado.dispatch.diagnostic",
            "resource_refs": [f"ado:customer-zero/diagnostic/agent/{agent_id}"],
            "canonical_input_hash": "a" * 64,
            "reality_snapshot": _diagnostic_snapshot(agent_id),
        },
    }


def test_ado_diagnostic_endpoint_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("VORTEX_ENABLE_ADO_DIAGNOSTIC_ACTION", raising=False)
    response = client.post("/v1/decision/ado-diagnostic", json=_diagnostic_request())
    assert response.status_code == 503
    assert response.get_json()["error"] == "DIAGNOSTIC_OPERATOR_DISABLED"


def test_ado_diagnostic_endpoint_emits_bounded_action_recommendation(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_DIAGNOSTIC_ACTION", "true")
    response = client.post("/v1/decision/ado-diagnostic", json=_diagnostic_request())
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["decision_authority"] == "SOVEREIGN_VORTEX"
    assert body["epistemic_disposition"] == "ACTION_RECOMMENDATION"
    assert body["recommended_action"]["action_type"] == "ado.dispatch.diagnostic"
    assert body["recommended_action"]["resource_refs"] == ["ado:customer-zero/diagnostic/agent/ceo"]
    assert body["recommended_action"]["canonical_input_hash"] == "a" * 64
    assert body["execution_authority"] is False
    assert body["integrity"]["assurance_level"] == "HASH_ONLY"
    assert body["decision_hash"] == body["integrity"]["body_hash"]


def test_ado_diagnostic_endpoint_rejects_snapshot_tampering(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_DIAGNOSTIC_ACTION", "true")
    payload = _diagnostic_request()
    payload["objective"]["reality_snapshot"]["evidence_refs"][0]["payload_hash"] = "c" * 64
    response = client.post("/v1/decision/ado-diagnostic", json=payload)
    assert response.status_code == 409
    body = response.get_json()
    assert body["error"] == "DIAGNOSTIC_ACTION_REJECT"
    assert "snapshot_hash does not match" in body["detail"]


def test_ado_diagnostic_endpoint_rejects_future_evidence(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_DIAGNOSTIC_ACTION", "true")
    payload = _diagnostic_request()
    payload["evidence"].append(
        {
            "evidence_id": "evidence:future",
            "known_at": "2026-09-18T00:00:01Z",
            "payload": {},
            "provenance_sha256": "d" * 64,
        }
    )
    response = client.post("/v1/decision/ado-diagnostic", json=payload)
    assert response.status_code == 409
    assert response.get_json()["error"] == "DIAGNOSTIC_ACTION_REJECT"


def _cognitive_snapshot(agent_id="ceo"):
    evidence_id = f"evidence:agentops:cognitive-readiness:{agent_id}"
    value = {
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot:rig:placeholder",
        "reality_authority": "RIG",
        "information_cutoff": "2026-09-18T00:00:00Z",
        "captured_at": "2026-09-18T00:00:01Z",
        "subject_scope": {
            "entity_ids": [agent_id],
            "entity_types": ["agent"],
            "providers": ["agentops_customerzero_cognitive_readiness"],
            "source_classes": ["provider_observation_staging"],
            "extensions": {},
        },
        "completeness_state": "complete",
        "temporal_policy_version": "known-at-v1",
        "evidence_refs": [
            {
                "evidence_id": evidence_id,
                "payload_hash": "c" * 64,
                "known_at": "2026-09-17T23:59:59Z",
                "temporal_assurance": "DERIVED_OBSERVED_INGESTED",
                "source_id": "22222222-2222-4222-8222-222222222222",
                "provenance_ref": "rig_provider_observation_staging:cognitive-readiness:1",
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


def _cognitive_request(agent_id="ceo"):
    dispatch_arguments = {
        "agent_id": agent_id,
        "task": "Return exactly COGNITIVE_OK. Do not request or perform side effects.",
        "autonomy_override": 0,
    }
    return {
        "request_id": f"decision-request:ado-cognitive:{agent_id}:0001",
        "information_cutoff": "2026-09-18T00:00:00Z",
        "evidence": [
            {
                "evidence_id": f"evidence:agentops:cognitive-readiness:{agent_id}",
                "known_at": "2026-09-17T23:59:59Z",
                "payload": {
                    "worker_healthy": True,
                    "cognitive_provider": "groq",
                    "agent_id": agent_id,
                },
                "provenance_sha256": "c" * 64,
            }
        ],
        "objective": {
            "kind": "ADO_COGNITIVE_DISPATCH_V1",
            "cognitive_profile": "cognitive.v1",
            "tenant_id": "customer-zero",
            "agent_id": agent_id,
            "tool_name": "aug_agent_dispatch",
            "action_type": "ado.dispatch",
            "resource_refs": [f"ado:customer-zero/cognitive/agent/{agent_id}"],
            "dispatch_arguments": dispatch_arguments,
            "reality_snapshot": _cognitive_snapshot(agent_id),
        },
    }


def test_ado_cognitive_endpoint_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("VORTEX_ENABLE_ADO_COGNITIVE_ACTION", raising=False)
    response = client.post("/v1/decision/ado-cognitive", json=_cognitive_request())
    assert response.status_code == 503
    assert response.get_json()["error"] == "COGNITIVE_OPERATOR_DISABLED"


def test_ado_cognitive_endpoint_emits_bounded_nonexecuting_recommendation(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_COGNITIVE_ACTION", "true")
    payload = _cognitive_request()
    response = client.post("/v1/decision/ado-cognitive", json=payload)
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    args = payload["objective"]["dispatch_arguments"]
    assert body["decision_authority"] == "SOVEREIGN_VORTEX"
    assert body["epistemic_disposition"] == "ACTION_RECOMMENDATION"
    assert body["recommended_action"]["action_type"] == "ado.dispatch"
    assert body["recommended_action"]["resource_refs"] == [
        "ado:customer-zero/cognitive/agent/ceo"
    ]
    assert body["recommended_action"]["canonical_input_hash"] == canonical_action_input_hash(args)
    assert body["recommended_action"]["extensions"]["cognitive_output_only"] is True
    assert body["execution_authority"] is False
    assert body["risk_assessment"]["extensions"]["autonomy_override"] == 0
    assert body["decision_hash"] == body["integrity"]["body_hash"]


def test_ado_cognitive_endpoint_rejects_autonomy_override(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_COGNITIVE_ACTION", "true")
    payload = _cognitive_request()
    payload["objective"]["dispatch_arguments"]["autonomy_override"] = 1
    response = client.post("/v1/decision/ado-cognitive", json=payload)
    assert response.status_code == 409
    assert response.get_json()["error"] == "COGNITIVE_ACTION_REJECT"
    assert "autonomy_override must be exactly 0" in response.get_json()["detail"]


def test_ado_cognitive_endpoint_rejects_snapshot_tampering(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_COGNITIVE_ACTION", "true")
    payload = _cognitive_request()
    payload["objective"]["reality_snapshot"]["evidence_refs"][0]["payload_hash"] = "d" * 64
    response = client.post("/v1/decision/ado-cognitive", json=payload)
    assert response.status_code == 409
    assert response.get_json()["error"] == "COGNITIVE_ACTION_REJECT"
    assert "snapshot_hash does not match" in response.get_json()["detail"]


def test_ado_cognitive_endpoint_rejects_future_evidence(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_COGNITIVE_ACTION", "true")
    payload = _cognitive_request()
    payload["evidence"].append(
        {
            "evidence_id": "evidence:future",
            "known_at": "2026-09-18T00:00:01Z",
            "payload": {},
            "provenance_sha256": "e" * 64,
        }
    )
    response = client.post("/v1/decision/ado-cognitive", json=payload)
    assert response.status_code == 409
    assert response.get_json()["error"] == "COGNITIVE_ACTION_REJECT"
    assert "rejected/future evidence" in response.get_json()["detail"]

def _hitl_cognitive_request(agent_id="ceo"):
    payload = _cognitive_request(agent_id)
    payload["request_id"] = f"decision-request:ado-hitl-cognitive:{agent_id}:0001"
    payload["mandatory_human_review"] = True
    payload["objective"]["kind"] = "ADO_HITL_COGNITIVE_DISPATCH_V1"
    payload["objective"]["resource_refs"] = [
        f"ado:customer-zero/hitl/agent/{agent_id}"
    ]
    return payload


def test_ado_hitl_cognitive_endpoint_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("VORTEX_ENABLE_ADO_HITL_COGNITIVE_ACTION", raising=False)
    response = client.post(
        "/v1/decision/ado-hitl-cognitive",
        json=_hitl_cognitive_request(),
    )
    assert response.status_code == 503
    assert response.get_json()["error"] == "HITL_COGNITIVE_OPERATOR_DISABLED"


def test_ado_hitl_cognitive_endpoint_emits_nonexecuting_hitl_recommendation(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_HITL_COGNITIVE_ACTION", "true")
    payload = _hitl_cognitive_request()
    response = client.post("/v1/decision/ado-hitl-cognitive", json=payload)
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    args = payload["objective"]["dispatch_arguments"]
    assert body["decision_authority"] == "SOVEREIGN_VORTEX"
    assert body["epistemic_disposition"] == "ACTION_RECOMMENDATION"
    assert body["recommended_action"]["action_type"] == "ado.dispatch"
    assert body["recommended_action"]["resource_refs"] == [
        "ado:customer-zero/hitl/agent/ceo"
    ]
    assert body["recommended_action"]["canonical_input_hash"] == canonical_action_input_hash(args)
    assert body["recommended_action"]["extensions"]["cognitive_output_only"] is True
    assert body["recommended_action"]["extensions"]["human_approval_required"] is True
    assert body["execution_authority"] is False
    assert body["subject"]["extensions"]["human_approval_required"] is True
    assert body["decision_hash"] == body["integrity"]["body_hash"]


def test_ado_hitl_cognitive_endpoint_requires_mandatory_human_review(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_HITL_COGNITIVE_ACTION", "true")
    payload = _hitl_cognitive_request()
    payload["mandatory_human_review"] = False
    response = client.post("/v1/decision/ado-hitl-cognitive", json=payload)
    assert response.status_code == 409
    body = response.get_json()
    assert body["error"] == "HITL_COGNITIVE_ACTION_REJECT"
    assert "mandatory_human_review must be true" in body["detail"]


def test_ado_hitl_cognitive_endpoint_rejects_cognitive_scope_substitution(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_ADO_HITL_COGNITIVE_ACTION", "true")
    payload = _hitl_cognitive_request()
    payload["objective"]["resource_refs"] = [
        "ado:customer-zero/cognitive/agent/ceo"
    ]
    response = client.post("/v1/decision/ado-hitl-cognitive", json=payload)
    assert response.status_code == 409
    body = response.get_json()
    assert body["error"] == "HITL_COGNITIVE_ACTION_REJECT"
    assert "exact HITL agent" in body["detail"]

