"""Typed data contracts for the pre-submission rules engine."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    INFO = "INFO"


class Actor(StrEnum):
    CITIZEN = "CITIZEN"
    EMPLOYER = "EMPLOYER"
    BANK = "BANK"


class MemberProfile(BaseModel):
    """A synthetic member record used by the rules engine.

    Defaults make it possible for callers to construct a focused fixture for
    one rule without supplying unrelated fields.  No field contains real
    identity data.
    """

    model_config = ConfigDict(extra="forbid")

    uan_activated: bool = True
    kyc_approved: bool = True
    name_as_per_epfo: str = ""
    name_as_per_aadhaar: str = ""
    dob_epfo: date | None = None
    dob_aadhaar: date | None = None
    date_of_exit: date | None = None
    claim_type: str = ""
    bank_ifsc_verified: bool = True
    account_holder_name: str = ""
    account_is_joint: bool = False
    aadhaar_seeded: bool = True
    service_months: int = Field(default=0, ge=0)
    claim_amount: Decimal = Decimal("0")
    employment_status: str = "NOT_EMPLOYED"
    member_ids: list[str] = Field(default_factory=list)
    untransferred_member_ids: list[str] = Field(default_factory=list)
    eps_contribution_months: int = Field(default=0, ge=0)
    claim_purpose: str = ""


class RuleResult(BaseModel):
    rule_id: str
    severity: Severity
    actor: Actor
    field_read: str
    observed_value: Any
    why: str
    fix: str
    eta_days: int = Field(ge=0)
    source_note: str
