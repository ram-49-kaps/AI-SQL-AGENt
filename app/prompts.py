"""
Prompt templates for the AI SQL Agent.

All LLM prompts are centralized here for easy tuning and maintenance.
Each prompt is a format string with clearly named placeholders.
"""

# ─── System Prompt ───────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert SQL assistant for a company database running SQLite.

Your job is to convert natural language questions into valid SQLite SQL queries.

RULES:
1. Generate ONLY valid SQLite SQL — no explanations, no markdown, no code blocks.
2. Use ONLY the table and column names provided in the schema below.
3. ONLY generate SELECT queries. Never generate DROP, DELETE, UPDATE, INSERT, ALTER, or any destructive statements.
4. Respect foreign key relationships between tables.
5. Use proper JOINs when querying across related tables.
6. For date comparisons, use ISO format (YYYY-MM-DD) and the DATE() function when needed.
7. Always use table aliases for readability in JOIN queries.
8. If selecting columns with the same name from different tables (e.g., both tables have a 'name' column), you MUST alias them (e.g., `SELECT e.name AS employee_name, d.name AS department_name`).
9. If a question asks for "overdue" or "late" projects, compare the deadline with the current date using DATE('now') AND ensure the status is NOT 'Completed'.
10. If a question asks for projects with a specific status like "active", "completed", "delayed", or "pending", query for that EXACT status explicitly using a case-insensitive match. Do not group multiple statuses together unless asked.
11. String comparisons must be case-insensitive (e.g. use `LOWER(column) = LOWER('value')` or `LIKE`).
12. Return ONLY the SQL query — nothing else. No explanation, no comments.

DATABASE SCHEMA:
{schema}
"""

# ─── SQL Generation Prompt ───────────────────────────────────────
SQL_GENERATION_PROMPT = """Given the database schema above, generate a SQL query for this question:

{conversation_context}

Current question: {question}

Remember: Return ONLY the raw SQL query. No markdown, no explanation, no code fences."""

# ─── SQL Retry Prompt ────────────────────────────────────────────
RETRY_PROMPT = """The previous SQL query failed with an error. Please generate a corrected query.

Original question: {question}

Failed SQL query:
{failed_sql}

Error message:
{error_message}

Please generate a corrected SQL query that fixes the error.
Return ONLY the raw SQL query — no explanation, no markdown."""

# ─── Ambiguity Detection Prompt ─────────────────────────────────
AMBIGUITY_PROMPT = """Analyze the following user question about a company database and determine if it is ambiguous or too vague to generate a precise SQL query.

DATABASE SCHEMA:
{schema}

{conversation_context}

USER QUESTION: "{question}"

A question is AMBIGUOUS ONLY if:
- It is extremely vague with NO entity mentioned (e.g. "show data", "give me info", "tell me something")
- It is a single generic word like "data" or "info"

A question is CLEAR if ANY of these are true (mark as NOT ambiguous):
- It mentions any entity like "employees", "projects", "departments", or "salaries"
- It uses words like "show", "list", "get", "find", "display" followed by an entity
- It uses conditions like "overdue", "active", "highest", "lowest", "recent", "after", "before"
- It asks about a specific department (e.g. "Engineering employees" is CLEAR)
- It is a FOLLOW-UP question that references previous context using words like "those", "them", "they", "now", "also", "their", "these" — this is ALWAYS CLEAR because the context comes from the previous conversation

IMPORTANT: When in doubt, mark the question as CLEAR (is_ambiguous: false). Only flag truly meaningless questions.

Respond in this exact JSON format (no markdown, no code fences):
{{"is_ambiguous": true/false, "reason": "brief explanation", "suggestions": ["specific question 1", "specific question 2", "specific question 3"]}}

If the question is clear, set is_ambiguous to false and leave suggestions as an empty list.
If ambiguous, provide 2-3 specific alternative questions the user might mean."""

# ─── SQL Explanation Prompt ──────────────────────────────────────
EXPLANATION_PROMPT = """Explain this SQL query in plain English for a non-technical user.
Keep the explanation concise (1-3 sentences).

SQL Query:
{sql}

Original Question: {question}

Provide ONLY the plain English explanation — no SQL, no markdown, no formatting."""

# ─── Follow-up Questions Prompt ──────────────────────────────────
FOLLOW_UP_PROMPT = """Based on the user's question and the SQL query results, suggest 2-3 relevant follow-up questions they might want to ask.

DATABASE SCHEMA:
{schema}

User's question: "{question}"

Generated SQL: {sql}

Row count returned: {row_count}

Respond in this exact JSON format (no markdown, no code fences):
{{"follow_up_questions": ["question 1", "question 2", "question 3"]}}

Make the follow-up questions natural, specific, and directly related to the original query.
They should explore the data further or drill down into the results."""
