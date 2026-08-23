# All Things Agentic submission checklist

## Qualification

- [x] Taskmaster category selected.
- [x] Gemini 3.5 Flash model name is explicit in code and deployment.
- [x] Google ADK agent fleet is implemented.
- [x] Google Gen AI SDK is used for typed structured extraction.
- [x] Google Cloud infrastructure is implemented: Cloud Run + Firestore + Pub/Sub/Scheduler.
- [x] Complete workflow takes action beyond chat.
- [x] Background obligation state survives sessions in Firestore.
- [x] Safety permissions and evidence traceability are implemented.
- [ ] Deploy to the participant's Google Cloud project and save proof.

## Required Devpost fields

- [ ] Category: Taskmaster.
- [x] Hosted URL tested publicly: https://realitycheck-agent.vercel.app.
- [x] Text description drafted in `DEVPOST_SUBMISSION.md`.
- [x] Features and functionality drafted.
- [x] Technologies used drafted.
- [x] Other data sources drafted.
- [x] Findings and learnings drafted.
- [x] Repository URL: https://github.com/vivekyarra/RealityCheck
- [x] README spin-up instructions included.
- [x] Architecture diagram included as upload-ready `docs/architecture.png` (source: `docs/architecture.svg`).
- [ ] Record and upload the approximately four-minute demo video.
- [x] Demo script includes problem, value proposition, live product, and Google Cloud proof.

## Repository release gate

- [x] `ruff check app tests scripts` passes.
- [x] Coverage gate passes at 85% or better.
- [x] 10,000-case adversarial stress run reports zero failures across 145,111 invariant checks.
- [x] Docker image builds and health endpoint passes as a non-root runtime.
- [x] GitHub Actions is green on `main` for release commit `15cc391`.
- [x] No secret is tracked (`git grep` and staged-file scan clean).
- [x] `.env`, local DB, uploads, references, generated render files, and API key are absent from Git.
- [x] Public repository description, homepage, and topics are set.
- [ ] Create release tag `v1.0.0` after deployment proof is captured.

## Demo proof gate

- [ ] Cloud Run revision and URL visible.
- [ ] `/api/health` reports `store: firestore`, `model: gemini-3.5-flash`, `ai_configured: true`.
- [ ] Firestore case document visible.
- [ ] Cloud Scheduler success visible.
- [ ] Cloud Logging trace visible.
- [ ] No secrets or personal account data visible.
- [ ] Recovery is shown only after adjustment evidence.
- [ ] Fictional FiberMax sandbox boundary is stated aloud and visible in health/runtime truth.

## Bonus points

- [ ] Publish `BLOG_POST.md` on a public platform and add the required hackathon-purpose disclosure.
- [ ] Publish `SOCIAL_POST.md` with `#AllThingsAgenticHackathon`.
- [ ] Add the public URLs to Devpost.
