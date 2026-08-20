from dataclasses import dataclass

from app.domain import ActionLevel, ReconciliationCase


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


PROHIBITED_WITHOUT_EXPLICIT_APPROVAL = {
    "accept_settlement",
    "waive_rights",
    "purchase",
    "change_plan",
    "file_legal_claim",
    "file_regulatory_complaint",
}


def authorize(
    case: ReconciliationCase, action: str, level: ActionLevel, explicit_approval: bool = False
) -> PolicyDecision:
    if action in PROHIBITED_WITHOUT_EXPLICIT_APPROVAL and not explicit_approval:
        return PolicyDecision(
            False, True, "Sensitive decisions always require explicit user approval."
        )
    if (
        level in {ActionLevel.SEND, ActionLevel.ESCALATE, ActionLevel.SENSITIVE}
        and not explicit_approval
    ):
        return PolicyDecision(
            False, True, "External actions require explicit approval for this specific attempt."
        )
    if level not in case.expectation.allowed_actions:
        if explicit_approval and level in {ActionLevel.SEND, ActionLevel.ESCALATE}:
            return PolicyDecision(True, False, "User approved this scoped action.")
        return PolicyDecision(
            False, True, f"The expectation contract does not grant {level.value} permission."
        )
    if (
        case.reality_diff
        and case.reality_diff.confidence < 0.75
        and level not in {ActionLevel.INFORM, ActionLevel.PREPARE}
    ):
        return PolicyDecision(
            False, True, "Low-confidence evidence cannot trigger an external action."
        )
    return PolicyDecision(True, False, "Action is within the captured permission boundary.")
