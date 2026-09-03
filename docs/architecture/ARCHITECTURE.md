# Vortex Architecture

## Category

**Failure-Preserving Epistemic Decision Architecture**

## Mission

Reconstruct uncertain system state from time-admissible evidence, select representations/regimes/operators, generate future distributions, evaluate causal interventions, choose constrained actions, and learn from immutable outcomes without rewriting prior failures.

## Canonical pipeline

`Evidence -> State -> Representation -> Regime -> Operator -> Future -> Decision -> Reality -> Learning`

## Canonical tuple

`V_t = (E_t, S_t, R_t, Z_t, O_t, G_t, F_t, U_t, J_t, M_t)`

- `E`: evidence with provenance, epistemic status, `observed_at`, `known_at`.
- `S`: posterior over latent system state.
- `R`: candidate representations and posterior weights.
- `Z`: regime posterior including UNKNOWN.
- `O`: operator/model/policy posterior including NONE/UNKNOWN.
- `G`: observed graph plus probabilistic latent structure.
- `F`: future manifold/distribution.
- `U`: separated uncertainty vector.
- `J`: objectives, constraints, stakes, horizon, risk tolerances.
- `M`: immutable epistemic memory: evidence decisions, forecasts, receipts, outcomes, scores, failures, version history.

## Uncertainty

`U = (U_parameter, U_representation, U_regime, U_operator, U_causal, U_predictive, U_decision, U_unknown)`

These components should not be collapsed into a single confidence number without a validated mapping.

## Action space

`A = {domain actions, PROBE, WAIT, ABSTAIN}` plus explicit human review where governance requires it.

Decision optimization is constrained by objectives, risk tolerances, evidence sufficiency, and catastrophe constraints. Permission to execute remains outside Vortex.

## Four-plane ecosystem

1. **Evidence & Provenance Plane — RIG**: what evidence supports the decision?
2. **Domain Interpretation Plane**: what does that evidence mean in this domain?
3. **Epistemic Decision Plane — Vortex**: should the system act, probe, wait, abstain, or escalate?
4. **Governance & Execution Plane — Sovereign AgentOps / ADO**: may and can the action execute under policy?

`EvidenceAuthority != DomainInference != EpistemicDecisionAuthority != ExecutionAuthority`

## Learning loop

`OBSERVE -> MODEL -> HYPOTHESIZE -> SIMULATE -> PREDICT -> TEST -> COMPARE -> LEARN -> UPDATE -> REPEAT`

Learning may update future models and policies. It must not rewrite historical evidence cutoffs, frozen baselines, receipts, outcomes, or experimental gates.
