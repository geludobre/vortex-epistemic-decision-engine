# C30.8 Runtime Lineage

**Status:** HISTORICAL LINEAGE RECORD — artifact metadata preserved; source ZIP bytes are not represented as migrated unless separately imported and hash-verified.

This document records the canonical lineage of the Vortex B1/B2 live-capture runtime produced before the GitHub SSOT consolidation. It exists to prevent loss of ancestry, frozen gates, test history, and known failures during migration.

## Migration rule

GitHub is the operational SSOT going forward. Historical ZIPs remain immutable evidence/history. A component is not considered migrated merely because its name or hash appears here.

For each historical artifact, migration requires:

1. source bytes available;
2. SHA-256 verified against this record;
3. public/private classification reviewed;
4. known failures preserved;
5. code/tests ported on a branch;
6. CI passing without changing frozen experimental gates;
7. provenance to the historical artifact recorded in commit/PR documentation.

## v0.2 — Decision API

Artifact: `VORTEX_C30_8_B1_B2_LIVE_CAPTURE_RUNTIME_V0_2_DECISION_API.zip`

SHA-256:

`7fda4700b26e3a2eb2c771a07c11d10a44fa233e8ca43bdd8665560da4fe19b7`

Recorded properties:

- baseline excluded from Vortex request;
- `known_at` firewall;
- SHADOW mode;
- canonical request SHA-256 binding;
- request/cutoff echo;
- fail-closed on malformed response/hash/cutoff/decision;
- full request-response receipt ancestry;
- tests: **11/11 PASS**.

## v0.3 — Real Decision Service

Artifact: `VORTEX_C30_8_B1_B2_LIVE_CAPTURE_RUNTIME_V0_3_REAL_DECISION_SERVICE.zip`

SHA-256:

`602e6a858bea0901949ef2e9fb773e56ef1afe7e00c42d6401778fb0d9664283`

Recorded interface:

- `POST /v1/decision`
- `/health`
- model version: `vortex-epistemic-controller-0.3.0`
- policy version: `vortex-admission-policy-0.3.0`

Controller status: interpretable reference controller, **not calibrated ML**.

Recorded B1 policy behavior:

- contradiction + high stakes -> `HUMAN_REVIEW`;
- missing assurance / weak evidence / open-set uncertainty -> `PROBE`;
- high stakes + intermediate evidence -> `WAIT`;
- otherwise `ACT`, SHADOW only.

Recorded B2 policy behavior:

- human authority required -> `HUMAN_REVIEW`;
- irreversible without safeguards -> `ABSTAIN`;
- incomplete evidence -> `PROBE` or `WAIT`;
- high stakes without policy authorization -> `WAIT`;
- bounded probe -> `PROBE`;
- otherwise `ACT`, SHADOW only.

Failure history:

- initial test run: **6 errors** caused by a test-fixture DB path leak;
- failure is preserved as engineering history;
- after fix: **24/24 PASS**.

## v0.4 — Prospective Scoring Harness

Artifact: `VORTEX_C30_8_B1_B2_LIVE_CAPTURE_RUNTIME_V0_4_PROSPECTIVE_SCORING_HARNESS.zip`

SHA-256:

`2555bfcb98a5c1022e63cc0323091f3b4553f3479f2b9d1e20db4d88fcecf486`

Added:

- scorecard;
- scoreboard;
- CSV scoreboard.

Primary paired improvement:

`DeltaLoss = Loss_baseline - Loss_Vortex`

Positive values favor Vortex.

Guardrails:

- observed outcome is not automatically converted into counterfactual loss;
- heuristic uncertainty is not a probability;
- Brier score only when a genuine ex-ante `forecast_probability` and `binary_outcome` exist.

Tests: **32/32 PASS**.

## v0.5 — Statistical Freeze

Artifact: `VORTEX_C30_8_B1_B2_LIVE_CAPTURE_RUNTIME_V0_5_STATISTICAL_FREEZE.zip`

Protocol SHA-256:

`20d187d15440c2115478a71177c941e953e2fd6b3288506f4a31c2e7b594bd90`

ZIP SHA-256:

`bb112357ba771b39fca6ad932cf17e995682d843e3aec5c2e5d05a2e2058de39`

