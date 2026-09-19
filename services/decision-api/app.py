from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from jsonschema import Draft202012Validator, FormatChecker

from vortex.decision.reference_engine import (
    DecisionRequest,
    EvidenceItem,
    ReferenceDecisionEngine,
)
from vortex.decision.cognitive_adapter import (
    AdoCognitiveDecisionAdapter,
    CognitiveDecisionError,
)
from vortex.decision.hitl_cognitive_adapter import (
    AdoHitlCognitiveDecisionAdapter,
    HitlCognitiveDecisionError,
)
from vortex.decision.seos_adapter import (
    AdoDiagnosticDecisionAdapter,
    DiagnosticDecisionError,
)

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_MODE = "SHADOW_REFERENCE"
REQUEST_SCHEMA_PATH = ROOT / "schemas" / "v1" / "decision-request.schema.json"
RESPONSE_SCHEMA_PATH = ROOT / "schemas" / "v1" / "decision-response.schema.json"
SOURCE_FILE = ROOT / "SOURCE_GIT_SHA"


def _load_json(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


REQUEST_VALIDATOR = Draft202012Validator(
    _load_json(REQUEST_SCHEMA_PATH), format_checker=FormatChecker()
)
RESPONSE_VALIDATOR = Draft202012Validator(
    _load_json(RESPONSE_SCHEMA_PATH), format_checker=FormatChecker()
)
ENGINE = ReferenceDecisionEngine()
DIAGNOSTIC_ADAPTER = AdoDiagnosticDecisionAdapter()
COGNITIVE_ADAPTER = AdoCognitiveDecisionAdapter()
HITL_COGNITIVE_ADAPTER = AdoHitlCognitiveDecisionAdapter()


def _truthy(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _exact_sha(value: str) -> bool:
    return len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def source_git_sha(*, required: bool = False) -> str | None:
    env_sha = os.environ.get("VORTEX_SOURCE_GIT_SHA", "").strip()
    file_sha = SOURCE_FILE.read_text(encoding="utf-8").strip() if SOURCE_FILE.is_file() else ""
    for label, value in (("VORTEX_SOURCE_GIT_SHA", env_sha), ("SOURCE_GIT_SHA", file_sha)):
        if value and not _exact_sha(value):
            raise RuntimeError(f"SOURCE_IDENTITY_REJECT: {label} must be exact lower-case 40-hex")
    if env_sha and file_sha and env_sha != file_sha:
        raise RuntimeError("SOURCE_IDENTITY_REJECT: environment and image source SHA differ")
    value = env_sha or file_sha or None
    if required and value is None:
        raise RuntimeError("SOURCE_IDENTITY_NOT_READY: exact source SHA is required")
    return value


def _schema_errors(validator: Draft202012Validator, payload: Any) -> list[str]:
    return [
        f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    ]


def _result_payload(result: Any) -> dict[str, Any]:
    payload = {
        "request_id": result.request_id,
        "decision": result.decision,
        "reason": result.reason,
        "admitted_evidence_ids": list(result.admitted_evidence_ids),
        "rejected_evidence_ids": list(result.rejected_evidence_ids),
        "information_cutoff": result.information_cutoff,
        "execution_authority": result.execution_authority,
        "receipt_sha256": result.receipt_sha256,
    }
    errors = _schema_errors(RESPONSE_VALIDATOR, payload)
    if errors:
        raise RuntimeError("RESPONSE_CONTRACT_REJECT: " + "; ".join(errors))
    if payload["execution_authority"] is not False:
        raise RuntimeError("CONSTITUTION_REJECT: Vortex reference runtime cannot grant execution authority")
    return payload


def _request_model(payload: dict[str, Any]) -> DecisionRequest:
    return DecisionRequest(
        request_id=payload["request_id"],
        information_cutoff=payload["information_cutoff"],
        evidence=tuple(
            EvidenceItem(
                evidence_id=item["evidence_id"],
                known_at=item["known_at"],
                payload=item["payload"],
                provenance_sha256=item.get("provenance_sha256"),
            )
            for item in payload["evidence"]
        ),
        objective=payload.get("objective", {}),
        constraints=payload.get("constraints", {}),
        mandatory_human_review=payload.get("mandatory_human_review", False),
    )


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("VORTEX_MAX_REQUEST_BYTES", "1048576"))


@app.after_request
def _headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Vortex-Mode"] = RUNTIME_MODE
    sha = None
    try:
        sha = source_git_sha(required=False)
    except RuntimeError:
        pass
    if sha:
        response.headers["X-Vortex-Source-SHA"] = sha
    return response


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "vortex-decision-api", "mode": RUNTIME_MODE})


