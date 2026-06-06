"""
Query Route — handles the POST /query endpoint.

Accepts a natural language question and returns structured results
from the AI SQL Agent pipeline.
"""

from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.agent import process_question

router = APIRouter()


# ─── Request / Response Models ───────────────────────────────────
class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="A natural language question about the company database.",
        examples=["How many employees are in the Engineering department?"],
    )


class QueryResponse(BaseModel):
    """Response body — flexible to handle success, error, and ambiguity."""

    success: bool
    question: str
    generated_sql: Optional[str] = None
    explanation: Optional[str] = None
    execution_time: Optional[str] = None
    row_count: Optional[int] = None
    result: Optional[list] = None
    error: Optional[str] = None
    message: Optional[str] = None
    reason: Optional[str] = None
    suggestions: Optional[list[str]] = None
    follow_up_questions: Optional[list[str]] = None


# ─── Endpoint ────────────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest,
    x_session_id: Optional[str] = Header(
        default="default",
        description="Optional session ID for multi-turn conversation memory.",
    ),
) -> dict:
    """
    Convert a natural language question to SQL and execute it.

    The agent will:
    1. Check if the question is ambiguous
    2. Generate SQL using an LLM
    3. Validate the SQL for safety
    4. Execute against the database
    5. Return formatted results with explanation

    Pass an `X-Session-Id` header to enable multi-turn conversation memory.
    """
    result = process_question(
        question=request.question,
        session_id=x_session_id or "default",
    )
    return result
