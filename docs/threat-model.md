# Vortex Threat Model

**Scope:** epistemic integrity of the public Vortex reference architecture.

This threat model focuses on ways a decision system can appear more certain, more causal, more successful, or more authoritative than its evidence permits.

## Protected properties

Vortex must preserve:

- time-admissible evidence;
- provenance;
- immutable frozen decisions and failures;
- baseline independence;
- explicit uncertainty and non-action states;
- authority separation;
- reproducible scoring;
- bounded claims.

## Threats and controls

### T1 — Temporal leakage

**Threat:** future-known information enters a historical or prospective decision.

**Controls:** mandatory `known_at`, frozen `information_cutoff`, timezone-aware timestamps, leakage falsification tests, reject evidence known after cutoff.

### T2 — Outcome leakage / baseline contamination

**Threat:** the baseline or feature set is selected after Vortex output or outcome knowledge.

**Controls:** canonical order `Baseline -> Freeze -> Vortex -> Outcome -> Score`; baseline freeze must precede Vortex observation.

### T3 — Post-hoc gate movement

**Threat:** thresholds, loss functions, cohorts, horizons, or exclusions are changed to rescue a result.

**Controls:** versioned frozen protocols; future changes apply only to future cases; prior result remains immutable.

### T4 — Selective case deletion

**Threat:** losses, abstentions, timeouts, or inconvenient cases are silently excluded.

**Controls:** consecutive-case rules, explicit adjudicability requirements, preserved system failures and abstentions.

### T5 — Evidence/inference collapse

**Threat:** a model score, inferred signal, or narrative is represented as observed fact.

**Controls:** typed artifact boundaries, provenance references, explicit evidence/inference classification, fail closed on missing source lineage.

### T6 — Causal overreach

**Threat:** predictive association is described as an intervention effect.

**Controls:** causal claims require a declared identification design; otherwise retain associational language and uncertainty.

### T7 — Hidden-actor hallucination

**Threat:** residual error or anomaly is treated as evidence of manipulation, intent, or an unseen agent.

**Controls:** residuals are model error signals, not actor evidence; competing explanations remain live until discriminating evidence exists.

### T8 — Authority confusion

**Threat:** an epistemic recommendation is treated as execution permission.

**Controls:** `EpistemicDecisionAuthority != ExecutionAuthority`; public reference outputs `execution_authority=false`; separate authorization/execution layer required.

### T9 — Abstention suppression

**Threat:** the system is optimized to always act, converting uncertainty into false confidence.

**Controls:** `PROBE`, `WAIT`, `ABSTAIN`, and `HUMAN_REVIEW` are legal first-class dispositions.

### T10 — Receipt/provenance tampering

**Threat:** a prior decision, evidence set, or score is changed without detection.

**Controls:** canonical hashing, append-oriented evidence, immutable version ancestry, separate outcome/adjudication artifacts.

### T11 — Model/version drift

**Threat:** a live model changes while a prospective program is evaluated, making cases incomparable.

**Controls:** model/protocol version identity in case evidence; prospective changes create a new version/cohort rather than silently mutating the old one.

### T12 — Data poisoning / source degradation

**Threat:** low-quality, manipulated, duplicated, or stale sources distort state reconstruction.

**Controls:** provenance, source class, freshness, corroboration/dependence checks where applicable, uncertainty escalation, `PROBE/WAIT/ABSTAIN` on insufficient support.

### T13 — Prompt or tool injection through evidence

**Threat:** untrusted evidence contains instructions that alter system behavior or trigger tools.

**Controls:** evidence is data, not authority; tools require separate policy; untrusted content cannot grant execution permission.

### T14 — Cross-domain overclaim

**Threat:** success in one domain or demo is generalized to unrelated domains.

**Controls:** demos establish portability only; empirical generalization requires separately controlled validation tracks.

### T15 — Synthetic-to-real claim laundering

**Threat:** simulated or synthetic evidence is counted as real prospective evidence.

**Controls:** source classification; demos/replays/qualification events do not increment prospective counters.

## Fail-closed response

When a protected property cannot be established, Vortex should prefer rejection, `WAIT`, `PROBE`, `ABSTAIN`, or `HUMAN_REVIEW` over invented certainty.

## Out of scope

This public document does not disclose private infrastructure topology, credentials, customer data, exploit details, or enterprise security controls. Security vulnerabilities should follow `SECURITY.md`.
