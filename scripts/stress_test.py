from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.demo import create_demo_case, observe_bill, resolve, verify_credit


def run(cases: int) -> dict[str, float | int]:
    started = time.perf_counter()
    recovered = 0
    invariant_checks = 0
    rng = random.Random(20260820)
    for index in range(cases):
        case = create_demo_case(f"stress_{index}")

        # Adversarial ordering: approval and verification cannot create a result
        # before a material, evidence-backed observation exists.
        for _ in range(rng.randint(0, 3)):
            case = resolve(case, approved=rng.choice([True, False]))
            case = verify_credit(case, demo_time_jump=True)
            assert case.status == "captured"
            assert not case.obligations and case.recovered_amount == 0
            invariant_checks += 3

        # Duplicate delivery must be idempotent.
        for _ in range(rng.randint(1, 4)):
            case = observe_bill(case)
        assert len(case.observations) == 1
        assert case.reality_diff and case.reality_diff.net_amount == 350
        invariant_checks += 2

        # Repeated denials cannot accidentally authorize an external action.
        for _ in range(rng.randint(1, 3)):
            case = resolve(case, approved=False)
        assert not case.obligations and case.recovered_amount == 0
        invariant_checks += 2

        # Duplicate approved submissions create one monitored obligation.
        for _ in range(rng.randint(1, 4)):
            case = resolve(case, approved=True)
        assert case.status == "monitoring" and len(case.obligations) == 1
        assert verify_credit(case).status == "monitoring"
        invariant_checks += 3

        # Demo time travel is explicit. Duplicate verification stays idempotent.
        for _ in range(rng.randint(1, 4)):
            case = verify_credit(case, demo_time_jump=True)
        assert len(case.observations) == 1 and len(case.obligations) == 1
        assert case.audit_chain_valid()
        invariant_checks += 3
        if case.recovered_amount == 350 and case.status == "recovered":
            recovered += 1
    elapsed = time.perf_counter() - started
    return {
        "cases": cases,
        "verified": recovered,
        "failures": cases - recovered,
        "invariant_checks": invariant_checks,
        "seed": 20260820,
        "seconds": round(elapsed, 3),
        "cases_per_second": round(cases / elapsed, 1),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=1000)
    args = parser.parse_args()
    result = run(args.cases)
    print(result)
    raise SystemExit(0 if result["failures"] == 0 else 1)
