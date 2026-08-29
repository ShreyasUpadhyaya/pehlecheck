"""FastAPI boundary for the synthetic EPF preflight demo."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .graph import PreflightState, preflight_graph
from .llm import DraftMessageResult, draft_message
from .models import Actor, MemberProfile, RuleResult


_MEMBERS_PATH = Path(__file__).parent / "data" / "members.json"
_MEMBERS: dict[str, MemberProfile] = {
    uan: MemberProfile.model_validate(profile)
    for uan, profile in json.loads(_MEMBERS_PATH.read_text(encoding="utf-8")).items()
}


class PreflightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uan: str
    intake_text: str = ""
    language: str = "en"


class OverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: PreflightState
    overrides: dict[str, Any] = Field(default_factory=dict)


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: PreflightState
    recipient: Actor = Actor.EMPLOYER


class SubmitMockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: PreflightState
    review_confirmed: bool = False


class SubmitMockResponse(BaseModel):
    submitted: bool
    blocking_rule_ids: list[str] = Field(default_factory=list)
    needs_human_review: list[str] = Field(default_factory=list)


app = FastAPI(title="PehleCheck")


def _profile_for_uan(uan: str) -> MemberProfile:
    try:
        return _MEMBERS[uan]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown synthetic demo UAN") from exc


def _run_preflight(
    profile: MemberProfile,
    intake_text: str,
    language: str,
) -> PreflightState:
    initial = PreflightState(
        intake_text=intake_text,
        language=language,
        profile=profile,
    )
    output = preflight_graph.invoke(initial.model_dump())
    return PreflightState.model_validate(output)


@app.post("/preflight", response_model=PreflightState)
def preflight(request: PreflightRequest) -> PreflightState:
    return _run_preflight(
        _profile_for_uan(request.uan),
        request.intake_text,
        request.language,
    )


@app.post("/override", response_model=PreflightState)
def override(request: OverrideRequest) -> PreflightState:
    try:
        profile = MemberProfile.model_validate(
            {**request.state.profile.model_dump(), **request.overrides}
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _run_preflight(profile, request.state.intake_text, request.state.language)


@app.post("/draft", response_model=DraftMessageResult)
def draft(request: DraftRequest) -> DraftMessageResult:
    results: list[RuleResult] = request.state.ordered_results or request.state.fired_results
    return draft_message(results, recipient=request.recipient, language=request.state.language)


@app.post("/submit-mock", response_model=SubmitMockResponse)
def submit_mock(request: SubmitMockRequest) -> SubmitMockResponse:
    blockers = [
        result.rule_id
        for result in request.state.fired_results
        if result.severity.value == "BLOCKER"
    ]
    return SubmitMockResponse(
        submitted=request.review_confirmed and not blockers,
        blocking_rule_ids=blockers,
        needs_human_review=request.state.needs_human_review,
    )


_FRONTEND_ROOT = Path(__file__).parents[1] / "frontend"
_FRONTEND_BUILD = _FRONTEND_ROOT / "dist"
_STATIC_ROOT = _FRONTEND_BUILD if _FRONTEND_BUILD.is_dir() else _FRONTEND_ROOT
app.mount("/", StaticFiles(directory=_STATIC_ROOT, html=True), name="frontend")
