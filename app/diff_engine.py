from decimal import Decimal, InvalidOperation

from app.domain import Classification, Delta, ExpectationContract, Observation, RealityDiff, Term


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value).replace(",", "").replace("₹", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _by_key(terms: list[Term]) -> dict[str, Term]:
    return {term.key: term for term in terms}


def reconcile(expectation: ExpectationContract, observation: Observation) -> RealityDiff:
    expected = _by_key(expectation.terms)
    actual = _by_key(observation.terms)
    deltas: list[Delta] = []
    net_amount = Decimal("0")

    # Explicit credits neutralize matching explicit fees before judgment.
    remaining_credits = sum(
        (_decimal(t.value) or Decimal("0")) for t in observation.terms if t.key.endswith("_credit")
    )

    for key in sorted(set(expected) | set(actual)):
        exp = expected.get(key)
        act = actual.get(key)
        exp_value = exp.value if exp else None
        act_value = act.value if act else None
        exp_num = _decimal(exp_value)
        act_num = _decimal(act_value)

        if exp is None:
            amount = act_num
            is_credit = key.endswith("_credit") and bool(amount and amount > 0)
            classification = Classification.EXPLAINED if is_credit else Classification.UNCERTAIN
            material = bool(amount and amount != 0 and not is_credit)
            explanation = (
                "An explicit credit reduces or offsets observed charges."
                if is_credit
                else "This line item was not present in the captured agreement and needs review."
            )
        elif act is None:
            amount = None
            classification = Classification.UNCERTAIN
            material = True
            explanation = (
                "The expected term is missing from the observation; more evidence is required."
            )
        elif exp_num is not None and act_num is not None:
            amount = act_num - exp_num
            classification = Classification.EXPLAINED if amount == 0 else Classification.UNEXPLAINED
            material = abs(amount) >= Decimal("1")
            explanation = (
                "Observed value matches the agreement."
                if amount == 0
                else "Observed amount conflicts with the evidence-backed expected amount."
            )
            if material and amount > 0 and key.endswith("_fee") and remaining_credits >= amount:
                remaining_credits -= amount
                classification = Classification.EXPLAINED
                material = False
                explanation = "The added fee is fully offset by an explicit matching credit."
            if material and key.endswith(("price", "fee", "amount")):
                net_amount += amount
        else:
            matched = str(exp_value).strip().casefold() == str(act_value).strip().casefold()
            amount = None
            classification = Classification.EXPLAINED if matched else Classification.UNEXPLAINED
            material = not matched
            explanation = (
                "Observed term matches the agreement."
                if matched
                else "Observed term conflicts with the captured agreement."
            )

        deltas.append(
            Delta(
                key=key,
                label=(exp or act).label,
                expected=exp_value,
                actual=act_value,
                amount=amount,
                classification=classification,
                material=material,
                explanation=explanation,
                expected_evidence_id=exp.evidence_id if exp else None,
                actual_evidence_id=act.evidence_id if act else None,
            )
        )

    confidence = min(expectation.confidence, observation.confidence)
    if any(delta.classification == Classification.UNCERTAIN for delta in deltas):
        confidence = min(confidence, 0.74)
    return RealityDiff(
        expectation_id=expectation.id,
        observation_id=observation.id,
        deltas=deltas,
        net_amount=net_amount,
        confidence=confidence,
    )
