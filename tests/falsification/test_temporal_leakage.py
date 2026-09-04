from vortex.decision.reference_engine import DecisionRequest, EvidenceItem, ReferenceDecisionEngine


def test_future_evidence_cannot_change_admitted_set_or_decision():
    engine = ReferenceDecisionEngine()
    base = DecisionRequest(
        request_id="temporal-1",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(EvidenceItem("past", "2026-09-04T09:00:00Z", {"value": 1}),),
    )
    contaminated = DecisionRequest(
        request_id="temporal-1",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(
            EvidenceItem("past", "2026-09-04T09:00:00Z", {"value": 1}),
            EvidenceItem("future", "2026-09-05T09:00:00Z", {"outcome": "known later"}),
        ),
    )

    clean_result = engine.evaluate(base)
    contaminated_result = engine.evaluate(contaminated)

    assert clean_result.decision == contaminated_result.decision == "ABSTAIN"
    assert clean_result.admitted_evidence_ids == contaminated_result.admitted_evidence_ids == ("past",)
    assert contaminated_result.rejected_evidence_ids == ("future",)
    assert contaminated_result.execution_authority is False
