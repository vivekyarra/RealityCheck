const $ = (selector) => document.querySelector(selector);
const statusOrder = { captured: 0, mismatch: 1, needs_approval: 1, resolving: 2, monitoring: 2, recovered: 3, closed: 3 };
let state;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function money(value) {
  return `₹${Number(value || 0).toLocaleString("en-IN")}`;
}

function titleCase(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

function renderTimeline(audit) {
  const list = $("#timelineList");
  list.innerHTML = "";
  [...audit].reverse().forEach((event) => {
    const li = document.createElement("li");
    const time = new Date(event.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const dot = document.createElement("span");
    dot.className = "timeline-dot";
    dot.textContent = "✓";
    const detail = document.createElement("div");
    const actor = document.createElement("strong");
    actor.textContent = titleCase(event.actor);
    const summary = document.createElement("p");
    summary.textContent = event.summary;
    detail.append(actor, summary);
    const timestamp = document.createElement("time");
    timestamp.textContent = time;
    li.append(dot, detail, timestamp);
    list.appendChild(li);
  });
  $("#eventCount").textContent = `${audit.length} events`;
}

function renderStages(status) {
  const current = statusOrder[status] ?? 0;
  document.querySelectorAll(".stage").forEach((stage, index) => {
    stage.classList.toggle("done", index < current || (status === "recovered" && index <= current));
    stage.classList.toggle("current", index === current && status !== "recovered");
    const small = stage.querySelector("small");
    if (index < current || (status === "recovered" && index <= current)) small.textContent = "Complete";
    else if (index === current) small.textContent = "Active";
    else small.textContent = "Queued";
  });
}

function render(caseState) {
  state = caseState;
  const status = caseState.status;
  const observed = caseState.observations.length > 0;
  const monitoring = status === "monitoring";
  const recovered = status === "recovered";
  $("#caseStatus").textContent = titleCase(status);
  renderStages(status);
  renderTimeline(caseState.audit);

  $("#diffArea").classList.toggle("pre-observation", !observed);
  $("#actualAmount").textContent = recovered ? "₹499" : observed ? "₹849" : "Awaiting bill";
  $("#actualLabel").textContent = recovered ? "adjusted total" : observed ? "invoice total" : "no observation yet";
  $("#installationActual").textContent = recovered ? "₹0" : observed ? "₹350" : "—";
  $("#billEvidence").textContent = recovered ? "✓ Adjustment ADJ-2081" : observed ? "! Invoice FM-2081" : "Waiting for evidence";
  $("#billEvidence").classList.toggle("muted", !observed);
  $("#deltaAmount").textContent = recovered ? "₹0" : observed ? "+₹350" : "—";
  $("#deltaClassification").textContent = recovered ? "Reconciled" : observed ? "Unexplained charge" : "No comparison yet";
  $("#deltaCard").classList.toggle("resolved", recovered);
  $("#judgeNote").hidden = !observed || recovered;
  $("#billDocument").hidden = !observed;
  $("#replyDocument").hidden = !monitoring && !recovered;
  $("#creditDocument").hidden = !recovered;
  $("#approvalBox").hidden = status !== "mismatch" && status !== "needs_approval";
  $("#approvalCheck").checked = false;
  $("#recoveredMetric").textContent = money(caseState.recovered_amount);
  $("#recoveredCaption").textContent = recovered ? "Verified by adjustment ADJ-2081" : "Evidence required to close";
  $("#activeCaption").textContent = recovered ? "4 on track · 0 open diffs" : observed ? "3 on track · 1 open diff" : "3 on track · 1 awaiting observation";

  const button = $("#advanceButton");
  button.disabled = false;
  if (!recovered) $("#attentionBanner").removeAttribute("style");
  if (status === "captured") {
    button.innerHTML = "Observe next bill <span>→</span>";
    $("#actionHint").textContent = "Observe · compare · judge";
    $("#attentionTitle").textContent = "FiberMax bill ready";
    $("#attentionCopy").textContent = "Agreement captured · invoice queued";
    $("#severityBadge").textContent = "WATCHING";
  } else if (status === "mismatch" || status === "needs_approval") {
    button.innerHTML = "Approve & send correction <span>→</span>";
    $("#actionHint").textContent = "Guardian approval required";
    $("#attentionTitle").textContent = "₹350 agreement conflict";
    $("#attentionCopy").textContent = "Free installation promised · ₹350 charged";
    $("#severityBadge").textContent = "ACTION NEEDED";
  } else if (monitoring) {
    button.innerHTML = "Fast-forward 48h & verify <span>→</span>";
    $("#actionHint").textContent = "OWED Agent verification window";
    $("#attentionTitle").textContent = "₹350 credit due in 48h";
    $("#attentionCopy").textContent = "Obligation open · proof pending";
    $("#severityBadge").textContent = "MONITORING";
  } else if (recovered) {
    button.textContent = "Recovery verified ✓";
    button.disabled = true;
    $("#actionHint").textContent = "Closed with evidence";
    $("#attentionTitle").textContent = "₹350 recovered";
    $("#attentionCopy").textContent = "Reality matches · case closed";
    $("#severityBadge").textContent = "VERIFIED";
    $("#attentionBanner").style.background = "var(--green-soft)";
    $("#attentionBanner").style.borderColor = "var(--mint)";
  }
}

async function advance() {
  const button = $("#advanceButton");
  button.disabled = true;
  try {
    let step = "observe";
    let approve = false;
    if (["mismatch", "needs_approval"].includes(state.status)) {
      step = "resolve";
      approve = $("#approvalCheck").checked;
      if (!approve) {
        toast("Approval is required before provider contact.");
        button.disabled = false;
        return;
      }
    } else if (state.status === "monitoring") {
      step = "verify";
    }
    const next = await api("/api/demo/advance", { method: "POST", body: JSON.stringify({ step, approve }) });
    render(next);
    toast(step === "observe" ? "Reality diff detected: +₹350" : step === "resolve" ? "Correction sent; new promise is being monitored" : "₹350 recovery verified");
  } catch (error) {
    toast(error.message);
  } finally {
    if (state.status !== "recovered") button.disabled = false;
  }
}

async function reset() {
  const next = await api("/api/demo/reset", { method: "POST", body: "{}" });
  $("#attentionBanner").removeAttribute("style");
  render(next);
  toast("Demo reset to the captured agreement.");
}

async function init() {
  try {
    const now = new Date();
    $("#currentDate").textContent = now.toLocaleDateString("en-US", {
      weekday: "long", month: "long", day: "numeric",
    }).toUpperCase();
    const hour = now.getHours();
    const daypart = hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
    $("#greeting").textContent = `Good ${daypart}, Vivek.`;
    const [health, demo, fleet] = await Promise.all([
      api("/api/health"), api("/api/demo/state"), api("/api/agents"),
    ]);
    const cloudState = health.store === "firestore" ? "Firestore live" : "Local state";
    $("#runtimeMode").textContent = health.ai_configured
      ? `${health.model} · ${cloudState}`
      : `${cloudState} · AI ready`;
    const agentGrid = $("#agentGrid");
    fleet.agents.forEach((agent) => {
      const card = document.createElement("div");
      card.className = "agent-card";
      const framework = document.createElement("span");
      framework.textContent = "GOOGLE ADK";
      const name = document.createElement("strong");
      name.textContent = titleCase(agent.name);
      const readiness = document.createElement("small");
      readiness.textContent = "READY";
      card.append(framework, name, readiness);
      agentGrid.appendChild(card);
    });
    render(demo);
  } catch (error) {
    toast(`Startup failed: ${error.message}`);
  }
}

$("#advanceButton").addEventListener("click", advance);
$("#resetButton").addEventListener("click", reset);
$("#showEvidence").addEventListener("click", () => $("#evidence").scrollIntoView({ behavior: "smooth" }));
$("#secondaryAction").addEventListener("click", () => $("#evidence").scrollIntoView({ behavior: "smooth" }));
$("#menuButton").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
document.querySelectorAll(".nav-item").forEach((item) => item.addEventListener("click", () => $(".sidebar").classList.remove("open")));
init();
