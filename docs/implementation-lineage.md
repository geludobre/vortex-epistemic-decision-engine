# Vortex 1.0 Public Implementation Lineage Audit

**Date:** 2026-09-19  
**Status:** SOURCE-CUSTODY AUDIT FOR PUBLIC CODE MIGRATION  
**Purpose:** determine which historical Vortex elements can be ported as recovered source, which can only be reimplemented from frozen protocols, and which must remain failed/experimental evidence.

## Rule

A historical experiment name is not automatically a production/reference implementation.

Public migration uses three custody classes:

1. **RECOVERED_SOURCE** — executable source bytes survive and can be ported with source identity.
2. **FROZEN_PROTOCOL_DERIVATION** — protocol/config/results survive, but implementation source does not. Any public code is a new reference implementation derived from those artifacts and must be labelled as such.
3. **EXPERIMENTAL_RESULT_ONLY** — result evidence survives but is not sufficient to define a canonical implementation.

A PASS/FAIL result is preserved independently of source-custody class.

## Research Program archive

Physical archive:

- `VORTEX_Research_Program_v0.1.zip`
- SHA-256: `35281333c5cecca50f90dde7281b032fa768885b94a27b3a6634cc3e18057b45`

The archive contains frozen configs, raw/summary results, result freezes, hashes, validation reports, ontology/mathematical/backtesting/lab documents, E2 dossiers and E3 protocol material.

It does **not** contain a Python/package source tree for a monolithic Vortex v0.x engine.

The later `VORTEX_Research_Program_v0.1_E3_update.zip` (SHA-256 `cfadf51dc3e492ce5c4511c71c9575a30c338dc240beb24303e372ab6ece1fb0`) likewise contains research/evidence artifacts rather than a recoverable core implementation tree.

Therefore the phrase “migrate v0.2–v0.8 lineage” must not be interpreted as “copy a surviving v0.8 codebase”.

## Recovered executable source

The recovered Part 1 corpus contains executable Python primarily in the later E3 benchmark/reproduction layer, including:

- `vortex_challenger_v0.1.py`
- `materialize_views_arena_v0.1.py`
- `bridge_views_to_vortex_arena_v0.1.py`
- `score_vortex_transitions_v0.1.py`
- `score_calibration_significance_v0.1.py`
- UCDP/TOCSIN materialization and verification helpers.

These are benchmark/scoring/reproduction tools. They are not evidence that the complete epistemic controller, uncertainty engine, admission controller, or receipts package survived as source bytes.

They may be migrated only into appropriate benchmark/reproduction surfaces, preserving their scientific claim ceiling.

## Admission lineage

### C5.3 — Adaptive Value-of-Information Controller v0.2

Archive:

- `VORTEX_C5_3_VOI_Controller_v0.2.zip`
- SHA-256: `c1df68075f07b0e837fd62bdb497f17c4d541afc9cc45b2e2f14538682dbb478`

Custody: **FROZEN_PROTOCOL_DERIVATION**

The package contains frozen config, episode results, hashes, report and result freeze — not controller source.

The v0.2 design changed architecture after v0.1 over-probing while preserving gates. It still ended **FAIL**:

- regret vs oracle gate: FAIL;
- improvement vs static: FAIL;
- improvement vs fixed probe: FAIL;
- probe-rate cap: PASS;
- post-detection best-action accuracy: FAIL.

No public canonical VOI controller may be advertised as validated from this experiment.

### C5.20 — Risk-Calibrated Optional Experiment Admission v0.1

Archive:

- `VORTEX_C5_20_Risk_Calibrated_Optional_Experiment_Admission_v0.1.zip`
- SHA-256: `11871103a1960d29ab760cd31500449b1c3838623465853f0b70d38fd2ed087b`

Custody: **FROZEN_PROTOCOL_DERIVATION**

The package preserves a calibration-derived risk policy and holdout evidence, not source code.

Frozen rule:

> admit an optional experiment only if the Wilson lower bound for the probability of positive realized optional value, conditional on state, is at least 0.80.

