# Vortex 1.0 Architecture

**Status:** Research & Engineering Release Candidate architecture. This document defines the public reference architecture, not an execution platform or a universal-performance claim.

## Purpose

Vortex is a failure-preserving epistemic decision architecture for decisions under incomplete evidence, regime change, uncertainty, and asymmetric consequences.

The canonical reasoning loop is:

`Evidence -> State -> Representation -> Regime -> Operator -> Future -> Decision -> Reality -> Learning`

The canonical state notation is:

`V_t = (E_t, S_t, R_t, Z_t, O_t, G_t, F_t, U_t, J_t, M_t)`

where the components represent evidence, state, representation, regime, operator, goals/constraints, futures, uncertainty, judgment/decision state, and memory/evaluation state. Implementations may specialize these fields, but may not erase provenance, uncertainty, or the information cutoff.

## Ecosystem boundary

The public architectural boundary is:

`RIG -> Domain Intelligence -> Vortex -> governed authorization/execution -> Reality -> RIG`

Authority separation is mandatory:

`EvidenceAuthority != DomainInference != EpistemicDecisionAuthority != ExecutionAuthority`

Vortex owns epistemic disposition and recommendation semantics. It does not grant permission to execute a real-world side effect.

## Time-admissible evidence

Every prospective decision requires a frozen `information_cutoff`.

Evidence is admissible only when its `known_at` is no later than that cutoff. Event time and knowledge time are distinct. A later-discovered fact about an earlier event cannot be silently injected into a historical decision state.

The public reference engine demonstrates this firewall directly.

## Decision semantics

Legal non-action outcomes include:

- `PROBE`
- `WAIT`
- `ABSTAIN`
- `HUMAN_REVIEW`

A domain adapter may produce a bounded action recommendation only when its own contract is satisfied. A recommendation remains non-executing and must preserve `execution_authority=false`.

## Domain operators

The public reference core intentionally does not invent a universal domain operator.

Domain-specific models and inference layers may supply:

- state estimates;
- forecasts/distributions;
- regime hypotheses;
- causal or counterfactual analysis;
- candidate interventions;
- uncertainty and failure modes.

Those outputs must remain distinguishable from observed evidence and must carry sufficient provenance to reproduce the decision state.

## Failure-preserving learning

Learning is append-oriented:

`frozen decision -> observed outcome -> adjudication -> score -> later model update`

A later model version may supersede a prior model for future decisions. It may not rewrite the prior forecast, decision, gate, or outcome.

## Public/private separation

This repository contains publishable architecture, schemas, reference components, frozen protocols, falsification tests, benchmarks, and synthetic examples.

Private deployment configuration, customer evidence, production endpoints, credentials, enterprise-only integrations, live-study ledgers, and commercial material belong in the private `vortex-enterprise` program repository or the owning component repository.

## Reference implementation boundary

The reference implementation prioritizes auditable invariants over feature breadth:

- deterministic receipts;
- time-admissible evidence;
- explicit abstention/non-action;
- immutable evaluation semantics;
- no execution authority.

A production domain operator may be more capable than the public reference engine, but it may not weaken these invariants.
