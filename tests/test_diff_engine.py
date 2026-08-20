from datetime import UTC, datetime

from app.demo import create_demo_case, observe_bill
from app.diff_engine import reconcile
from app.domain import EvidenceRef, Observation, Term


def test_explicit_installation_mismatch_is_350():
    case = observe_bill(create_demo_case())
    assert case.reality_diff.net_amount == 350
    delta = next(item for item in case.reality_diff.deltas if item.key == "installation_fee")
    assert delta.material is True
    assert delta.classification == "unexplained"


def test_matching_credit_explains_added_fee():
    case = create_demo_case()
    evidence = EvidenceRef(
        id="e", filename="bill", sha256="a" * 64, span="all", quote="fee and credit"
    )
    observation = Observation(
        expectation_id=case.expectation.id,
        source="bill",
        observed_at=datetime.now(UTC),
        evidence=[evidence],
        confidence=0.99,
        terms=[
            Term(
                key="monthly_price",
                label="Monthly plan",
                value=499,
                confidence=0.99,
                evidence_id="e",
            ),
            Term(
                key="installation_fee",
                label="Installation",
                value=350,
                confidence=0.99,
                evidence_id="e",
            ),
            Term(
                key="installation_credit",
                label="Installation credit",
                value=350,
                confidence=0.99,
                evidence_id="e",
            ),
            Term(
                key="duration_months", label="Duration", value=12, confidence=0.99, evidence_id="e"
            ),
        ],
    )
    result = reconcile(case.expectation, observation)
    added_credit = next(item for item in result.deltas if item.key == "installation_credit")
    fee = next(item for item in result.deltas if item.key == "installation_fee")
    assert added_credit.classification == "explained"
    assert fee.classification == "explained"
    assert fee.material is False
    assert result.net_amount == 0


def test_missing_expected_term_preserves_uncertainty():
    case = create_demo_case()
    evidence = EvidenceRef(id="e", filename="bill", sha256="a" * 64, span="all", quote="499")
    observation = Observation(
        expectation_id=case.expectation.id,
        source="partial bill",
        observed_at=datetime.now(UTC),
        evidence=[evidence],
        confidence=0.9,
        terms=[
            Term(
                key="monthly_price",
                label="Monthly plan",
                value=499,
                confidence=0.9,
                evidence_id="e",
            )
        ],
    )
    result = reconcile(case.expectation, observation)
    assert result.confidence == 0.74
    assert any(item.classification == "uncertain" for item in result.deltas)
