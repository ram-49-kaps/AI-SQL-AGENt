"""
Response Formatter — structures all API responses consistently.

Provides three response types:
    - Success: question + SQL + explanation + results + metadata
    - Error: question + error message + optional SQL
    - Ambiguity: question + suggestions for clarification
"""

from typing import Any


def format_response(
    question: str,
    generated_sql: str,
    explanation: str,
    results: list[dict[str, Any]],
    execution_time: str,
    follow_up_questions: list[str] | None = None,
) -> dict[str, Any]:
    """
    Format a successful query response.

    Args:
        question: The original natural language question.
        generated_sql: The SQL query that was generated and executed.
        explanation: Plain English explanation of the SQL.
        results: List of result row dicts.
        execution_time: Total processing time string.
        follow_up_questions: Optional list of suggested follow-up questions.

    Returns:
        Structured response dictionary.
    """
    response: dict[str, Any] = {
        "success": True,
        "question": question,
        "generated_sql": generated_sql,
        "explanation": explanation,
        "execution_time": execution_time,
        "row_count": len(results),
        "result": results,
    }

    if follow_up_questions:
        response["follow_up_questions"] = follow_up_questions

    return response


def format_error(
    question: str,
    error_message: str,
    generated_sql: str | None = None,
    execution_time: str = "0s",
) -> dict[str, Any]:
    """
    Format an error response.

    Args:
        question: The original question.
        error_message: Description of what went wrong.
        generated_sql: The SQL that caused the error (if available).
        execution_time: Processing time before failure.

    Returns:
        Structured error response dictionary.
    """
    response: dict[str, Any] = {
        "success": False,
        "question": question,
        "error": error_message,
        "execution_time": execution_time,
    }

    if generated_sql:
        response["generated_sql"] = generated_sql

    return response


def format_ambiguity(
    question: str,
    suggestions: list[str],
    reason: str = "",
    execution_time: str = "0s",
) -> dict[str, Any]:
    """
    Format an ambiguity response with clarification suggestions.

    Args:
        question: The original ambiguous question.
        suggestions: List of specific alternative questions.
        reason: Why the question was deemed ambiguous.
        execution_time: Processing time.

    Returns:
        Structured ambiguity response dictionary.
    """
    return {
        "success": False,
        "question": question,
        "message": "Your request is ambiguous. Please try one of the suggested questions below.",
        "reason": reason,
        "suggestions": suggestions,
        "execution_time": execution_time,
    }
