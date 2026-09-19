# Decision API — Reference Contract

This directory defines the public HTTP boundary that will wrap the reference engine.

## Planned endpoint

`POST /v1/decision/evaluate`

Input: `schemas/v1/decision-request.schema.json`

Output: `schemas/v1/decision-response.schema.json`

## Non-negotiable invariants

- The API accepts only time-admissible evidence for epistemic reasoning.
- Evidence with `known_at > information_cutoff` cannot influence the decision.
- The response never grants execution permission: `execution_authority=false`.
- `WAIT`, `ABSTAIN`, `PROBE`, and `HUMAN_REVIEW` are first-class outcomes.
- Domain action selection must be provided by a separately versioned operator contract; this public bootstrap does not fabricate one.
- Decision receipts are deterministic over the canonical response payload.

The executable transport adapter will be added only after the operator/VCRF contract is migrated from a canonical source artifact and covered by contract tests.