@app.get("/readyz")
def readyz():
    try:
        required = _truthy("VORTEX_REQUIRE_EXACT_SOURCE", default=True)
        sha = source_git_sha(required=required)
        sentinel = ENGINE.evaluate(
            DecisionRequest(
                request_id="readiness-sentinel",
                information_cutoff="2026-01-01T00:00:00+00:00",
                evidence=(),
            )
        )
        if sentinel.execution_authority is not False:
            raise RuntimeError("CONSTITUTION_REJECT: readiness sentinel gained execution authority")
        return jsonify(
            {
                "status": "ready",
                "service": "vortex-decision-api",
                "mode": RUNTIME_MODE,
                "source_git_sha": sha,
                "execution_authority": False,
                "ado_diagnostic_action_enabled": _truthy(
                    "VORTEX_ENABLE_ADO_DIAGNOSTIC_ACTION", default=False
                ),
                "ado_cognitive_action_enabled": _truthy(
                    "VORTEX_ENABLE_ADO_COGNITIVE_ACTION", default=False
                ),
                "ado_hitl_cognitive_action_enabled": _truthy(
                    "VORTEX_ENABLE_ADO_HITL_COGNITIVE_ACTION", default=False
                ),
            }
        )
    except Exception as exc:
        return jsonify({"status": "not_ready", "reason": str(exc), "mode": RUNTIME_MODE}), 503





@app.post("/v1/decision/ado-hitl-cognitive")
def ado_hitl_cognitive():
    if not _truthy("VORTEX_ENABLE_ADO_HITL_COGNITIVE_ACTION", default=False):
        return jsonify(
            {
                "error": "HITL_COGNITIVE_OPERATOR_DISABLED",
                "detail": "ADO HITL cognitive action recommendation is disabled",
            }
        ), 503
    if not request.is_json:
        return jsonify(
            {"error": "UNSUPPORTED_MEDIA_TYPE", "detail": "application/json required"}
        ), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "MALFORMED_REQUEST", "detail": "JSON object required"}
        ), 400
    errors = _schema_errors(REQUEST_VALIDATOR, payload)
    if errors:
        return jsonify({"error": "REQUEST_CONTRACT_REJECT", "details": errors}), 400
    try:
        model = _request_model(payload)
        reference_result = ENGINE.evaluate(model)
        artifact = HITL_COGNITIVE_ADAPTER.build(
            request=model,
            reference_result=reference_result,
        )
        if artifact["execution_authority"] is not False:
            raise RuntimeError(
                "CONSTITUTION_REJECT: Vortex HITL cognitive adapter gained execution authority"
            )
        return jsonify(artifact)
    except HitlCognitiveDecisionError as exc:
        return jsonify(
            {"error": "HITL_COGNITIVE_ACTION_REJECT", "detail": str(exc)}
        ), 409
    except ValueError as exc:
        return jsonify(
            {"error": "REQUEST_SEMANTIC_REJECT", "detail": str(exc)}
        ), 400
    except Exception as exc:
        app.logger.exception("Vortex ADO HITL cognitive decision failed closed")
        return jsonify(
            {"error": "VORTEX_FAIL_CLOSED", "detail": str(exc)}
        ), 500


