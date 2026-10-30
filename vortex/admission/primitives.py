"""Conservative admission primitives derived from frozen Vortex experiments.

No function in this module grants real-world execution authority.

C17.2 supplies the semantic vocabulary ALLOW / ABSTAIN / ESCALATE / PROBE,
but the C17.2 meta-policy failed its frozen utility-gain gate. Therefore this
module exposes the vocabulary only and does not ship that failed policy.

C5.20 supplies a narrower controlled rule for whether an *optional experiment*
should be admitted based on a calibration-only Wilson lower confidence bound.
C5.20 passed its frozen synthetic holdout gates and prohibited holdout retuning.
The reference implementation below reproduces only that frozen mathematical
admission rule; it is not a general action-admission policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt


SOURCE_ORIGIN = "FROZEN_PROTOCOL_DERIVATION"
C5_20_ARCHIVE_SHA256 = (
    "11871103a1960d29ab760cd31500449b1c3838623465853f0b70d38fd2ed087b"
)
C17_2_ARCHIVE_SHA256 = (
    "403316549916936724803f543921234e268565693a107b1cdca10344167e0d77"
)


class AdmissionAction(str, Enum):
    """Semantic vocabulary from C17.2, without the failed C17.2 meta-policy."""

    ALLOW = "ALLOW"
    ABSTAIN = "ABSTAIN"
    ESCALATE = "ESCALATE"
    PROBE = "PROBE"


def wilson_lower_bound(successes: int, trials: int, z: float = 1.645) -> float:
    """Wilson-score lower confidence bound for a Bernoulli success rate.

    The default z=1.645 is frozen by C5.20 v0.1.
    """

    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("successes and trials must be integers, not booleans")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("successes and trials must be integers")
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must satisfy 0 <= successes <= trials")
    if z <= 0:
        raise ValueError("z must be positive")

    p_hat = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = p_hat + z2 / (2.0 * trials)
    radius = z * sqrt(
        (p_hat * (1.0 - p_hat) / trials) + (z2 / (4.0 * trials * trials))
    )
    return (center - radius) / denominator


@dataclass(frozen=True)
class OptionalExperimentAdmissionResult:
    """Result of the narrow C5.20 optional-experiment admission rule."""

    admitted: bool
    trials: int
    successes: int
    wilson_lower_bound: float
    probability_floor: float
    min_calibration_n: int
    reason: str
    source_origin: str = SOURCE_ORIGIN


@dataclass(frozen=True)
class OptionalExperimentAdmissionPolicy:
    """Reference implementation of the frozen C5.20 v0.1 risk rule.

    Frozen defaults:
    - Wilson z = 1.645
    - success probability lower-bound floor = 0.80
    - minimum calibration sample size = 30

    No holdout/adaptive retuning is implemented here.
    """

    probability_floor: float = 0.80
    wilson_z: float = 1.645
    min_calibration_n: int = 30

    def __post_init__(self) -> None:
        if not 0.0 < self.probability_floor <= 1.0:
            raise ValueError("probability_floor must be in (0, 1]")
        if self.wilson_z <= 0:
            raise ValueError("wilson_z must be positive")
        if self.min_calibration_n <= 0:
            raise ValueError("min_calibration_n must be positive")

    def evaluate(self, *, successes: int, trials: int) -> OptionalExperimentAdmissionResult:
        lower = wilson_lower_bound(successes, trials, self.wilson_z)

        if trials < self.min_calibration_n:
            return OptionalExperimentAdmissionResult(
                admitted=False,
                trials=trials,
                successes=successes,
                wilson_lower_bound=lower,
                probability_floor=self.probability_floor,
                min_calibration_n=self.min_calibration_n,
                reason="insufficient calibration support",
            )

        admitted = lower >= self.probability_floor
        return OptionalExperimentAdmissionResult(
            admitted=admitted,
            trials=trials,
            successes=successes,
            wilson_lower_bound=lower,
            probability_floor=self.probability_floor,
            min_calibration_n=self.min_calibration_n,
            reason=(
                "Wilson lower bound meets frozen probability floor"
                if admitted
                else "Wilson lower bound is below frozen probability floor"
            ),
        )
