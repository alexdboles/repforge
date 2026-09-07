from datetime import date
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    simulation_id: str = Field(max_length=80)
    rating: int = Field(ge=1, le=5, strict=True)


class FeedbackResponse(BaseModel):
    saved: bool = True


class EvidenceSummary(BaseModel):
    start: date
    end: date
    sample_size: int
    demo_starts: int
    first_replies: int
    completed_grading: int
    completion_rate: float
    returning_users: int
    retry_starts: int
    retry_completions: int
    comparable_improvements: int
    feedback_count: int
    feedback_average: float | None = None
    note: str