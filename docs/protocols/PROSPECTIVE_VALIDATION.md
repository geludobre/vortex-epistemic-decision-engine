# Prospective Validation Protocol — Public Summary

This document records the frozen public logic for the B1/B2 prospective comparison program. It is not evidence that either track has passed.

## Primary estimand

For each admissible paired case:

`Delta_i = Loss_baseline,i - Loss_Vortex,i`

Positive values favor Vortex. B1 and B2 are analyzed separately and may not be pooled to manufacture a PASS.

## Target

50 consecutive eligible cases per track.

A track requires at least 45/50 valid primary adjudications. If more than 10% of the first 50 lack an adjudicable primary outcome, the track is INCONCLUSIVE.

## Primary loss scale

`{0, 0.25, 0.50, 0.75, 1.00}`

Intermediate values are forbidden in the frozen primary analysis to avoid false precision.

## Admission invariants

A prospective case is eligible only when, before the outcome:

- the source event is real and belongs to the declared B1/B2 track;
- evidence provenance and time fields are present;
- the information cutoff is frozen;
- the baseline decision and actor are frozen independently of Vortex;
- the baseline freeze occurs before Vortex observation;
- the outcome horizon is defined ex ante;
- the exact protocol/freeze identity is recorded;
- Vortex operates in SHADOW mode;
- demo, qualification, replay, and synthetic events are excluded from prospective evidence.

Cases cannot be removed because Vortex lost.

## Adjudication

Two reviewers independently score the baseline and Vortex decisions under the same predeclared loss function and horizon. A third independent reviewer resolves disagreement. Conflicts of interest must be declared.

## Statistical gate

Primary endpoint: arithmetic mean paired loss improvement.

Primary uncertainty interval: paired non-parametric bootstrap of the mean delta, 10,000 resamples, fixed seed 369, percentile 95% CI.

Sensitivity diagnostic: exact paired sign test, two-sided alpha 0.05. The sensitivity test cannot override the primary gate.

Minimum practically important effect:

`mean(Delta) >= 0.10`

### PASS

All must hold:

1. at least 45/50 valid primary adjudications;
2. mean paired loss improvement >= +0.10;
3. lower 95% bootstrap CI > 0.

### FAIL

FAIL if either:

- upper 95% bootstrap CI < 0; or
- mean paired loss improvement <= -0.10.

Otherwise the result is INCONCLUSIVE.

A near miss remains a near miss. Thresholds must not be moved after outcomes are observed.

## Claim boundary

Even if both B1 and B2 pass, the admissible claim is limited to demonstrated cross-domain incremental utility in those frozen tracks. It does not establish universal superiority.
