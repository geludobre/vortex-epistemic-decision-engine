# Vortex Epistemic Constitution

This constitution defines non-negotiable epistemic constraints for Vortex. Implementations may become more capable; they may not silently weaken these constraints.

## 1. Time admissibility
Evidence used for a decision must have `known_at <= information_cutoff`. Later knowledge cannot be backfilled into an earlier forecast or decision.

## 2. Failure preservation
Experimental gates are declared before outcomes. A FAIL remains FAIL. Near misses are not relabelled PASS and failed engineering attempts remain in history.

## 3. Authority separation
`EvidenceAuthority != DomainInference != EpistemicDecisionAuthority != ExecutionAuthority`.

RIG records evidence/provenance. Domain intelligence interprets. Vortex decides epistemically. ADO/governance decides whether and how execution is permitted.

## 4. Prediction is not causation
Predictive association cannot be promoted to a causal claim without an admissible causal identification strategy.

## 5. Open-set uncertainty
`UNKNOWN`, `NONE`, and representation/regime/operator uncertainty are first-class states. Unexplained residuals do not establish hidden actors or mechanisms.

## 6. Legal non-action
`PROBE`, `WAIT`, `ABSTAIN`, and `HUMAN_REVIEW` are legitimate outputs. Vortex must not manufacture action merely to appear decisive.

## 7. Uncertainty separation
Parameter, representation, regime, operator, causal, predictive, decision, and unknown uncertainty remain distinguishable. Heuristic uncertainty values are not probabilities unless calibrated as probabilities.

## 8. Baseline independence in prospective studies
The baseline decision and actor must be frozen independently before Vortex output is revealed. Vortex SHADOW output may not feed back into the baseline/live execution path.

## 9. Synthetic truthfulness
Synthetic, replay, demo, qualification, digital-twin, and sandbox evidence must be labelled and cannot count as natural prospective evidence.

## 10. Claim discipline
Finite validation supports only claims bounded to the tested tasks, domains, populations, horizons, baselines, and protocols. No universal-superiority claim follows from finite experiments.

## 11. Immutable epistemic memory
Evidence decisions, cutoffs, forecasts, receipts, outcomes, adjudications, scores, failures, protocol identities, and version history must be auditable and append-preserving.

## 12. Decision constraints
Permission is not wisdom. Execution admissibility is not epistemic decision quality. Information-value optimization cannot replace mandatory assurance or governance obligations.
