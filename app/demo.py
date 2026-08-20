from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.diff_engine import reconcile
from app.domain import (
    ActionLevel,
    CaseStatus,
    ExpectationContract,
    Obligation,
    Observation,
    ReconciliationCase,
    Term,
)
from app.evidence import make_evidence
from app.guardian import authorize
from app.provider import CorrectionRequest, FiberMaxSandboxConnector, ProviderConnector

WELCOME_EMAIL = """Welcome to FiberMax Home Internet.
Your plan is fixed at ₹499/month for 12 months. Installation is completely free.
Your service begins on 12 August 2026. We are glad to have you with us.
"""

BILL_EMAIL = """FiberMax Invoice FM-2081
Monthly plan: ₹499
Installation fee: ₹350
Total due: ₹849
"""

CORRECTED_BILL = """FiberMax Adjustment Notice
Installation fee reversal: -₹350
Credit applied: ₹350
Balance correction complete. Reference: FM-CREDIT-350.
"""


def create_demo_case(case_id: str = "case_fibermax_demo") -> ReconciliationCase:
    now = datetime.now(UTC)
    welcome = make_evidence(
        "ev_welcome_001",
        "fibermax-welcome.txt",
        WELCOME_EMAIL,
        "₹499/month for 12 months. Installation is completely free.",
        "lines 2-2",
    )
    expectation = ExpectationContract(
        id="exp_fibermax_demo",
        counterparty="FiberMax",
        subject="Home internet plan",
        effective_at=now - timedelta(days=62),
        terms=[
            Term(
                key="monthly_price",
                label="Monthly plan",
                value=499,
                unit="INR/month",
                confidence=0.99,
                evidence_id=welcome.id,
            ),
            Term(
                key="installation_fee",
                label="Installation",
                value=0,
                unit="INR",
                confidence=0.99,
                evidence_id=welcome.id,
            ),
            Term(
                key="duration_months",
                label="Price guarantee",
                value=12,
                unit="months",
                confidence=0.98,
                evidence_id=welcome.id,
            ),
        ],
        verification_rule="Every invoice must preserve ₹499/month and charge ₹0 for installation for 12 months.",
        evidence=[welcome],
        confidence=0.98,
        allowed_actions=[ActionLevel.INFORM, ActionLevel.PREPARE, ActionLevel.SEND],
    )
    case = ReconciliationCase(
        id=case_id,
        title="FiberMax installation charge",
        expectation=expectation,
        next_action_at=now,
    )
    case.record(
        "expectation_agent",
        "contract_compiled",
        "Captured ₹499/month for 12 months with free installation.",
        [welcome.id],
        model="gemini-3.5-flash",
    )
    case.record(
        "watch_agent",
        "watch_scheduled",
        "Waiting for the next FiberMax invoice.",
        next_action_at=now.isoformat(),
    )
    return case


def observe_bill(case: ReconciliationCase) -> ReconciliationCase:
    if case.observations:
        return case
    evidence = make_evidence(
        "ev_bill_001",
        "fibermax-invoice-2081.txt",
        BILL_EMAIL,
        "Installation fee: ₹350",
        "lines 2-4",
    )
    observation = Observation(
        id="obs_fibermax_bill",
        expectation_id=case.expectation.id,
        source="FiberMax invoice FM-2081",
        observed_at=datetime.now(UTC),
        terms=[
            Term(
                key="monthly_price",
                label="Monthly plan",
                value=499,
                unit="INR",
                confidence=0.99,
                evidence_id=evidence.id,
            ),
            Term(
                key="installation_fee",
                label="Installation",
                value=350,
                unit="INR",
                confidence=0.99,
                evidence_id=evidence.id,
            ),
            Term(
                key="duration_months",
                label="Price guarantee",
                value=12,
                unit="months",
                confidence=0.98,
                evidence_id=evidence.id,
            ),
        ],
        evidence=[evidence],
        confidence=0.99,
    )
    case.observations.append(observation)
    case.reality_diff = reconcile(case.expectation, observation)
    case.status = CaseStatus.MISMATCH
    case.approval_required = True
    case.record(
        "observation_agent",
        "bill_observed",
        "Parsed invoice total ₹849 with a ₹350 installation charge.",
        [evidence.id],
    )
    case.record(
        "diff_agent",
        "material_diff",
        "Expected ₹499; observed ₹849; unexplained difference ₹350.",
        ["ev_welcome_001", evidence.id],
        deterministic=True,
    )
    case.record(
        "judge_agent",
        "judgment",
        "The ₹350 charge conflicts with the explicit free-installation term.",
        ["ev_welcome_001", evidence.id],
        confidence=0.99,
    )
    case.record(
        "guardian_agent",
        "approval_requested",
        "Routine provider contact requires the user's scoped approval.",
    )
    return case


