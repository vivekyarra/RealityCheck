# Devpost submission copy

## Project name

RealityCheck

## Tagline

The autonomous agent that makes sure reality matches what you agreed to.

## Category

**Taskmaster** - RealityCheck completes a long-running consumer reconciliation workflow rather than returning advice in chat.

## Hosted project URL

https://realitycheck-agent.vercel.app

This public judge URL runs the complete deterministic provider-sandbox workflow. It is separate
from the required Google Cloud deployment proof and does not claim to be a Cloud Run runtime.

## Repository URL

https://github.com/vivekyarra/RealityCheck

## Short description

RealityCheck is a persistent personal reconciliation agent. It captures measurable promises from emails, receipts, bills, and screenshots as evidence-backed Expectation Contracts. When reality arrives later, it computes a deterministic “reality diff,” decides whether the difference is legitimate, and - with the user's permission - pursues correction. If a provider makes a new promise, RealityCheck monitors that promise and closes the case only after the correction is independently observed.

## The problem

Companies have reconciliation software protecting them from mismatches. Consumers have memory, screenshots, and support queues. The evidence needed to challenge a wrong fee, missing inclusion, late refund, incorrect specification, or broken deadline usually exists, but it is fragmented and arrives weeks or months apart. People lose money and time because remembering, comparing, contacting, and following up is tedious.

## Value proposition

RealityCheck gives every person their own expectation ledger and autonomous reconciliation team. The user does not search old emails, calculate the discrepancy, draft a support request, or remember the follow-up. They approve a clearly scoped action and receive a verified outcome with an audit trail.

## Features and functionality

- Compiles promises into typed, machine-checkable Expectation Contracts.
- Preserves a SHA-256 hash, exact evidence quote, source, and confidence for every term; audit events are hash-chained.
- Observes later bills and outcomes, then computes deterministic numeric/date/specification diffs.
- Uses a Judge Agent to separate legitimate variation from unexplained or uncertain mismatch.
- Presents evidence and “why” rather than opaque conclusions.
- Enforces L0-L4 permission tiers with an independent Guardian Agent.
- Prepares and sends only routine user-approved corrective requests in the MVP.
- Converts provider replies into new monitored OWED obligations.
- Runs asynchronously with Firestore state and authenticated Cloud Scheduler wake-ups; Pub/Sub is provisioned for connector fan-out.
- Closes cases only after corrective evidence is observed.
- Provides a responsive dashboard, evidence vault, timeline, and agent registry instead of a chat-first UI.
- Degrades honestly to a labeled deterministic demo when model credentials are unavailable.

## Demo scenario

FiberMax promises ₹499/month for 12 months with free installation. Two months later an ₹849 bill includes a ₹350 installation fee. RealityCheck extracts both documents, isolates the ₹350 unexplained difference, cites the original phrase “installation is completely free,” and asks for permission to contact the provider. FiberMax approves a ₹350 credit within 48 hours. RealityCheck does not close the case: its OWED Agent creates a new obligation, waits, observes an adjustment notice, verifies the ₹350 credit, and finally reports ₹350 recovered.

## Technologies used

- Gemini 3.5 Flash
- Google Agent Development Kit (ADK)
- Google Gen AI SDK with typed structured output
- Vertex AI
- Google Cloud Run
- Cloud Firestore
- Pub/Sub and Cloud Scheduler
- Cloud Build and Artifact Registry
- OpenTelemetry and Cloud Logging-compatible structured events
- Python, FastAPI, Pydantic, SQLite local fallback
- Accessible HTML, CSS, and JavaScript dashboard
- Pytest, Ruff, coverage, stress testing, Docker, GitHub Actions

## Other data sources used

- User-provided or demo email text
- User-provided or demo invoice text
- Fictional FiberMax provider-sandbox response and adjustment notice

No bank, merchant, or private mailbox is accessed in the judging demo. FiberMax is visibly sandboxed; no external contact is implied. Future connectors require explicit per-source consent.

## Findings and learnings

1. Detection is not the hard part; judgment is. Taxes, prorations, upgrades, partial shipments, and credits can explain a raw difference.
2. A provider saying “approved” is not resolution. It is a new promise that must be monitored.
3. LLMs are valuable at the unstructured evidence boundary, while deterministic code should own arithmetic and exact comparisons.
4. Autonomy is trustworthy only when permission and evidence are first-class state, not prompt text.
5. A narrow end-to-end scenario tells a stronger story than many shallow integrations.

## How Google technology is essential

Gemini 3.5 Flash compiles messy human agreements into structured terms and grounds each term in evidence. Google ADK expresses the specialist agent fleet and its orchestration boundary. Cloud Run makes the web/API runtime reproducible and scalable; Firestore keeps state across weeks; authenticated Cloud Scheduler ticks execute due OWED obligations without an open browser, while Pub/Sub is available for connector fan-out. Vertex AI lets production use service-account identity rather than shipping a model key.

## What makes it different

Most billing tools find anomalies. RealityCheck models the agreement first, reconciles later reality against it, acts within consent, and verifies the correction. Its primitive generalizes beyond money to quantities, specifications, inclusions, warranties, deliveries, and deadlines.

## Spin-up instructions

The repository README contains copy-paste setup, verification, Docker, and Google Cloud deployment instructions. The deterministic complete demo works with no credential. Live Gemini extraction requires `GOOGLE_API_KEY` locally or Vertex AI/Application Default Credentials on Google Cloud.

## Cloud deployment proof

**Still required before submission:** deploy to a billing-enabled Google Cloud project and include a demo-video shot of:

- Cloud Run revision and URL
- `/api/health` showing Firestore, Gemini 3.5 Flash, and AI configured
- Firestore case document
- successful Cloud Scheduler invocation
- Cloud Logging request trace

## Team

Vivek Yarra - product concept, implementation, testing, demonstration, and submission.
