from app.demo import create_demo_case, observe_bill
from app.domain import ActionLevel
from app.guardian import authorize


def test_sensitive_action_is_denied_without_approval():
    case = observe_bill(create_demo_case())
    result = authorize(case, "accept_settlement", ActionLevel.SENSITIVE)
    assert result.allowed is False
    assert result.requires_approval is True


def test_scoped_send_is_allowed_after_explicit_approval():
    case = observe_bill(create_demo_case())
    result = authorize(case, "send_correction_request", ActionLevel.SEND, explicit_approval=True)
    assert result.allowed is True


def test_permission_boundary_blocks_ungranted_escalation():
    case = create_demo_case()
    result = authorize(case, "escalate", ActionLevel.ESCALATE)
    assert result.allowed is False