@app.post("/v1/decision/ado-cognitive")
def ado_cognitive():
    if not _truthy("VORTEX_ENABLE_ADO_COGNITIVE_ACTION", default=False):
        return jsonify(
            {
                "error": "COGNITIVE_OPERATOR_DISABLED",
                "detail": "ADO cognitive action recommendation is disabled",
            }
        ), 503
    if not request.is_json:
        return jsonify(
            {"error": "UNSUPPORTED_MEDIA_TYPE", "detail": "application/json required"}
        ), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "MALFORMED_REQUEST", "detail": "JSON object required"}
        ), 400
    errors = _schema_errors(REQUEST_VALIDATOR, payload)
    if errors:
        return jsonify({"error": "REQUEST_CONTRACT_REJECT", "details": errors}), 400
    try:
        model = _request_model(payload)
        reference_result = ENGINE.evaluate(model)
        artifact = COGNITIVE_ADAPTER.build(
            request=model,
            reference_result=reference_result,
        )
        if artifact["execution_authority"] is not False:
            raise RuntimeError(
                "CONSTITUTION_REJECT: Vortex cognitive adapter gained execution authority"
            )
        return jsonify(artifact)
    except CognitiveDecisionError as exc:
        return jsonify(
            {"error": "COGNITIVE_ACTION_REJECT", "detail": str(exc)}
        ), 409
    except ValueError as exc:
        return jsonify(
            {"error": "REQUEST_SEMANTIC_REJECT", "detail": str(exc)}
        ), 400
    except Exception as exc:
        app.logger.exception("Vortex ADO cognitive decision failed closed")
        return jsonify(
            {"error": "VORTEX_FAIL_CLOSED", "detail": str(exc)}
        ), 500


@app.post("/v1/decision/ado-diagnostic")
def ado_diagnostic():
    if not _truthy("VORTEX_ENABLE_ADO_DIAGNOSTIC_ACTION", default=False):
        return jsonify(
            {
                "error": "DIAGNOSTIC_OPERATOR_DISABLED",
                "detail": "ADO diagnostic action recommendation is disabled",
            }
        ), 503
    if not request.is_json:
        return jsonify(
            {"error": "UNSUPPORTED_MEDIA_TYPE", "detail": "application/json required"}
        ), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "MALFORMED_REQUEST", "detail": "JSON object required"}
        ), 400
    errors = _schema_errors(REQUEST_VALIDATOR, payload)
    if errors:
        return jsonify({"error": "REQUEST_CONTRACT_REJECT", "details": errors}), 400
    try:
        model = _request_model(payload)
        reference_result = ENGINE.evaluate(model)
        artifact = DIAGNOSTIC_ADAPTER.build(
            request=model,
            reference_result=reference_result,
        )
        if artifact["execution_authority"] is not False:
            raise RuntimeError(
                "CONSTITUTION_REJECT: Vortex diagnostic adapter gained execution authority"
            )
        return jsonify(artifact)
    except DiagnosticDecisionError as exc:
        return jsonify(
            {"error": "DIAGNOSTIC_ACTION_REJECT", "detail": str(exc)}
        ), 409
    except ValueError as exc:
        return jsonify(
            {"error": "REQUEST_SEMANTIC_REJECT", "detail": str(exc)}
        ), 400
    except Exception as exc:
        app.logger.exception("Vortex ADO diagnostic decision failed closed")
        return jsonify(
            {"error": "VORTEX_FAIL_CLOSED", "detail": str(exc)}
        ), 500

@app.post("/v1/decision/evaluate")
def evaluate():
    if not request.is_json:
        return jsonify({"error": "UNSUPPORTED_MEDIA_TYPE", "detail": "application/json required"}), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "MALFORMED_REQUEST", "detail": "JSON object required"}), 400
    errors = _schema_errors(REQUEST_VALIDATOR, payload)
    if errors:
        return jsonify({"error": "REQUEST_CONTRACT_REJECT", "details": errors}), 400
    try:
        result = ENGINE.evaluate(_request_model(payload))
        return jsonify(_result_payload(result))
    except ValueError as exc:
        return jsonify({"error": "REQUEST_SEMANTIC_REJECT", "detail": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Vortex decision evaluation failed closed")
        return jsonify({"error": "VORTEX_FAIL_CLOSED", "detail": str(exc)}), 500