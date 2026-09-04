# Contributing to Vortex

Vortex is a failure-preserving epistemic decision architecture. Contributions are welcome only when they preserve its experimental and authority boundaries.

## Non-negotiable invariants

1. Never rewrite a historical FAIL into PASS.
2. Never change a frozen gate after observing outcomes.
3. Preserve `observed_at`, `known_at`, information cutoffs, provenance and receipt ancestry.
4. Prediction is not causation.
5. Synthetic, demo, replay and qualification data must never be represented as prospective evidence.
6. `UNKNOWN`, `PROBE`, `WAIT`, `ABSTAIN` and human review remain legal outcomes.
7. Vortex epistemic decisions do not grant execution authority.
8. No universal-superiority claim may be inferred from finite validation.

## Pull requests

A PR that changes decision logic, admission, scoring, receipts or experimental protocols should include:
- the invariant being changed or preserved;
- tests or falsification cases;
- compatibility/claim impact;
- whether the change affects a frozen protocol;
- explicit migration/versioning if historical reproducibility could change.

Frozen protocols are immutable. Corrections require a new version while preserving the prior artifact and its status.

## Tests

Prefer tests that attempt to falsify the claimed behavior. In particular test time leakage, baseline leakage, malformed evidence, open-set uncertainty, unavailable dependencies and authority-boundary violations.

## Security

Do not disclose exploitable vulnerabilities publicly. Follow `SECURITY.md`.
