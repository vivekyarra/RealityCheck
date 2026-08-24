# All Things Agentic submission checklist

## Qualification

- [x] Taskmaster category selected.
- [x] Gemini 3.5 Flash model name is explicit in code and deployment.
- [x] Google ADK agent fleet is implemented.
- [x] Google Gen AI SDK is used for typed structured extraction.
- [x] Live Google Cloud infrastructure: default Cloud Firestore database in `argus-489918`; Cloud Run + Pub/Sub/Scheduler remain implemented optional paths.
- [x] Complete workflow takes action beyond chat.
- [x] Background obligation state survives sessions in Firestore.
- [x] Safety permissions and evidence traceability are implemented.
- [x] Public deployment writes verified against participant-owned Firestore in `argus-489918`.

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
- [x] GitHub Actions is green on `main` for the release branch.
- [x] No secret is tracked (`git grep` and staged-file scan clean).
- [x] `.env`, local DB, uploads, references, generated render files, and API key are absent from Git.
- [x] Public repository description, homepage, and topics are set.
- [ ] Create release tag `v1.0.0` after deployment proof is captured.

## Demo proof gate

- [ ] `/api/health` reports `store: firestore`, project `argus-489918`, model `gemini-3.5-flash`, and truthful AI status.
- [ ] Firestore case document visible.
- [ ] Firestore document visibly changes while the public workflow advances.
- [ ] State that compute is Vercel and durable backend state is Google Cloud Firestore.
- [ ] No secrets or personal account data visible.
- [ ] Recovery is shown only after adjustment evidence.
- [ ] Fictional FiberMax sandbox boundary is stated aloud and visible in health/runtime truth.

## Bonus points

- [ ] Publish `BLOG_POST.md` on a public platform and add the required hackathon-purpose disclosure.
- [ ] Publish `SOCIAL_POST.md` with `#AllThingsAgenticHackathon`.
- [ ] Add the public URLs to Devpost.
