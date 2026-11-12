"""Native geopolitical decision operator: live-profile and adversarial integrity tests."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from hashlib import sha256
from pathlib import Path

import pytest

from vortex.decision.reference_engine import (
    DecisionRequest, EvidenceItem, ReferenceDecisionEngine,
)
from vortex.decision.seos_adapter import recompute_reality_snapshot_hash
from vortex.decision.geopolitical_evidence_triage import (
    GeopoliticalDecisionError,
    GeopoliticalEvidenceTriageAdapter,
)

NOW = "2026-11-12T10:00:00Z"


def source_payload(kind, group, idx, status="EVENT_REPORTED"):
    return {
        "evidence_class": kind, "correlation_group": group,
        "source_ref": "rig:independent-source:" + str(idx),
        "event_status": status, "claim_id": "claim:" + str(idx),
    }


def make_request(entries=None):
    if entries is None:
        entries = [
            source_payload("OFFICIAL_PRIMARY_RECORD", "agency:official", 1, "EVENT_OBSERVED"),
            source_payload("INDEPENDENT_INCIDENT_RECORD", "verified:incident", 2, "EVENT_REPORTED"),
        ]
    evidence = []
    refs = []
    for idx, payload in enumerate(entries):
        digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False).encode("utf-8")).hexdigest()
        eid = f"evidence:geo:{idx}"
        evidence.append({
            "evidence_id": eid, "known_at": "2026-11-12T09:00:00Z",
            "payload": payload, "provenance_sha256": digest,
        })
        refs.append({
            "evidence_id": eid, "payload_hash": digest,
            "known_at": "2026-11-12T09:00:00Z",
            "temporal_assurance": "DERIVED_OBSERVED_INGESTED",
            "source_id": f"11111111-1111-4111-8111-{idx+1:012d}",
            "provenance_ref": payload["source_ref"],
            "extensions": {},
        })
    snap = {
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot:rig:placeholder",
        "reality_authority": "RIG",
        "information_cutoff": NOW,
        "captured_at": "2026-11-12T10:00:01Z",
        "subject_scope": {
            "entity_ids": ["geo:industrial-cyber-exposure"],
            "entity_types": ["geopolitical_case"],
            "providers": ["rig_geopolitical_evidence"],
            "source_classes": ["source_observation"],
            "extensions": {},
        },
        "completeness_state": "complete",
        "temporal_policy_version": "known-at-v1",
        "evidence_refs": refs,
        "prediction_refs": [],
        "feature_snapshot_refs": [],
        "source_state_refs": [],
        "excluded_refs": [],
        "degraded_sources": [],
        "snapshot_hash": "0" * 64,
        "proof_ref": None,
        "extensions": {},
    }
    digest = recompute_reality_snapshot_hash(snap)
    snap["snapshot_hash"] = digest
    snap["snapshot_id"] = "snapshot:rig:" + digest
    return {
        "request_id": "request:geo:test:001",
        "information_cutoff": NOW,
        "evidence": evidence,
        "objective": {
            "kind": "GEOPOLITICAL_EVIDENCE_TRIAGE_V1",
            "case_id": "geo:industrial-cyber-exposure",
            "reality_snapshot": snap,
        },
    }


def assess(req):
    model = DecisionRequest(
        request_id=req["request_id"],
        information_cutoff=req["information_cutoff"],
        evidence=tuple(EvidenceItem(**e) for e in req["evidence"]),
        objective=req["objective"],
        mandatory_human_review=req.get("mandatory_human_review", False),
    )
    return GeopoliticalEvidenceTriageAdapter().build(
        request=model, reference_result=ReferenceDecisionEngine().evaluate(model)
    )


def test_valid_live_rig_primary_plus_independent_claim_is_human_review():
    body = assess(make_request())
    assert body["schema_version"] == "1.0.0"
    assert body["domain"] == "GLOBAL_GEOPOLITICAL_INTELLIGENCE"
    assert body["decision_authority"] == "SOVEREIGN_VORTEX"
    assert body["epistemic_disposition"] == "HUMAN_REVIEW"
    assert body["recommended_action"] is None
    assert body["execution_authority"] is False
    assert body["decision_hash"] == body["integrity"]["body_hash"]
    assert body["uncertainty"]["dimensions"]["real_world_events_independently_adjudicated"] == 0


def test_media_sources_are_never_treated_as_independent_event_truth():
    p1 = source_payload("MEDIA_INDEX", "media:syndicated:one", 1, "MEDIA_MENTION_ONLY")
    p2 = source_payload("MEDIA_INDEX", "media:syndicated:two", 2, "MEDIA_MENTION_ONLY")
    body = assess(make_request([p1, p2]))
    assert body["epistemic_disposition"] == "PROBE"
    assert body["uncertainty"]["extensions"]["media_mentions_are_events"] is False


def test_one_correlated_family_is_probe_not_two_votes():
    p1 = source_payload("OFFICIAL_PRIMARY_RECORD", "same:group", 1, "EVENT_OBSERVED")
    p2 = source_payload("INDEPENDENT_INCIDENT_RECORD", "same:group", 2)
    body = assess(make_request([p1, p2]))
    assert body["epistemic_disposition"] == "PROBE"
    assert body["uncertainty"]["dimensions"]["observed_correlation_group_count"] == 1


def test_canonical_snapshot_tamper_rejected():
    req = make_request()
    req["objective"]["reality_snapshot"]["evidence_refs"][0]["payload_hash"] = "f" * 64
    with pytest.raises(GeopoliticalDecisionError, match="SNAPSHOT_REJECT"):
        assess(req)


def test_mismatched_payload_source_and_known_at_rejected():
    req = make_request()
    req["evidence"][0]["payload"]["claim_id"] = "forged"
    with pytest.raises(GeopoliticalDecisionError, match="CUSTODY_MISMATCH"):
        assess(req)
    req = make_request()
    req["evidence"][0]["known_at"] = "2026-11-12T09:01:00Z"
    with pytest.raises(GeopoliticalDecisionError, match="KNOWN_AT_DRIFT"):
        assess(req)
    req = make_request()
    req["evidence"][0]["payload"]["source_ref"] = "not-the-RIG-source"
    with pytest.raises(GeopoliticalDecisionError, match="CUSTODY_MISMATCH"):
        assess(req)


def test_future_source_evidence_rejected_even_if_reported_by_rig():
    req = make_request()
    req["evidence"][1]["known_at"] = "2026-11-12T10:00:01Z"
    with pytest.raises(GeopoliticalDecisionError, match="FUTURE"):
        assess(req)


def test_duplicate_evidence_or_missing_snapshot_source_rejected():
    req = make_request()
    req["evidence"].append(copy.deepcopy(req["evidence"][0]))
    with pytest.raises(GeopoliticalDecisionError, match="DUPLICATE_EVIDENCE"):
        assess(req)
    req = make_request()
    del req["objective"]["reality_snapshot"]["evidence_refs"][0]
    with pytest.raises(GeopoliticalDecisionError, match="SNAPSHOT_REJECT"):
        assess(req)


def test_policy_human_review_is_not_downgraded():
    req = make_request([source_payload("MEDIA_INDEX", "media:one", 1, "MEDIA_MENTION_ONLY")])
    req["mandatory_human_review"] = True
    assert assess(req)["epistemic_disposition"] == "HUMAN_REVIEW"


def _client():
    os.environ["VORTEX_REQUIRE_EXACT_SOURCE"] = "false"
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "vortex_geo_api_test", root / "services" / "decision-api" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.app.test_client()


def test_api_route_disabled_by_default(monkeypatch):
    monkeypatch.delenv("VORTEX_ENABLE_GEO_EVIDENCE_TRIAGE", raising=False)
    response = _client().post("/v1/decision/geopolitical-evidence", json=make_request())
    assert response.status_code == 503
    assert response.get_json()["error"] == "GEO_OPERATOR_DISABLED"


def test_api_route_returns_canonical_decision_artifact(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_GEO_EVIDENCE_TRIAGE", "true")
    response = _client().post("/v1/decision/geopolitical-evidence", json=make_request())
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["epistemic_disposition"] == "HUMAN_REVIEW"
    assert body["execution_authority"] is False


def test_api_route_rejects_an_unexpected_payload_property(monkeypatch):
    monkeypatch.setenv("VORTEX_ENABLE_GEO_EVIDENCE_TRIAGE", "true")
    payload = make_request()
    payload["evidence"][0]["payload"]["contact_email"] = "private@example.com"
    response = _client().post("/v1/decision/geopolitical-evidence", json=payload)
    assert response.status_code == 409
    assert response.get_json()["error"] == "GEO_ADMISSION_REJECT"
