# Vortex Epistemic Decision Engine

**Failure-Preserving Epistemic Decision Architecture** for decisions under incomplete evidence, changing regimes, model uncertainty, and asymmetric consequences.

> **Status:** Research & Engineering Release Candidate. Controlled engineering validation exists; universal superiority is **not** claimed. Prospective validation remains in progress.

## Mission

Vortex reconstructs uncertain system state from time-admissible evidence, selects representations/regimes/operators, generates future distributions with explicit uncertainty, evaluates causal interventions, chooses constrained actions, and learns from immutable outcomes without rewriting prior failures.

Canonical flow:

`Evidence -> State -> Representation -> Regime -> Operator -> Future -> Decision -> Reality -> Learning`

Canonical state:

`V_t = (E_t, S_t, R_t, Z_t, O_t, G_t, F_t, U_t, J_t, M_t)`

## Core invariants

- `known_at` cutoff is mandatory for prospective reasoning.
- No retroactive experimental gates.
- A FAIL remains FAIL.
- Prediction is not causation.
- Residual error does not justify hidden-actor claims.
- `UNKNOWN`, `WAIT`, `PROBE`, `ABSTAIN`, and human review are legal outcomes.
- Synthetic/controlled validation is labelled as such.
- Finite validation never licenses a universal claim.
- Epistemic decision authority is separate from execution authority.

## Ecosystem boundary

`RIG -> Domain Intelligence -> Vortex -> Sovereign AgentOps -> Reality -> RIG`

- **RIG:** evidence/provenance authority.
- **Domain Intelligence:** domain interpretation and derived signals.
- **Vortex:** epistemic decision plane.
- **Sovereign AgentOps / ADO:** governance and execution plane.

`EvidenceAuthority != DomainInference != EpistemicDecisionAuthority != ExecutionAuthority`

## Repository scope

This **public** repository is the canonical home for publishable Vortex architecture, epistemic constitution, schemas, reference decision components, frozen experimental protocols, falsification tests, and synthetic examples.

It must not contain customer data, credentials, private FinBridge endpoints, proprietary deployment configuration, or enterprise-only integrations. Those belong in the private `vortex-enterprise` repository.

## Planned structure

```text
vortex/
  decision/
  uncertainty/
  receipts/
services/
  decision-api/
  prospective-intake/
schemas/
docs/
  architecture/
  protocols/
  validation/
experiments/
tests/
examples/
```

## Claim discipline

Vortex is currently best described as a **failure-preserving epistemic decision architecture**, not as a universally superior predictor, universal equation, or autonomous execution authority.

Engineering readiness is not prospective evidence. Prospective B1/B2 counters remain evidence-bearing only when real cases satisfy the frozen admission protocol.

## Security

Do not report exploitable vulnerabilities in public issues. See `SECURITY.md`.

## License

License terms are intentionally not declared by this bootstrap commit. Until a license is explicitly added, no open-source license grant should be inferred merely from public repository visibility.
