# Statistical Validation

**Status:** Public validation discipline for Vortex 1.0 Research & Engineering RC.

Architecture correctness, engineering reliability, retrospective benchmark performance, and prospective incremental utility are separate claims. They must not be collapsed into one status.

## Validation layers

### Engineering validation

Tests deterministic behavior, schemas, temporal leakage controls, receipts, API contracts, and failure handling.

Engineering PASS proves the tested implementation property only.

### Controlled / synthetic validation

Uses known or controlled ground truth to exercise components such as state estimation, transition detection, causal recovery under identified conditions, or replanning under a declared shift model.

Controlled evidence must remain labelled as controlled/synthetic.

### Retrospective benchmarking

Uses historical outcomes to compare models or design alternatives.

Retrospective results are useful for research and model development but are not, by themselves, prospective certification.

### Prospective validation

The decision/baseline and evidence cutoff are frozen before the outcome.

For the public B1/B2 protocol the canonical order is:

`Baseline -> Freeze -> Vortex_SHADOW -> Outcome -> Adjudication -> Score`

See:

- `protocols/STATISTICAL_AND_LOSS_FUNCTION_FREEZE_V1_0.md`
- `protocols/PROSPECTIVE_CASE_ACQUISITION_ADJUDICATION_V1_0.md`

## Frozen B1/B2 primary gate

Per track:

- 50 consecutive eligible cases;
- at least 45/50 valid primary adjudications;
- primary loss scale `{0, 0.25, 0.50, 0.75, 1.00}`;
- `Delta_i = Loss_baseline,i - Loss_Vortex,i`;
- primary estimand: arithmetic mean `mean(Delta)`;
- paired non-parametric bootstrap: 10,000 resamples, seed 369, percentile 95% CI;
- minimum practically important effect: `mean(Delta) >= +0.10`.

PASS, FAIL, and INCONCLUSIVE rules are defined only in the frozen protocol and must not be reinterpreted after outcomes.

## Consecutive-case discipline

An eligible case cannot be dropped because Vortex:

- lost;
- timed out;
- abstained;
- produced an inconvenient answer;
- worsened the aggregate result.

Missing or ambiguous pre-outcome baseline data makes a case ineligible; a baseline cannot be fabricated after Vortex output is known.

## Calibration and comparison

A lower point loss than a comparator is not automatically statistically demonstrated superiority.

Where clustered or repeated observations exist, uncertainty estimation must respect the data-generating unit. Calibration, transition behavior, horizon effects, and tail/failure modes should be reported alongside aggregate scores where applicable.

## Research & Engineering RC meaning

The Research & Engineering Release Candidate status means the architecture and engineering validation program reached its declared RC audit boundary.

It does **not** mean:

- universal superiority has been demonstrated;
- every domain operator is validated;
- prospective B1/B2 evidence is complete;
- every external benchmark has passed;
- production execution authority belongs to Vortex.

## Prospective external programs

Prospective programs such as NOAA or ECB/FX remain unscored until their frozen target period is complete and their predeclared source/QC/adjudication requirements are satisfied.

Premature scoring converts a prospective test into retrospective analysis and is prohibited.

## Publication rule

A performance claim should identify at least:

- population/domain;
- time period;
- information cutoff;
- comparator/baseline;
- frozen loss function;
- sample/adjudicability counts;
- uncertainty interval;
- protocol version;
- known exclusions/failures.

Claims without this context are not Vortex scientific evidence.