Frozen target:

- 50 eligible cases per track;
- at least 45/50 valid primary adjudications;
- loss scale `{0, 0.25, 0.50, 0.75, 1.00}`;
- no intermediate primary-loss values;
- `Delta_i = L_baseline,i - L_Vortex,i`;
- primary endpoint: arithmetic mean paired improvement;
- paired non-parametric bootstrap, 10,000 resamples, seed 369, percentile 95% CI;
- minimum practically important effect: `mean(Delta) >= +0.10`;
- sign test: two-sided alpha 0.05, diagnostic only.

PASS iff all hold:

1. >=45/50 valid adjudications;
2. mean improvement >= +0.10;
3. lower 95% bootstrap CI > 0.

FAIL iff either holds:

- upper 95% bootstrap CI < 0; or
- mean improvement <= -0.10.

Otherwise: INCONCLUSIVE.

Tests: **39/39 PASS**.

## v0.6 — Prospective Case Intake

Artifact: `VORTEX_C30_8_B1_B2_LIVE_CAPTURE_RUNTIME_V0_6_PROSPECTIVE_CASE_INTAKE.zip`

SHA-256:

`7d5eef9077ff2049527a674fc37f1bb1e48c50d51c734c45efd3441efc875f39`

Lifecycle:

`CANDIDATE -> ELIGIBILITY_CHECKED -> FROZEN_UNSCORED -> OUTCOME_CAPTURED -> REVIEW_1 -> REVIEW_2 -> ADJUDICATED -> SCORED`

Public IDs:

- `B1-00001...`
- `B2-00001...`

Eligible B1 types:

- `CBAM_CLAIM_REVIEW`
- `ESG_CLAIM_ASSURANCE`

Eligible B2 types:

- `HIGH_RISK_AGENT_ACTION`
- `PRIVILEGED_EXECUTION_REQUEST`

Synthetic/demo/qualification cases are excluded from prospective evidence.

Adjudication: two independent reviewers plus third-reviewer tiebreak.

Tests: **45/45 PASS**.

Known defect preserved:

- automatic final score did not fully match v0.4 required fields `loss_scale` and `adjudication_method`.

This defect must not be erased from history.

## v0.7 — Real Source Gateway

Artifact: `VORTEX_C30_8_B1_B2_LIVE_CAPTURE_RUNTIME_V0_7_REAL_SOURCE_GATEWAY.zip`

SHA-256:

`48d97dc895d0d9a593db61508e971257b5d88cd4e5b80c53def407fad4424a3c`

Recorded endpoints:

- `POST /source-gateway/v1/b1/events`
- `POST /source-gateway/v1/b2/events`

Security controls:

- source registry;
- HMAC-SHA256;
- timestamp;
- nonce replay protection;
- 300-second replay window;
- source-track binding.

Accepted source kinds:

- `LIVE`
- `PRODUCTION_SHADOW`

Rejected source kinds:

- `SYNTHETIC`
- `DEMO`
- `QUALIFICATION`
- `REPLAY`

Tests: **51/51 PASS**.

Prospective counters remained `B1=0/50`, `B2=0/50`.

## v0.8 — Production Producer Integration Kit

Artifact: `VORTEX_C30_8_B1_B2_V0_8_PRODUCTION_PRODUCER_INTEGRATION_KIT.zip`

SHA-256:

`1863edc5d5deacc318d7c2f47841f36573be2cad006e6980073d756a0fdf2c`

Recorded contents:

- `producer_client.py`
- `b1_rig_esg_producer.py`
- `b2_ado_producer.py`
- environment example;
- deployment runbook;
- tests.

Recommended source IDs:

- `finbridge-rig-esg-prod`
- `sovereign-agentops-prod`

Separate >=128-bit secrets were required.

Critical invariant:

`Vortex output MUST NOT feed baseline/live execution.`

Tests: **54/54 PASS**.

Recorded state at v0.8:

`Prospective Collection Live = FALSE`

`B1=0/50`, `B2=0/50`.

## Scientific boundary

This lineage demonstrates increasingly mature engineering controls. It is not prospective evidence of real-world superiority. Historical test PASS values, demos, controlled runs, and qualification events cannot increment B1/B2 counters or support a universal-superiority claim.
