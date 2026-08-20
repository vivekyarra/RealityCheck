from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class CaseStatus(StrEnum):
    CAPTURED = "captured"
    MISMATCH = "mismatch"
    NEEDS_APPROVAL = "needs_approval"
    RESOLVING = "resolving"
    MONITORING = "monitoring"
    RECOVERED = "recovered"
    CLOSED = "closed"
    UNCERTAIN = "uncertain"


class Classification(StrEnum):
    EXPLAINED = "explained"
    UNEXPLAINED = "unexplained"
    UNCERTAIN = "uncertain"


class ActionLevel(StrEnum):
    INFORM = "L0"
    PREPARE = "L1"
    SEND = "L2"
    ESCALATE = "L3"
    SENSITIVE = "L4"


class EvidenceRef(BaseModel):
    id: str
    filename: str
    media_type: str = "text/plain"
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    span: str
    quote: str
    captured_at: datetime = Field(default_factory=utc_now)


class Term(BaseModel):
    key: str
    label: str
    value: str | int | float | Decimal | bool
    unit: str | None = None
    kind: str = "hard"
    confidence: float = Field(ge=0, le=1)
    evidence_id: str


class ExpectationContract(BaseModel):
    id: str = Field(default_factory=lambda: f"exp_{uuid4().hex[:12]}")
    counterparty: str
    subject: str
    effective_at: datetime
    deadline_at: datetime | None = None
    terms: list[Term]
    verification_rule: str
    evidence: list[EvidenceRef]
    confidence: float = Field(ge=0, le=1)
    allowed_actions: list[ActionLevel] = Field(
        default_factory=lambda: [ActionLevel.INFORM, ActionLevel.PREPARE]
    )
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("terms")
    @classmethod
    def require_terms(cls, value: list[Term]) -> list[Term]:
        if not value:
            raise ValueError("an expectation contract needs at least one term")
        return value

    @model_validator(mode="after")
    def require_unique_grounded_terms(self):
        keys = [term.key for term in self.terms]
        if len(keys) != len(set(keys)):
            raise ValueError("expectation term keys must be unique")
        evidence_ids = {item.id for item in self.evidence}
        if any(term.evidence_id not in evidence_ids for term in self.terms):
            raise ValueError("every expectation term must reference included evidence")
        return self


class Observation(BaseModel):
    id: str = Field(default_factory=lambda: f"obs_{uuid4().hex[:12]}")
    expectation_id: str
    source: str
    observed_at: datetime
    terms: list[Term]
    evidence: list[EvidenceRef]
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def require_unique_grounded_terms(self):
        keys = [term.key for term in self.terms]
        if len(keys) != len(set(keys)):
            raise ValueError("observation term keys must be unique")
        evidence_ids = {item.id for item in self.evidence}
        if any(term.evidence_id not in evidence_ids for term in self.terms):
            raise ValueError("every observation term must reference included evidence")
        return self


class Delta(BaseModel):
    key: str
    label: str
    expected: str | int | float | Decimal | bool | None
    actual: str | int | float | Decimal | bool | None
    amount: Decimal | None = None
    classification: Classification
    material: bool
    explanation: str
    expected_evidence_id: str | None = None
    actual_evidence_id: str | None = None


class RealityDiff(BaseModel):
    id: str = Field(default_factory=lambda: f"diff_{uuid4().hex[:12]}")
    expectation_id: str
    observation_id: str
    deltas: list[Delta]
    net_amount: Decimal = Decimal("0")
    currency: str = "INR"
    confidence: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=utc_now)


class Obligation(BaseModel):
    id: str = Field(default_factory=lambda: f"obl_{uuid4().hex[:12]}")
    promise: str
    amount: Decimal | None = None
    currency: str = "INR"
    deadline_at: datetime
    verification_rule: str
    status: str = "open"
    evidence_id: str


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:12]}")
    at: datetime = Field(default_factory=utc_now)
    actor: str
    action: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str
    event_hash: str


class ReconciliationCase(BaseModel):
    id: str = Field(default_factory=lambda: f"case_{uuid4().hex[:12]}")
    title: str
    status: CaseStatus = CaseStatus.CAPTURED
    expectation: ExpectationContract
    observations: list[Observation] = Field(default_factory=list)
    reality_diff: RealityDiff | None = None
    obligations: list[Obligation] = Field(default_factory=list)
    audit: list[AuditEvent] = Field(default_factory=list)
    recovered_amount: Decimal = Decimal("0")
    currency: str = "INR"
    next_action_at: datetime | None = None
    approval_required: bool = False
    updated_at: datetime = Field(default_factory=utc_now)

    def record(
        self,
        actor: str,
        action: str,
        summary: str,
        evidence_ids: list[str] | None = None,
        **metadata: Any,
    ) -> None:
        previous_hash = self.audit[-1].event_hash if self.audit else "GENESIS"
        event_data = {
            "id": f"aud_{uuid4().hex[:12]}",
            "at": utc_now(),
            "actor": actor,
            "action": action,
            "summary": summary,
            "evidence_ids": evidence_ids or [],
            "metadata": metadata,
            "previous_hash": previous_hash,
        }
        canonical = json.dumps(event_data, sort_keys=True, separators=(",", ":"), default=str)
        event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.audit.append(AuditEvent(**event_data, event_hash=event_hash))
        self.updated_at = utc_now()

    def audit_chain_valid(self) -> bool:
        previous_hash = "GENESIS"
        for event in self.audit:
            event_data = event.model_dump(exclude={"event_hash"})
            canonical = json.dumps(event_data, sort_keys=True, separators=(",", ":"), default=str)
            expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if event.previous_hash != previous_hash or event.event_hash != expected:
                return False
            previous_hash = event.event_hash
        return True


class AdvanceRequest(BaseModel):
    step: str
    approve: bool = False


class TextEvidenceRequest(BaseModel):
    filename: str = "evidence.txt"
    text: str = Field(min_length=10, max_length=100_000)
    counterparty_hint: str | None = None
