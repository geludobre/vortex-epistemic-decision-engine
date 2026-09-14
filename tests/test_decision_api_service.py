from __future__ import annotations

import importlib.util
import os
from pathlib import Path

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
