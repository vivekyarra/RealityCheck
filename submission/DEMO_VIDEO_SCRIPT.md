# RealityCheck - 4-minute demo script

Target runtime: **3:45-3:55**. Record at 1080p. Use the running Cloud Run URL. Do not show secrets.

## 0:00-0:25 - Problem and category

**Visual:** RealityCheck dashboard, untouched captured state.

**Voiceover:**

“Companies have reconciliation systems to catch what doesn't match. Consumers have memory and screenshots. RealityCheck gives an individual their own reconciliation agent. When I buy, book, subscribe, or receive a promise, it compiles what I should get into an Expectation Contract. Later it observes what happened, computes the reality diff, and - with my permission - pursues correction until reality matches the agreement.”

## 0:25-0:47 - Google Cloud proof

**Visual:** Cloud Run service page with URL and green revision. Open `/api/health`. Briefly show Firestore case collection and a Cloud Logging request. Keep project identifiers visible; mask billing/account information.

**Voiceover:**

“This is the backend running on Google Cloud Run. The health endpoint shows Gemini 3.5 Flash, Firestore production state, and the fictional provider-sandbox boundary. Firestore preserves cases and obligations across sessions, while authenticated Cloud Scheduler ticks execute due checks and Pub/Sub supports connector fan-out.”

## 0:47-1:18 - Expectation Contract

**Visual:** Return to dashboard. Point at agreement and evidence vault.

**Voiceover:**

“FiberMax promised ₹499 per month for 12 months, with installation completely free. Gemini's Expectation Agent turned that email into three typed terms. Every term carries the source hash, exact quote, and confidence. This is evidence, not memory.”

## 1:18-1:54 - Observe and compute the reality diff

**Action:** Click **Observe next bill**.

**Visual:** Expected ₹499 versus actual ₹849 and +₹350 diff. Show Judge Agent note and invoice evidence.

**Voiceover:**

“A new ₹849 bill arrives. The Observation Agent parses the line items. Arithmetic stays deterministic: ₹499 matches; the ₹350 installation fee does not. The Judge Agent checks whether the delta is explained and cites the exact conflicting promise. If taxes, a matching credit, or a later plan change explained the amount, the case would remain explained or uncertain rather than launching a false dispute.”

## 1:54-2:26 - Permissioned action

**Action:** Try the action once without checking approval. Show the Guardian toast. Then check approval and click **Approve & send correction**.

**Voiceover:**

“RealityCheck is autonomous, not reckless. The Guardian blocks provider contact until I approve this one scoped request. It can inform and prepare automatically. It can never accept a settlement, spend money, change a plan, waive rights, or file a legal complaint without explicit approval.”

## 2:26-3:03 - OWED promise handoff

**Visual:** Provider response document and monitoring state.

**Voiceover:**

“FiberMax approves a ₹350 credit within 48 hours. Most agents would celebrate and stop. RealityCheck knows that approval is another promise, not reality. The OWED Agent creates a new obligation with an amount, deadline, evidence, and verification rule, then goes back to waiting asynchronously.”

## 3:03-3:30 - Verified outcome

**Action:** Click **Fast-forward 48h & verify**.

**Visual:** Recovered metric, green verified state, adjustment evidence, completed timeline.

**Voiceover:**

“A new adjustment notice appears. The Outcome Agent observes the promised ₹350 credit and only now closes the case. ₹350 recovered. Messages written by me: zero. Documents searched: zero. Follow-ups I had to remember: zero.”

## 3:30-3:52 - Architecture and close

**Visual:** Architecture diagram, then dashboard final state.

**Voiceover:**

“Gemini 3.5 Flash and Google ADK handle semantic evidence and specialist coordination. Cloud Run, Firestore, Pub/Sub, and Scheduler make the workflow durable and asynchronous. Today it is an ISP fee. The same Expectation Contract works for hotel inclusions, product specifications, missing refunds, warranties, and deadlines. Reality should match the agreement.”

## Recording checklist

- [ ] Use the deployed `.run.app` URL, not localhost.
- [ ] Show Cloud Run and Firestore proof for at least 10 seconds.
- [ ] Ensure runtime badge says connected; never fake this state.
- [ ] Reset the demo immediately before recording.
- [ ] Keep the entire autonomous loop in one continuous take if practical.
- [ ] Do not show API keys, tokens, environment values, email addresses, billing IDs, or unrelated browser tabs.
- [ ] Upload publicly or unlisted according to current Devpost rules, then add the URL to the submission.
