# Prospective Case Acquisition and Adjudication V1.0

**Status:** FROZEN

This protocol governs admission and adjudication of real B1/B2 SHADOW cases. Engineering tests, demos, replays, qualification events, and synthetic cases are not prospective evidence.

## Canonical order

`Baseline -> Freeze -> Vortex_SHADOW -> Outcome -> Adjudication -> Score`

Never:

`Vortex -> Baseline`

## Admission requirements

Before the outcome is known, every primary case must record:

1. a real source event belonging to the declared B1 or B2 track;
2. evidence provenance and time fields;
3. a frozen `information_cutoff`;
4. a baseline decision and baseline actor frozen independently of Vortex;
5. `baseline_frozen_at <= information_cutoff` and the baseline freeze completed before Vortex observation;
6. an ex-ante outcome horizon after the information cutoff;
7. the exact protocol/freeze identity;
8. Vortex operating in SHADOW mode with no execution authority;
9. a source classification that excludes demo, replay, synthetic, or qualification evidence.

Missing or ambiguous baseline data makes the event ineligible. It must not be repaired retroactively by fabricating a baseline.

## Consecutive-case rule

Eligible cases are counted consecutively. A case cannot be removed because Vortex lost, timed out, abstained, produced an inconvenient result, or made the aggregate statistic worse.

## Adjudication

- Two reviewers independently score baseline and Vortex under the same predeclared loss function and outcome horizon.
- A third independent reviewer resolves disagreement.
- Conflicts of interest must be declared.
- Adjudicators must not alter the frozen baseline, Vortex decision, information cutoff, or outcome horizon.

## Evidence counters

B1 and B2 counters increment only after a natural operational event satisfies the frozen admission protocol. Engineering readiness does not increment a counter.

## Claim boundary

PASS on B1/B2 would support only the bounded claim demonstrated by those frozen tracks. It would not establish universal superiority, causal omniscience, or general prediction of the future.
