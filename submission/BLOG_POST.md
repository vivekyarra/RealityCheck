# Building RealityCheck: Git Diff for Real Life

> I created this article for the purpose of entering Google's All Things Agentic Hackathon.

Companies reconcile expected and actual money every day. Consumers do the same work with memory, inbox search, calculators, and repeated support calls. That asymmetry led me to one question: what if an individual had an autonomous reconciliation system?

RealityCheck begins when an agreement is made, not when a complaint is filed. Gemini 3.5 Flash compiles a welcome email, receipt, booking confirmation, or support promise into an evidence-backed Expectation Contract. The contract contains measurable terms - amount, included benefit, date, quantity, specification, warranty, or deadline - and stores the exact source passage behind each one.

Later, an Observation Agent reads what actually happened. Deterministic code computes numeric and exact-value differences. A Judge Agent then handles the part arithmetic cannot: was the difference explained by tax, a proration, a later change, a partial shipment, or a matching credit? Uncertainty is a valid result. The system does not invent certainty to create a dramatic demo.

The part I care most about comes after the first correction request. A provider might reply, “₹350 credit approved; it will arrive within 48 hours.” That sentence is not resolution. It is a new promise. RealityCheck's OWED Agent turns it into a monitored obligation and closes the case only when later evidence proves the credit arrived.

The stack mirrors that lifecycle. Google ADK defines specialist agents. Gemini and the Google Gen AI SDK handle structured semantic extraction. Cloud Run hosts the application and API. Firestore holds state across long-running cases. Pub/Sub and Cloud Scheduler wake future checks. A Guardian Agent enforces permission boundaries before any external action.

For the hackathon demo I deliberately chose one ISP scenario rather than pretending to support every consumer domain. FiberMax promises ₹499/month for 12 months with free installation, then bills ₹849 including a ₹350 installation fee. The complete loop - capture, observe, diff, judge, approve, contact, monitor, verify - fits in under four minutes while still showing the real system property: the agent does not stop until reality matches the agreement.

The biggest learning was simple. Detecting a difference is easy. Deciding whether it matters, acting safely, and verifying the outcome are where an agent earns trust.
