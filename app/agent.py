"""
Agent Orchestrator — the core workflow engine.

Chains together all components:
    1. Ambiguity detection
    2. Schema loading
    3. SQL generation (with conversation context)
    4. Safety validation
    5. Query execution (with retry on failure)
    6. SQL explanation
    7. Follow-up question generation
    8. Result formatting

Also manages conversation memory for multi-turn interactions.
"""

import time
import logging
from typing import Any

from app import llm_service
from app.database import get_schema_info, execute_query
from app.safety import validate_sql, validate_user_input
from app.formatter import format_response, format_error, format_ambiguity

logger = logging.getLogger(__name__)


# ─── Conversation Memory ────────────────────────────────────────
class ConversationMemory:
    """
    In-memory conversation store for multi-turn context.

    Maintains per-session history of Q&A pairs, limited to the
    last MAX_TURNS entries to prevent context overflow.
    """

    MAX_TURNS = 10

    def __init__(self) -> None:
        self._sessions: dict[str, list[dict[str, str]]] = {}

    def get_history(self, session_id: str) -> str:
        """
        Get formatted conversation history for a session.

        Returns:
            A formatted string of previous Q&A pairs, or empty string.
        """
        turns = self._sessions.get(session_id, [])
        if not turns:
            return ""

        lines = []
        for turn in turns:
            lines.append(f"User: {turn['question']}")
            lines.append(f"SQL: {turn['sql']}")
        return "\n".join(lines)

    def add_turn(self, session_id: str, question: str, sql: str) -> None:
        """Record a Q&A turn for a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append({
            "question": question,
            "sql": sql,
        })

        # Trim to last MAX_TURNS
        if len(self._sessions[session_id]) > self.MAX_TURNS:
            self._sessions[session_id] = self._sessions[session_id][-self.MAX_TURNS:]

    def clear(self, session_id: str) -> None:
        """Clear history for a session."""
        self._sessions.pop(session_id, None)


# Global conversation memory instance
memory = ConversationMemory()


# ─── Agent Workflow ──────────────────────────────────────────────
def process_question(question: str, session_id: str = "default") -> dict[str, Any]:
    """
    Process a natural language question through the full agent pipeline.

    Args:
        question: The user's natural language question.
        session_id: Optional session ID for conversation memory.

    Returns:
        A structured response dict (success, error, or ambiguity).
    """
    start_time = time.time()

    try:
        # ── Step 0: Input safety check ────────────────────────
        is_safe_input, input_msg = validate_user_input(question)
        if not is_safe_input:
            logger.warning("Blocked destructive user input: %s", question)
            elapsed = round(time.time() - start_time, 3)
            return format_error(
                question=question,
                error_message=input_msg,
                execution_time=f"{elapsed}s",
            )

        # ── Step 1: Load schema ──────────────────────────────
        schema = get_schema_info()
        logger.info("Schema loaded for LLM context")

        # ── Step 1b: Load conversation history ────────────────
        history = memory.get_history(session_id)

        # ── Step 2: Ambiguity check ──────────────────────────
        ambiguity = llm_service.check_ambiguity(question, schema, history)
        if ambiguity.get("is_ambiguous", False):
            logger.info("Question flagged as ambiguous: %s", ambiguity.get("reason"))
            elapsed = round(time.time() - start_time, 3)
            return format_ambiguity(
                question=question,
                suggestions=ambiguity.get("suggestions", []),
                reason=ambiguity.get("reason", ""),
                execution_time=f"{elapsed}s",
            )

        # ── Step 3: Generate SQL ─────────────────────────────
        generated_sql = llm_service.generate_sql(question, schema, history)

        # ── Step 4: Safety validation ────────────────────────
        is_safe, safety_msg = validate_sql(generated_sql)
        if not is_safe:
            elapsed = round(time.time() - start_time, 3)
            return format_error(
                question=question,
                error_message=safety_msg,
                generated_sql=generated_sql,
                execution_time=f"{elapsed}s",
            )

        # ── Step 5: Execute SQL ──────────────────────────────
        try:
            results = execute_query(generated_sql)
        except Exception as exec_error:
            logger.warning("SQL execution failed: %s — attempting retry", exec_error)

            # ── Step 5b: Retry mechanism ─────────────────────
            try:
                corrected_sql = llm_service.retry_sql(
                    question=question,
                    failed_sql=generated_sql,
                    error_message=str(exec_error),
                    schema=schema,
                )

                # Validate the corrected SQL too
                is_safe, safety_msg = validate_sql(corrected_sql)
                if not is_safe:
                    elapsed = round(time.time() - start_time, 3)
                    return format_error(
                        question=question,
                        error_message=safety_msg,
                        generated_sql=corrected_sql,
                        execution_time=f"{elapsed}s",
                    )

                results = execute_query(corrected_sql)
                generated_sql = corrected_sql  # Use the corrected version
                logger.info("Retry succeeded with corrected SQL")

            except Exception as retry_error:
                logger.error("Retry also failed: %s", retry_error)
                elapsed = round(time.time() - start_time, 3)
                return format_error(
                    question=question,
                    error_message=(
                        "Unable to execute generated SQL. The AI tried to "
                        "correct the query but was unsuccessful. Please try "
                        "rephrasing your question."
                    ),
                    generated_sql=generated_sql,
                    execution_time=f"{elapsed}s",
                )

        # ── Step 6: Generate explanation ─────────────────────
        try:
            explanation = llm_service.explain_sql(generated_sql, question)
        except Exception:
            explanation = "SQL explanation unavailable."

        # ── Step 7: Generate follow-up questions ─────────────
        try:
            follow_ups = llm_service.generate_follow_up_questions(
                question=question,
                sql=generated_sql,
                row_count=len(results),
                schema=schema,
            )
        except Exception:
            follow_ups = []

        # ── Step 8: Record in conversation memory ────────────
        memory.add_turn(session_id, question, generated_sql)

        # ── Step 9: Format and return ────────────────────────
        elapsed = round(time.time() - start_time, 3)
        return format_response(
            question=question,
            generated_sql=generated_sql,
            explanation=explanation,
            results=results,
            execution_time=f"{elapsed}s",
            follow_up_questions=follow_ups,
        )

    except Exception as e:
        logger.exception("Unexpected error in agent pipeline")
        elapsed = round(time.time() - start_time, 3)
        return format_error(
            question=question,
            error_message=f"An unexpected error occurred: {str(e)}",
            execution_time=f"{elapsed}s",
        )