def resolve(
    case: ReconciliationCase,
    approved: bool,
    provider: ProviderConnector | None = None,
) -> ReconciliationCase:
    if case.status in {CaseStatus.MONITORING, CaseStatus.RECOVERED}:
        return case
    if case.status not in {CaseStatus.MISMATCH, CaseStatus.NEEDS_APPROVAL}:
        return case
    if not case.reality_diff or not any(delta.material for delta in case.reality_diff.deltas):
        case.status = CaseStatus.UNCERTAIN
        case.record(
            "guardian_agent",
            "action_blocked",
            "No evidence-backed material difference exists; provider contact was blocked.",
        )
        return case
    decision = authorize(
        case, "send_correction_request", ActionLevel.SEND, explicit_approval=approved
    )
    if not decision.allowed:
        case.status = CaseStatus.NEEDS_APPROVAL
        case.approval_required = True
        case.record("guardian_agent", "action_blocked", decision.reason)
        return case
    connector = provider or FiberMaxSandboxConnector()
    try:
        provider_reply = connector.submit_correction(
            CorrectionRequest(
                case_id=case.id,
                counterparty=case.expectation.counterparty,
                disputed_amount=int(case.reality_diff.net_amount),
                evidence_ids=("ev_welcome_001", "ev_bill_001"),
                requested_resolution="Reverse the installation fee and apply a ₹350 credit.",
            )
        )
    except (TimeoutError, ConnectionError, ValueError) as error:
        case.status = CaseStatus.MISMATCH
        case.record(
            "resolution_agent",
            "provider_action_failed",
            "Provider connector failed safely; no obligation was created.",
            error_type=type(error).__name__,
        )
        return case
    reply = make_evidence(
        "ev_provider_reply_001",
        "fibermax-response.txt",
        provider_reply.message,
        "₹350 credit is approved and will appear within 48 hours.",
        "lines 1-2",
    )
    case.expectation.evidence.append(reply)
    case.obligations.append(
        Obligation(
            id="obl_credit_350",
            promise="FiberMax credit will appear within 48 hours",
            amount=Decimal("350"),
            deadline_at=provider_reply.promised_by,
            verification_rule="A FiberMax statement must show an applied ₹350 credit.",
            evidence_id=reply.id,
        )
    )
    case.status = CaseStatus.MONITORING
    case.approval_required = False
    case.next_action_at = provider_reply.promised_by
    case.record("guardian_agent", "action_authorized", decision.reason, explicit_approval=True)
    case.record(
        "resolution_agent",
        "correction_sent",
        "Sent a scoped evidence packet to the FiberMax provider sandbox.",
        ["ev_welcome_001", "ev_bill_001"],
        provider_mode="sandbox",
        provider_reference=provider_reply.reference,
    )
    case.record(
        "owed_agent",
        "obligation_created",
        "Monitoring the promised ₹350 credit for 48 hours.",
        [reply.id],
        deadline=case.next_action_at.isoformat(),
    )
    return case


def verify_credit(case: ReconciliationCase, *, demo_time_jump: bool = False) -> ReconciliationCase:
    if case.status == CaseStatus.RECOVERED:
        return case
    if case.status != CaseStatus.MONITORING or not case.obligations:
        return case
    if case.next_action_at and datetime.now(UTC) < case.next_action_at and not demo_time_jump:
        return case
    evidence = make_evidence(
        "ev_credit_001",
        "fibermax-adjustment.txt",
        CORRECTED_BILL,
        "Credit applied: ₹350",
        "lines 1-4",
    )
    obligation = case.obligations[0]
    obligation.status = "verified"
    case.expectation.evidence.append(evidence)
    case.recovered_amount = Decimal("350")
    case.status = CaseStatus.RECOVERED
    case.next_action_at = None
    case.record(
        "observation_agent",
        "credit_observed",
        "Observed the promised ₹350 credit on the account.",
        [evidence.id],
    )
    case.record(
        "outcome_agent",
        "case_closed",
        "Correction verified. ₹350 recovered with no manual follow-up.",
        [obligation.evidence_id, evidence.id],
        recovered_amount=350,
        demo_time_jump=demo_time_jump,
    )
    return case
