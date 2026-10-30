from __future__ import annotations

import math

import pytest

from vortex.admission import (
    AdmissionAction,
    OptionalExperimentAdmissionPolicy,
    wilson_lower_bound,
)


def test_c17_action_vocabulary_is_exposed_without_policy_claim() -> None:
    assert {item.value for item in AdmissionAction} == {
        "ALLOW",
        "ABSTAIN",
        "ESCALATE",
        "PROBE",
    }


def test_c5_20_known_admit_vector() -> None:
    policy = OptionalExperimentAdmissionPolicy()
    result = policy.evaluate(successes=266, trials=303)

    assert result.admitted is True
    assert math.isclose(result.wilson_lower_bound, 0.8435573393485024, rel_tol=0, abs_tol=1e-15)
    assert result.source_origin == "FROZEN_PROTOCOL_DERIVATION"


def test_c5_20_known_reject_vector() -> None:
    policy = OptionalExperimentAdmissionPolicy()
    result = policy.evaluate(successes=120, trials=188)

    assert result.admitted is False
    assert math.isclose(result.wilson_lower_bound, 0.5790656450186242, rel_tol=0, abs_tol=1e-15)


def test_c5_20_minimum_calibration_count_is_fail_closed() -> None:
    policy = OptionalExperimentAdmissionPolicy()
    # This observed rate has a lower bound above 0.80 in the frozen risk table,
    # but C5.20 requires at least 30 calibration observations.
    result = policy.evaluate(successes=25, trials=26)

    assert result.wilson_lower_bound > 0.80
    assert result.admitted is False
    assert result.reason == "insufficient calibration support"


@pytest.mark.parametrize(
    ("successes", "trials"),
    [(-1, 10), (11, 10), (0, 0)],
)
def test_wilson_invalid_counts_fail_closed(successes: int, trials: int) -> None:
    with pytest.raises(ValueError):
        wilson_lower_bound(successes, trials)
