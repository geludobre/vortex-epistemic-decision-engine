import pytest

from vortex.decision.reference_engine import DecisionRequest, EvidenceItem, ReferenceDecisionEngine


def test_no_admissible_evidence_waits():
    request = DecisionRequest(
        request_id="r1",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(EvidenceItem("future", "2026-09-04T10:00:01Z", {"x": 1}),),
    )
    result = ReferenceDecisionEngine().evaluate(request)
    assert result.decision == "WAIT"
    assert result.admitted_evidence_ids == ()
    assert result.rejected_evidence_ids == ("future",)
    assert result.execution_authority is False


def test_admissible_evidence_without_domain_operator_abstains():
    request = DecisionRequest(
        request_id="r2",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(EvidenceItem("e1", "2026-09-04T09:59:59Z", {"signal": "x"}),),
    )
    result = ReferenceDecisionEngine().evaluate(request)
    assert result.decision == "ABSTAIN"
    assert result.admitted_evidence_ids == ("e1",)


def test_human_review_constraint_dominates_reference_policy():
    request = DecisionRequest(
        request_id="r3",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(EvidenceItem("e1", "2026-09-04T09:00:00Z", {}),),
        mandatory_human_review=True,
    )
    result = ReferenceDecisionEngine().evaluate(request)
    assert result.decision == "HUMAN_REVIEW"
    assert result.execution_authority is False


def test_naive_information_cutoff_is_rejected():
    request = DecisionRequest(request_id="r4", information_cutoff="2026-09-04T10:00:00")
    with pytest.raises(ValueError):
        ReferenceDecisionEngine().evaluate(request)


def test_receipt_is_deterministic_for_same_semantics():
    engine = ReferenceDecisionEngine()
    a = DecisionRequest(
        request_id="r5",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(
            EvidenceItem("b", "2026-09-04T09:00:00Z", {}),
            EvidenceItem("a", "2026-09-04T09:00:00Z", {}),
        ),
    )
    b = DecisionRequest(
        request_id="r5",
        information_cutoff="2026-09-04T10:00:00Z",
        evidence=(
            EvidenceItem("a", "2026-09-04T09:00:00Z", {}),
            EvidenceItem("b", "2026-09-04T09:00:00Z", {}),
        ),
    )
    assert engine.evaluate(a).receipt_sha256 == engine.evaluate(b).receipt_sha256
