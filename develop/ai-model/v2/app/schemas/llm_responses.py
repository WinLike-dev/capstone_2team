"""Structured response schemas used with Gemini response_schema."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class MemoryOperation(BaseModel):
    action: str = Field(description="One of ADD, UPDATE, DELETE, KEEP")
    fact_id: str = Field(default="", description="Existing fact id for update/delete")
    text: str = Field(default="", description="New or updated fact text")


class MemoryManagerResponse(BaseModel):
    has_changes: bool = Field(description="Whether memory updates are required")
    operations: list[MemoryOperation] = Field(default_factory=list)


class SearchEvalResponse(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Search relevance score")
    reason: str = Field(default="", description="Short reason for the score")


class QueryRegenResponse(BaseModel):
    query: str = Field(description="A rewritten search query")


class SelfEvalResponse(BaseModel):
    passed: bool = Field(default=True, description="Whether the draft passes self-eval")
    reason: str = Field(default="", description="Short failure reason when not passed")


class ExerciseItem(BaseModel):
    exercise_name: str = Field(description="세부 운동명 (예: 스쿼트, 데드리프트)")
    sets: int = Field(default=3, description="세트 수")


class PlanExtractItem(BaseModel):
    name: str = Field(description="운동 종류 (workout: 근력/유산소/스트레칭 등) 또는 식사명 (diet: 아침/점심/저녁 등)")
    detail: str = Field(default="", description="해당 세션 또는 식사의 간단한 설명")
    day: str = Field(default="", description="날짜 (YYYY-MM-DD 형식)")
    ex_list: list[ExerciseItem] = Field(
        default_factory=list,
        description="workout일 때만 채움 — 세부 운동 목록 [{exercise_name, sets}, ...]",
    )


PlanType = Literal["workout", "diet"]


class DraftResponse(BaseModel):
    """Structured output from the Draft node before persona styling."""

    core_message: str = Field(description="Primary answer or main decision")
    reason_points: list[str] = Field(
        default_factory=list,
        description="Short factual reasons that support the core message",
    )
    suggested_action: str = Field(
        default="",
        description="Concrete next action or practical application",
    )
    safety_notes: list[str] = Field(
        default_factory=list,
        description="Warnings or safety notes when needed",
    )
    approval_question: Optional[str] = Field(
        default=None,
        description="Question asking the user to approve a proposed plan change",
    )
    search_grounding_summary: str = Field(
        default="",
        description="Short summary of how search evidence was used",
    )
    proposed_plan: list[PlanExtractItem] = Field(
        default_factory=list,
        description="Structured plan items when the node is proposing a plan",
    )
    proposed_plan_type: Optional[PlanType] = Field(
        default=None,
        description='Plan type when proposed_plan exists: "workout" or "diet"',
    )


class PlanExtractResponse(BaseModel):
    has_plan: bool = Field(description="Whether a plan was extracted")
    plan_type: PlanType = Field(default="workout", description="workout or diet")
    items: list[PlanExtractItem] = Field(default_factory=list)


class PlanModifyResponse(BaseModel):
    has_changes: bool = Field(description="Whether the plan contains changes")
    plan_type: PlanType = Field(default="workout", description="workout or diet")
    items: list[PlanExtractItem] = Field(default_factory=list)
