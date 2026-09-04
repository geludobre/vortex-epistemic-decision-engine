# Statistical and Loss Function Freeze V1.0

**Status:** FROZEN

This file is the canonical public freeze for the primary B1/B2 prospective comparison gate. It must not be edited to improve results after outcomes are observed. A future change requires a new version and applies prospectively only.

## Unit of analysis

For each admissible paired case:

`Delta_i = Loss_baseline,i - Loss_Vortex,i`

Positive values favor Vortex. B1 and B2 are analyzed separately.

## Target and adjudicability

- 50 consecutive eligible cases per track.
- At least 45 of the first 50 require valid primary adjudication.
- If more than 10% of the first 50 lack an adjudicable primary outcome, the track is INCONCLUSIVE.

## Frozen primary loss scale

`{0, 0.25, 0.50, 0.75, 1.00}`

Intermediate primary-loss values are forbidden.

## Primary endpoint

Arithmetic mean paired loss improvement: `mean(Delta)`.

## Primary uncertainty interval

Paired non-parametric bootstrap of the mean delta:

- resamples: 10,000
- seed: 369
- interval: percentile 95% CI

## Sensitivity diagnostic

Exact paired sign test, two-sided alpha 0.05. This diagnostic cannot override the primary gate.

## Minimum practically important effect

`mean(Delta) >= +0.10`

## PASS

All conditions must hold:

1. at least 45/50 valid primary adjudications;
2. `mean(Delta) >= +0.10`;
3. lower 95% bootstrap CI > 0.

## FAIL

FAIL if either condition holds:

- upper 95% bootstrap CI < 0; or
- `mean(Delta) <= -0.10`.

Otherwise the result is INCONCLUSIVE.

## Immutability

A near miss remains a near miss. Failed cases cannot be removed because Vortex lost. Thresholds, seed, loss scale, primary estimand, and decision rules cannot be moved after outcomes are observed.
