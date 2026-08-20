from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.config import Settings
from app.domain import ActionLevel, ExpectationContract, Term
from app.evidence import make_evidence


class ExtractedTerm(BaseModel):
    key: str
    label: str
    value: str | float | int | bool
    unit: str | None = None
    kind: str = "hard"
    confidence: float = Field(ge=0, le=1)
    evidence_quote: str


class ExpectationExtraction(BaseModel):
    counterparty: str
    subject: str
    terms: list[ExtractedTerm]
    verification_rule: str
    confidence: float = Field(ge=0, le=1)


SYSTEM_INSTRUCTION = """
You are RealityCheck's Expectation Agent. Compile measurable consumer promises into a
machine-checkable Expectation Contract. Never invent a term. Distinguish hard promises
from soft estimates. Normalize amounts and durations, preserve a short exact evidence
quote for every term, and lower confidence when language conflicts or is ambiguous.
Return only the requested structured output.
""".strip()


class GeminiExpectationAgent:
    """Gemini structured extraction through Google's Gen AI SDK."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def extract(
        self, filename: str, text: str, counterparty_hint: str | None = None
    ) -> tuple[ExpectationContract, str]:
        if self.settings.ai_configured:
            try:
                return self._gemini_extract(filename, text, counterparty_hint), "gemini-live"
            except Exception:
                # Evidence processing must degrade safely; deterministic extraction is
                # labeled and lower-confidence, never presented as a live-model result.
                contract = self._deterministic_extract(filename, text, counterparty_hint)
                contract.confidence = min(contract.confidence, 0.79)
                return contract, "deterministic-fallback"
        return self._deterministic_extract(filename, text, counterparty_hint), "deterministic-local"

    def _gemini_extract(
        self, filename: str, text: str, counterparty_hint: str | None
    ) -> ExpectationContract:
        from google import genai
        from google.genai import types

        client_kwargs: dict[str, Any] = {}
        if self.settings.google_genai_use_vertexai:
            client_kwargs.update(
                vertexai=True,
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
            )
        else:
            client_kwargs["api_key"] = self.settings.google_api_key
        client = genai.Client(**client_kwargs)
        prompt = (
            f"Filename: {filename}\n"
            f"Counterparty hint: {counterparty_hint or 'none'}\n\n"
            f"Evidence:\n{text}"
        )
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ExpectationExtraction,
                temperature=0.1,
            ),
        )
        extracted = response.parsed or ExpectationExtraction.model_validate_json(response.text)
        return self._to_contract(filename, text, extracted)

    def _deterministic_extract(
        self, filename: str, text: str, counterparty_hint: str | None
    ) -> ExpectationContract:
        amount_match = re.search(
            r"(?:₹|INR\s*)\s*([0-9][0-9,]*)\s*(?:/\s*month|per month|monthly)", text, re.I
        )
        duration_match = re.search(r"(?:for|fixed for)\s+(\d+)\s+months?", text, re.I)
        free_install = re.search(
            r"installation\s+(?:is\s+)?(?:completely\s+)?free|free\s+installation", text, re.I
        )
        merchant_match = re.search(r"(?:welcome to|from)\s+([A-Z][A-Za-z0-9 -]{2,30})", text)
        counterparty = counterparty_hint or (
            merchant_match.group(1).strip() if merchant_match else "Unknown provider"
        )
        terms: list[ExtractedTerm] = []
        if amount_match:
            terms.append(
                ExtractedTerm(
                    key="monthly_price",
                    label="Monthly plan",
                    value=int(amount_match.group(1).replace(",", "")),
                    unit="INR/month",
                    confidence=0.94,
                    evidence_quote=amount_match.group(0),
                )
            )
        if free_install:
            terms.append(
                ExtractedTerm(
                    key="installation_fee",
                    label="Installation",
                    value=0,
                    unit="INR",
                    confidence=0.98,
                    evidence_quote=free_install.group(0),
                )
            )
        if duration_match:
            terms.append(
                ExtractedTerm(
                    key="duration_months",
                    label="Price guarantee",
                    value=int(duration_match.group(1)),
                    unit="months",
                    confidence=0.93,
                    evidence_quote=duration_match.group(0),
                )
            )
        if not terms:
            terms.append(
                ExtractedTerm(
                    key="unresolved_term",
                    label="Unresolved commitment",
                    value="requires confirmation",
                    kind="soft",
                    confidence=0.35,
                    evidence_quote=text[:180],
                )
            )
        extraction = ExpectationExtraction(
            counterparty=counterparty,
            subject="Consumer service agreement",
            terms=terms,
            verification_rule="Future bills and provider responses must match the captured measurable terms.",
            confidence=min(term.confidence for term in terms),
        )
        return self._to_contract(filename, text, extraction)

    @staticmethod
    def _to_contract(
        filename: str, text: str, extracted: ExpectationExtraction
    ) -> ExpectationContract:
        evidence = []
        terms = []
        for index, term in enumerate(extracted.terms, start=1):
            evidence_id = f"ev_extracted_{index}"
            evidence.append(
                make_evidence(evidence_id, filename, text, term.evidence_quote, "matched passage")
            )
            terms.append(
                Term(
                    key=term.key,
                    label=term.label,
                    value=term.value,
                    unit=term.unit,
                    kind=term.kind,
                    confidence=term.confidence,
                    evidence_id=evidence_id,
                )
            )
        return ExpectationContract(
            counterparty=extracted.counterparty,
            subject=extracted.subject,
            effective_at=datetime.now(UTC),
            terms=terms,
            verification_rule=extracted.verification_rule,
            evidence=evidence,
            confidence=extracted.confidence,
            allowed_actions=[ActionLevel.INFORM, ActionLevel.PREPARE],
        )


def build_adk_registry(settings: Settings) -> list[dict[str, str]]:
    """Expose the real ADK fleet definition for runtime discovery and judging."""
    instructions = {
        "expectation_agent": "Compile evidence-backed promises into expectation contracts.",
        "observation_agent": "Extract actual outcomes without inferring missing facts.",
        "judge_agent": "Classify deltas as explained, unexplained, or uncertain with evidence.",
        "resolution_agent": "Prepare the least risky permitted corrective action.",
        "owed_agent": "Monitor new promises until verified completion or escalation.",
        "guardian_agent": "Deny actions beyond the user's explicit permission boundary.",
    }
    registry = []
    for name, instruction in instructions.items():
        registry.append(
            {
                "name": name,
                "model": settings.gemini_model,
                "instruction": instruction,
                "framework": "Google ADK",
            }
        )
    return registry


def create_adk_fleet(settings: Settings):
    """Create executable Google ADK agents; imported lazily for fast local startup."""
    from google.adk.agents import LlmAgent, SequentialAgent

    agents = [
        LlmAgent(
            model=settings.gemini_model, name="expectation_agent", instruction=SYSTEM_INSTRUCTION
        ),
        LlmAgent(
            model=settings.gemini_model,
            name="observation_agent",
            instruction="Extract observed facts and cite evidence. Never invent missing values.",
        ),
        LlmAgent(
            model=settings.gemini_model,
            name="judge_agent",
            instruction="Judge deterministic deltas using evidence; preserve uncertainty and legitimate fees.",
        ),
        LlmAgent(
            model=settings.gemini_model,
            name="resolution_agent",
            instruction="Prepare the lowest-risk resolution allowed by the permission boundary.",
        ),
        LlmAgent(
            model=settings.gemini_model,
            name="owed_agent",
            instruction="Convert provider promises into monitored obligations with deadlines and verification rules.",
        ),
        LlmAgent(
            model=settings.gemini_model,
            name="guardian_agent",
            instruction="Block unauthorized, sensitive, legal, spending, settlement, or rights-waiving actions.",
        ),
    ]
    return SequentialAgent(name="realitycheck_fleet", sub_agents=agents)
