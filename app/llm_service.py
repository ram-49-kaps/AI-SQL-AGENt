"""
LLM Service — wraps Groq API (Llama 3.3 70B) for SQL generation and analysis.

Provides methods for:
    - SQL generation from natural language
    - Ambiguity detection
    - SQL explanation in plain English
    - SQL retry with error context
    - Follow-up question generation
"""

import os
import json
import logging
import re

from groq import Groq
from dotenv import load_dotenv

from app.prompts import (
    SYSTEM_PROMPT,
    SQL_GENERATION_PROMPT,
    RETRY_PROMPT,
    AMBIGUITY_PROMPT,
    EXPLANATION_PROMPT,
    FOLLOW_UP_PROMPT,
)

load_dotenv()
logger = logging.getLogger(__name__)

# ─── Configure Groq ──────────────────────────────────────────────
API_KEY = os.getenv("GROQ_API_KEY", "")
if not API_KEY or API_KEY == "your_groq_api_key_here":
    logger.warning("GROQ_API_KEY not set — LLM calls will fail.")

client = Groq(api_key=API_KEY)

# Model configuration
MODEL_NAME = "llama-3.3-70b-versatile"


def _call_llm(system_instruction: str, prompt: str) -> str:
    """
    Call the Groq API with a system instruction and user prompt.

    Args:
        system_instruction: The system message to set context.
        prompt: The user prompt to send.

    Returns:
        The raw text response from the model.
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1024,
        top_p=0.95,
    )
    return response.choices[0].message.content


def _clean_sql(raw: str) -> str:
    """
    Clean LLM output to extract raw SQL.

    Strips markdown code fences, backticks, and extra whitespace
    that the model sometimes adds despite instructions.
    """
    text = raw.strip()

    # Remove markdown code fences (```sql ... ``` or ``` ... ```)
    text = re.sub(r"```(?:sql)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*$", "", text)

    # Remove inline backticks
    text = text.strip("`").strip()

    # Remove trailing semicolons for consistency (we add them if needed)
    text = text.rstrip(";").strip()

    return text


def _parse_json_response(raw: str) -> dict:
    """
    Parse a JSON response from the LLM, handling common formatting issues.

    The model sometimes wraps JSON in markdown code fences.
    """
    text = raw.strip()

    # Remove markdown code fences
    text = re.sub(r"```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from LLM: %s\nRaw: %s", e, text[:200])
        return {}


# ─── Public API ──────────────────────────────────────────────────

def generate_sql(question: str, schema: str, conversation_history: str = "") -> str:
    """
    Generate a SQL query from a natural language question.

    Args:
        question: The user's natural language question.
        schema: The database schema string for context.
        conversation_history: Previous Q&A turns for multi-turn context.

    Returns:
        A clean SQL query string.

    Raises:
        Exception: If the LLM call fails.
    """
    system = SYSTEM_PROMPT.format(schema=schema)

    # Build conversation context
    context = ""
    if conversation_history:
        context = f"Previous conversation:\n{conversation_history}\n"

    prompt = SQL_GENERATION_PROMPT.format(
        question=question,
        conversation_context=context,
    )

    logger.info("Generating SQL for: %s", question)
    raw_sql = _call_llm(system, prompt)
    clean = _clean_sql(raw_sql)
    logger.info("Generated SQL: %s", clean)

    return clean


def check_ambiguity(question: str, schema: str, conversation_history: str = "") -> dict:
    """
    Check if a user question is ambiguous.

    Args:
        question: The user's natural language question.
        schema: The database schema string for context.
        conversation_history: Previous Q&A turns for multi-turn context.

    Returns:
        Dict with keys: is_ambiguous (bool), reason (str), suggestions (list[str])
    """
    prompt = AMBIGUITY_PROMPT.format(schema=schema, question=question, conversation_context=conversation_history)

    logger.info("Checking ambiguity for: %s", question)
    raw = _call_llm("You are a question clarity analyzer.", prompt)
    result = _parse_json_response(raw)

    if not result:
        # If parsing fails, assume the question is clear
        return {"is_ambiguous": False, "reason": "", "suggestions": []}

    return {
        "is_ambiguous": result.get("is_ambiguous", False),
        "reason": result.get("reason", ""),
        "suggestions": result.get("suggestions", []),
    }


def explain_sql(sql: str, question: str) -> str:
    """
    Generate a plain English explanation of a SQL query.

    Args:
        sql: The SQL query to explain.
        question: The original user question for context.

    Returns:
        A human-readable explanation string.
    """
    prompt = EXPLANATION_PROMPT.format(sql=sql, question=question)

    logger.info("Generating SQL explanation")
    return _call_llm("You are a SQL explainer for non-technical users.", prompt).strip()


def retry_sql(question: str, failed_sql: str, error_message: str, schema: str) -> str:
    """
    Retry SQL generation after a failure, providing the error as context.

    Args:
        question: The original user question.
        failed_sql: The SQL query that failed.
        error_message: The database error message.
        schema: The database schema for context.

    Returns:
        A corrected SQL query string.
    """
    system = SYSTEM_PROMPT.format(schema=schema)

    prompt = RETRY_PROMPT.format(
        question=question,
        failed_sql=failed_sql,
        error_message=error_message,
    )

    logger.info("Retrying SQL generation after error: %s", error_message[:100])
    raw = _call_llm(system, prompt)
    clean = _clean_sql(raw)
    logger.info("Retry generated SQL: %s", clean)

    return clean


def generate_follow_up_questions(
    question: str, sql: str, row_count: int, schema: str
) -> list[str]:
    """
    Generate contextual follow-up questions based on the query results.

    Args:
        question: The original user question.
        sql: The generated SQL query.
        row_count: Number of rows returned.
        schema: The database schema for context.

    Returns:
        List of 2-3 follow-up question strings.
    """
    prompt = FOLLOW_UP_PROMPT.format(
        schema=schema,
        question=question,
        sql=sql,
        row_count=row_count,
    )

    logger.info("Generating follow-up questions")
    raw = _call_llm("You are a helpful data analysis assistant.", prompt)
    result = _parse_json_response(raw)

    return result.get("follow_up_questions", [])
