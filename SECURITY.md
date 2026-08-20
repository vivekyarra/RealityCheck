# Security policy

## Security properties

- No secret or raw credential may be committed, logged, returned in health endpoints, or embedded in browser assets.
- Full evidence text remains server-side; UI responses expose only required, redacted passages.
- Every external action must have a policy level and permission basis.
- L4 actions cannot execute without explicit approval.
- Low-confidence or conflicting evidence cannot trigger external action.
- Task wake-up endpoints require a timing-safe shared-secret comparison or Cloud Run IAM.
- Production Firestore access uses the dedicated Cloud Run service account and least privilege.

## Threat model summary

| Threat | Control |
|---|---|
| Prompt injection in provider evidence | Evidence is data, not instruction; deterministic comparison and Guardian remain independent |
| Hallucinated agreement term | Typed extraction, exact quote, source hash, confidence gate |
| Unauthorized provider contact | L2 permission + scoped approval + audit event |
| PII leakage | Server-side redaction and evidence minimization |
| Duplicate scheduler delivery | Idempotent observations, obligations, and terminal states |
| Secret disclosure | `.gitignore`, ADC/Vertex AI production auth, no browser-side keys |
| Harassment / repeated contact | One scoped routine action in MVP; future connectors require rate limiting and revocation |

## Reporting

Please do not open a public issue for a vulnerability. Contact the repository owner privately with reproduction steps and impact.
