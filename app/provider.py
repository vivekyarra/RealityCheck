from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


@dataclass(frozen=True)
class CorrectionRequest:
    case_id: str
    counterparty: str
    disputed_amount: int
    evidence_ids: tuple[str, ...]
    requested_resolution: str


@dataclass(frozen=True)
class ProviderReply:
    reference: str
    message: str
    promised_amount: int
    promised_by: datetime


class ProviderConnector(Protocol):
    def submit_correction(self, request: CorrectionRequest) -> ProviderReply: ...


class FiberMaxSandboxConnector:
    """Deterministic external-system boundary for safe public judging."""

    def submit_correction(self, request: CorrectionRequest) -> ProviderReply:
        if request.counterparty != "FiberMax":
            raise ValueError("The FiberMax sandbox only accepts FiberMax cases.")
        if request.disputed_amount != 350 or len(request.evidence_ids) < 2:
            raise ValueError("The correction request is missing the verified dispute packet.")
        promised_by = datetime.now(UTC) + timedelta(hours=48)
        return ProviderReply(
            reference="FM-CREDIT-350",
            message=(
                "We reviewed the original welcome offer. A ₹350 credit is approved "
                "and will appear on your account within 48 hours. Reference: FM-CREDIT-350."
            ),
            promised_amount=350,
            promised_by=promised_by,
        )
