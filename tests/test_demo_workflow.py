from app.demo import create_demo_case, observe_bill, resolve, verify_credit


class FailingProvider:
    def submit_correction(self, request):
        raise TimeoutError("provider unavailable")


def test_complete_reconciliation_loop_requires_verified_outcome():
    case = create_demo_case()
    assert case.status == "captured"

    case = observe_bill(case)
    assert case.status == "mismatch"
    assert case.reality_diff.net_amount == 350
    assert case.approval_required is True

    blocked = resolve(case, approved=False)
    assert blocked.status == "needs_approval"

    monitoring = resolve(blocked, approved=True)
    assert monitoring.status == "monitoring"
    assert monitoring.recovered_amount == 0
    assert monitoring.obligations[0].status == "open"

    assert verify_credit(monitoring).status == "monitoring"
    recovered = verify_credit(monitoring, demo_time_jump=True)
    assert recovered.status == "recovered"
    assert recovered.recovered_amount == 350
    assert recovered.obligations[0].status == "verified"
    assert recovered.audit_chain_valid()


def test_steps_are_idempotent():
    case = observe_bill(create_demo_case())
    assert len(observe_bill(case).observations) == 1
    case = resolve(case, approved=True)
    assert len(resolve(case, approved=True).obligations) == 1
    case = verify_credit(case, demo_time_jump=True)
    assert verify_credit(case, demo_time_jump=True).recovered_amount == 350


def test_out_of_order_actions_cannot_bypass_evidence_or_deadline():
    captured = create_demo_case()
    assert resolve(captured, approved=True).status == "captured"
    assert verify_credit(captured, demo_time_jump=True).status == "captured"

    monitoring = resolve(observe_bill(create_demo_case()), approved=True)
    early = verify_credit(monitoring)
    assert early.status == "monitoring"
    assert early.recovered_amount == 0


def test_audit_chain_detects_tampering():
    case = observe_bill(create_demo_case())
    assert case.audit_chain_valid()
    case.audit[0].summary = "tampered"
    assert not case.audit_chain_valid()


def test_provider_failure_cannot_create_a_fake_obligation():
    case = observe_bill(create_demo_case())
    failed = resolve(case, approved=True, provider=FailingProvider())
    assert failed.status == "mismatch"
    assert failed.obligations == []
    assert failed.audit[-1].action == "provider_action_failed"
