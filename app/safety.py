"""
SQL Safety Validator — blocks destructive queries before execution.

Only allows read-only SELECT statements (including CTEs with WITH).
Blocks DROP, DELETE, UPDATE, ALTER, TRUNCATE, CREATE, INSERT, GRANT, REVOKE.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Destructive SQL keywords that must be blocked
BLOCKED_KEYWORDS: list[str] = [
    "DROP",
    "DELETE",
    "UPDATE",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "INSERT",
    "GRANT",
    "REVOKE",
    "REPLACE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
]

# Compile regex patterns for each blocked keyword
# Match whole words only (e.g., "DROP" but not "DROPPED" in a string literal)
BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(rf"\b{kw}\b", re.IGNORECASE) for kw in BLOCKED_KEYWORDS
]

# Allowed starting keywords
ALLOWED_STARTS = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


def _strip_sql_comments(sql: str) -> str:
    """Remove SQL comments to prevent obfuscation attacks."""
    # Remove single-line comments (-- ...)
    sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    # Remove multi-line comments (/* ... */)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql.strip()


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate that a SQL query is safe to execute.

    Checks:
        1. Query is not empty
        2. Query starts with SELECT or WITH (CTE)
        3. Query does not contain destructive keywords

    Args:
        sql: The SQL query string to validate.

    Returns:
        Tuple of (is_safe, error_message).
        If safe: (True, "")
        If unsafe: (False, "Descriptive error message")
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query received."

    # Strip comments to prevent obfuscation
    cleaned_sql = _strip_sql_comments(sql)

    if not cleaned_sql:
        return False, "SQL query contains only comments."

    # Check that query starts with SELECT or WITH
    if not ALLOWED_STARTS.match(cleaned_sql):
        logger.warning("Blocked SQL — does not start with SELECT/WITH: %s", sql[:100])
        return False, (
            "Unsafe query blocked. Only read-only SELECT queries are allowed. "
            "Your query does not appear to be a SELECT statement."
        )

    # Check for destructive keywords
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(cleaned_sql):
            keyword = pattern.pattern.replace(r"\b", "").upper()
            logger.warning("Blocked SQL — contains '%s': %s", keyword, sql[:100])
            return False, (
                f"Unsafe query blocked. The query contains a destructive operation "
                f"({keyword}). Only read-only SELECT queries are allowed."
            )

    # Check for multiple statements (semicolon followed by more SQL)
    # Allow trailing semicolons but block chained statements
    statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]
    if len(statements) > 1:
        logger.warning("Blocked SQL — multiple statements detected: %s", sql[:100])
        return False, (
            "Unsafe query blocked. Multiple SQL statements detected. "
            "Only single SELECT queries are allowed."
        )

    logger.info("SQL validated as safe: %s", sql[:100])
    return True, ""


# ─── User Input Safety Check ───────────────────────────────────
# Patterns to detect destructive intent in user's natural language input
INPUT_DESTRUCTIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(DROP)\s+(TABLE|DATABASE|INDEX|VIEW)\b", re.IGNORECASE),
    re.compile(r"\b(DELETE)\s+(FROM|ALL|EVERY)\b", re.IGNORECASE),
    re.compile(r"\b(UPDATE)\s+\w+\s+SET\b", re.IGNORECASE),
    re.compile(r"\b(TRUNCATE)\s+(TABLE)?\b", re.IGNORECASE),
    re.compile(r"\b(ALTER)\s+(TABLE|DATABASE)\b", re.IGNORECASE),
    re.compile(r"\b(INSERT)\s+(INTO)\b", re.IGNORECASE),
    re.compile(r"\bDROP\b", re.IGNORECASE),
    re.compile(r"\bDELETE\b.*\b(employee|department|project|record|row|data|table|all|everything)\b", re.IGNORECASE),
    re.compile(r"\b(remove|destroy|erase|wipe)\b.*\b(table|database|data|all|everything|record)\b", re.IGNORECASE),
]


def validate_user_input(question: str) -> tuple[bool, str]:
    """
    Check the user's raw question for destructive intent before
    it reaches the LLM. This prevents the LLM from cleverly
    converting destructive requests into safe-looking SELECT queries.

    Args:
        question: The raw user question string.

    Returns:
        Tuple of (is_safe, error_message).
        If safe: (True, "")
        If unsafe: (False, "Descriptive error message")
    """
    for pattern in INPUT_DESTRUCTIVE_PATTERNS:
        if pattern.search(question):
            keyword = pattern.search(question).group(0).upper()
            logger.warning("Blocked user input — destructive intent detected: '%s'", keyword)
            return False, (
                f"Destructive query blocked. Your request contains a destructive "
                f"operation ({keyword}). This agent only supports read-only SELECT queries. "
                f"Data modification is not permitted for security reasons."
            )

    return True, ""

