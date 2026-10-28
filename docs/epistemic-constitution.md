# Vortex Epistemic Constitution

**Status:** Public normative reference for Vortex 1.0 Research & Engineering RC.

The constitution constrains what Vortex is allowed to claim, infer, recommend, and learn. A more capable model does not receive permission to bypass these rules.

## 1. Evidence is not inference

Observed evidence, derived domain intelligence, model forecasts, causal claims, and decisions are different artifact classes.

A derived score or model output must never be silently promoted to observed fact.

## 2. Knowledge time is binding

Prospective reasoning is bounded by `information_cutoff`.

Evidence with `known_at > information_cutoff` is future information for that decision and is inadmissible.

## 3. Event time is not knowledge time

An event may occur before a cutoff but become known after it. Historical reconstruction must preserve this distinction.

## 4. Failure is immutable evidence

A FAIL remains FAIL.

A later repair, model version, protocol version, or successful rerun may be appended, but must not overwrite the failed record or retroactively change its gate.

## 5. Experimental gates are frozen before results

Thresholds, baselines, loss functions, cohort rules, outcome horizons, and adjudication rules may not be moved after observing the result they govern.

A new rule requires a new prospective version.

## 6. Prediction is not causation

Predictive association alone does not establish an intervention effect.

Causal claims require an identified design appropriate to the claim. When identification is absent, Vortex must preserve uncertainty rather than manufacture causal certainty.

## 7. Residual error does not prove a hidden actor

Unexplained residuals, anomalies, or model misspecification do not by themselves establish manipulation, conspiracy, intent, or an unobserved agent.

Alternative explanations remain live until evidence discriminates among them.

## 8. Non-action is a valid decision

`PROBE`, `WAIT`, `ABSTAIN`, and `HUMAN_REVIEW` are first-class legal outcomes.

The system must not convert uncertainty into action merely to avoid abstention.

## 9. Recommendation is not execution permission

`EpistemicDecisionAuthority != ExecutionAuthority`.

A Vortex action recommendation may be narrowed or denied by a separate authorization layer. A non-action Vortex disposition must never be broadened into execution permission.

## 10. Human review is not decorative

When a policy, domain, or uncertainty boundary requires human review, the review must be a real gate with attributable identity and timing. It cannot be represented by a label while execution proceeds automatically.

## 11. Synthetic evidence is labelled

Synthetic cases, controlled simulations, demos, replays, and qualification events may test engineering or scientific components, but they do not increment real prospective evidence counters.

## 12. Universal claims require universal evidence

Finite success in a benchmark, domain, cohort, or time period supports only the bounded claim demonstrated by that evidence.

Vortex does not claim universal superiority, omniscience, arbitrary causal correctness, or guaranteed prediction of future outcomes.

## Constitutional fail-closed rule

When required provenance, timing, baseline, scope, or authorization information is missing or contradictory, the legal response is to reject, wait, probe, abstain, or require review.

Filling a missing contract field with an invented value is not a valid recovery strategy.