The calibration policy was frozen before holdout; holdout retuning was false.

Controlled holdout result: **PASS** across the eight frozen gates, including:

- structural precision;
- claim coverage;
- optional-unnecessary-rate cap;
- optional positive-value rate;
- mean optional-experiment cap;
- constant-family precision;
- UNKNOWN when unresolved;
- no holdout retuning.

Claim ceiling: controlled synthetic optional-experiment admission only. This is not evidence that a general real-world action-admission controller is validated.

### C17.1 — Unified Admission Controller

Archive SHA-256: `4a33e8871425cb534f42ff8370476e255b9f950721755c0234d128c95bf58c2f`

Custody: **FROZEN_PROTOCOL_DERIVATION**

Overall: **FAIL**.

The controller did not meet the frozen minimum gain versus always-on, though the always-off comparison, harmful-activation cap, activation-range and no-retuning gates passed.

### C17.2 — ALLOW / ABSTAIN / ESCALATE / PROBE

Archive SHA-256: `403316549916936724803f543921234e268565693a107b1cdca10344167e0d77`

Custody: **FROZEN_PROTOCOL_DERIVATION**

Overall: **FAIL**.

The four-way policy substantially reduced catastrophic errors in the synthetic benchmark, but failed its frozen utility-gain gate versus the simpler binary comparator.

The action vocabulary is useful as a **semantic design donor**, not performance evidence.

### C17.3 — Admission Regret Benchmark

Archive SHA-256: `b573e1ddcdba18f8c52d242ff4ff8411db156ad52aa7e17ba7664ba2864f4059`

Custody: **EXPERIMENTAL_RESULT_ONLY / PROTOCOL AVAILABLE**

Overall: **FAIL**.

The controller reduced regret versus always-off but failed the frozen regret-reduction gate versus always-on and exceeded the maximum mean regret.

### C17.4 — Complexity Admission Principle

Archive SHA-256: `1ca5ab8efc10d8221210ac357c5f723968dbe900ab4cf8964e11f5c84bde3d47`

Custody: **EXPERIMENTAL_RESULT_ONLY / PROTOCOL AVAILABLE**

Overall: **FAIL**.

The synthetic controller reduced compute substantially and remained close to its synthetic oracle, but failed the frozen minimum net-gain gate versus maximum complexity.

It is not a real LLM-compute benchmark.

## Public migration consequence

The public target packages remain valid architectural destinations:

- `vortex/decision_api/`
- `vortex/epistemic_controller/`
- `vortex/uncertainty/`
- `vortex/admission/`
- `vortex/scoring/`
- `vortex/receipts/`

But implementation provenance differs by package.

### Safe now

- deterministic receipt/hash primitives already present in the public reference core;
- information-cutoff / time-admission logic already present and tested;
- explicit non-action semantics;
- benchmark/scoring utilities where exact source bytes survive;
- data/contract types derived from frozen semantics, when labelled as a new public reference implementation.

### Not safe to claim as “recovered implementation”

- a general v0.8 epistemic controller;
- a validated unified admission controller;
- a validated four-way meta-policy;
- a general uncertainty engine;
- a production action policy inferred only from experiment reports.

## First Step-2 implementation rule

The first new public modules should expose **conservative primitives and contracts**, not resurrect failed policies.

For admission specifically:

- preserve `ALLOW / ABSTAIN / ESCALATE / PROBE` as semantic vocabulary where useful;
- preserve UNKNOWN/non-action legality;
- expose no default learned admission policy;
- treat C5.20 risk-calibrated optional experiment admission as a separately labelled controlled-reference example if implemented;
- preserve C17.1–C17.4 as failure evidence and regression/design targets, not as successful algorithms.

## Future provenance requirement

Every migrated public module must state one of:

- `source_origin: RECOVERED_SOURCE`
- `source_origin: FROZEN_PROTOCOL_DERIVATION`
- `source_origin: NEW_REFERENCE_IMPLEMENTATION`

and name the source artifacts/commit identities that justify its semantics.

This prevents a clean Git history from erasing the actual experimental history.
