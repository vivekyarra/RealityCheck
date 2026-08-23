# Release verification report

Verified on 20 August 2026 against the repository release candidate.

## Release gates

| Gate | Result | Evidence |
|---|---:|---|
| Static analysis | Pass | Ruff reports zero violations |
| Automated tests | Pass | 27 tests, 87%+ statement coverage |
| Adversarial lifecycle stress | Pass | 10,000 cases, 145,111 invariant checks, 0 failures |
| Concurrent HTTP sessions | Pass | 100 parallel full lifecycles, 0 failures |
| Duplicate/racing HTTP actions | Pass | 192 racing requests; 1 observation, 1 obligation, 1 recovery |
| Multi-process persistence | Pass | Independent store instances serialize atomic mutations |
| Container clean build | Pass | Python 3.12 slim image resolves from scratch |
| Container privilege | Pass | Runtime UID is the non-root `realitycheck` user |
| Repeated container boot | Pass | 10/10 two-worker starts healthy, 0 lock errors |
| Browser workflow | Pass | Observe, blocked action, approval, monitor, verify, reset |
| Lighthouse mobile | Pass | 100 Performance, 100 Accessibility, 100 Best Practices, 100 SEO |
| Live Gemini extraction | Pass | `gemini-live`, 3 grounded terms, confidence 0.95 |
| Dependency integrity | Pass | `pip check` reports no broken requirements |
| Secret scan | Pass | No provided API key or environment secret is tracked |

## Loss cases explicitly tested

- Provider contact before a material evidence-backed mismatch.
- Provider contact without one-attempt scoped approval.
- Verification before an obligation exists or before its deadline.
- Duplicate observations, approvals, obligations, and completion events.
- Matching credits that should explain rather than inflate a fee discrepancy.
- Missing terms and low-confidence evidence that must remain uncertain.
- Tampering with any earlier hash-chained audit event.
- Invalid or corrupt persisted state.
- Concurrent workers updating the same case.
- Provider timeout or invalid response creating a false obligation.
- Oversized evidence payloads and unauthenticated scheduler calls.
- Cross-user demo state leakage.

## Runtime truth

- Gemini Developer API was called successfully using a local, uncommitted credential.
- The provider boundary is the explicitly labeled fictional FiberMax sandbox. No real company contact is claimed.
- Google Cloud deployment scripts are implemented and syntax-checked. A live deployment attempt authenticated successfully but Google rejected API activation because every accessible project currently has billing disabled. No hosted URL or Cloud deployment claim is made until billing is enabled.
- A public deterministic judge demo is verified at `https://realitycheck-agent.vercel.app`; it is not presented as Google Cloud proof and reports `store: local` and `ai_configured: false` at `/api/health`.

## Reproduce

```powershell
pip install -r requirements-dev.txt
ruff check app tests scripts
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
python scripts/stress_test.py --cases 10000
docker build -t realitycheck .
docker run --rm -p 8080:8080 realitycheck
```
