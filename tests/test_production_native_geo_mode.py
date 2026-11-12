"""Fail-closed production geopolitical runtime profile acceptance."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


APP = Path(__file__).resolve().parents[1] / "services" / "decision-api" / "app.py"


def _api_module():
    spec = importlib.util.spec_from_file_location("vortex_runtime_profile_test", APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shadow_is_default_no_claim_of_production(monkeypatch):
    monkeypatch.delenv("VORTEX_RUNTIME_MODE", raising=False)
    module = _api_module()
    assert module.RUNTIME_MODE == "SHADOW_REFERENCE"
    assert module._validated_runtime_mode() == "SHADOW_REFERENCE"


def test_native_production_requires_feature_flag(monkeypatch):
    monkeypatch.setenv("VORTEX_RUNTIME_MODE", "PRODUCTION_NATIVE_GEO")
    monkeypatch.delenv("VORTEX_ENABLE_GEO_EVIDENCE_TRIAGE", raising=False)
    monkeypatch.setenv("VORTEX_GEO_SERVICE_TOKEN", "secret-test-only-abcdefghijklmnopqrstuvwxyz123")
    module = _api_module()
    with pytest.raises(RuntimeError, match="PRODUCTION_GEO_OPERATOR_NOT_ENABLED"):
        module._validated_runtime_mode()


def test_native_production_requires_real_backend_identity(monkeypatch):
    monkeypatch.setenv("VORTEX_RUNTIME_MODE", "PRODUCTION_NATIVE_GEO")
    monkeypatch.setenv("VORTEX_ENABLE_GEO_EVIDENCE_TRIAGE", "true")
    monkeypatch.delenv("VORTEX_GEO_SERVICE_TOKEN", raising=False)
    module = _api_module()
    with pytest.raises(RuntimeError, match="PRODUCTION_GEO_SERVICE_IDENTITY_MISSING"):
        module._validated_runtime_mode()


def test_native_production_accepts_scoped_identity_and_geo_feature(monkeypatch):
    monkeypatch.setenv("VORTEX_RUNTIME_MODE", "PRODUCTION_NATIVE_GEO")
    monkeypatch.setenv("VORTEX_ENABLE_GEO_EVIDENCE_TRIAGE", "true")
    monkeypatch.setenv("VORTEX_GEO_SERVICE_TOKEN", "test-credential-only-abcdefghijklmnopqrstuvwxyz1234")
    module = _api_module()
    assert module._validated_runtime_mode() == "PRODUCTION_NATIVE_GEO"
    monkeypatch.setenv("VORTEX_REQUIRE_EXACT_SOURCE", "false")
    response = module.app.test_client().get("/readyz")
    assert response.status_code == 200
    body = response.get_json()
    assert body["mode"] == "PRODUCTION_NATIVE_GEO"
    assert body["geopolitical_evidence_triage_enabled"] is True
    assert body["execution_authority"] is False


def test_unsupported_runtime_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("VORTEX_RUNTIME_MODE", "FULL_UNRESTRICTED_EXTERNAL_EFFECTS")
    module = _api_module()
    with pytest.raises(RuntimeError, match="VORTEX_RUNTIME_MODE_UNKNOWN"):
        module._validated_runtime_mode()
