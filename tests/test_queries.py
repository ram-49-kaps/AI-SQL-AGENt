"""
Test suite for the AI SQL Agent.

Tests cover:
    - API endpoint availability
    - Request validation
    - SQL safety validation (unit tests — no LLM needed)
    - Database initialization and schema
    - Formatter output structure

Note: Tests that require LLM calls (integration tests) are marked
with pytest.mark.integration and skipped by default.
Run with: pytest -m integration to include them.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.safety import validate_sql
from app.formatter import format_response, format_error, format_ambiguity
from app.database import init_db, execute_query, get_schema_info, get_row_counts

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════
# API Endpoint Tests
# ═══════════════════════════════════════════════════════════════

class TestAPIEndpoints:
    """Test basic API endpoint availability."""

    def test_root_endpoint(self):
        """Root endpoint should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI SQL Agent"
        assert "endpoints" in data

    def test_health_check(self):
        """Health check should confirm database connection."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "tables" in data

    def test_docs_available(self):
        """Swagger docs should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_query_requires_body(self):
        """POST /query without body should return 422."""
        response = client.post("/query")
        assert response.status_code == 422

    def test_query_requires_question(self):
        """POST /query with empty question should return 422."""
        response = client.post("/query", json={"question": ""})
        assert response.status_code == 422

    def test_query_too_short(self):
        """POST /query with question shorter than 3 chars should fail."""
        response = client.post("/query", json={"question": "hi"})
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════
# SQL Safety Tests (no LLM needed)
# ═══════════════════════════════════════════════════════════════

class TestSQLSafety:
    """Test the SQL safety validator."""

    def test_valid_select(self):
        """Simple SELECT should be allowed."""
        is_safe, msg = validate_sql("SELECT * FROM employees")
        assert is_safe is True
        assert msg == ""

    def test_valid_select_with_join(self):
        """SELECT with JOIN should be allowed."""
        sql = """
        SELECT e.name, d.name
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        """
        is_safe, msg = validate_sql(sql)
        assert is_safe is True

    def test_valid_cte(self):
        """WITH (CTE) followed by SELECT should be allowed."""
        sql = "WITH dept_avg AS (SELECT department_id, AVG(salary) as avg_sal FROM employees GROUP BY department_id) SELECT * FROM dept_avg"
        is_safe, msg = validate_sql(sql)
        assert is_safe is True

    def test_block_drop(self):
        """DROP TABLE should be blocked."""
        is_safe, msg = validate_sql("DROP TABLE employees")
        assert is_safe is False
        assert "destructive" in msg.lower() or "Unsafe" in msg

    def test_block_delete(self):
        """DELETE should be blocked."""
        is_safe, msg = validate_sql("DELETE FROM employees WHERE id = 1")
        assert is_safe is False

    def test_block_update(self):
        """UPDATE should be blocked."""
        is_safe, msg = validate_sql("UPDATE employees SET salary = 0")
        assert is_safe is False

    def test_block_insert(self):
        """INSERT should be blocked."""
        is_safe, msg = validate_sql("INSERT INTO employees (name) VALUES ('hacker')")
        assert is_safe is False

    def test_block_alter(self):
        """ALTER should be blocked."""
        is_safe, msg = validate_sql("ALTER TABLE employees ADD COLUMN hack TEXT")
        assert is_safe is False

    def test_block_truncate(self):
        """TRUNCATE should be blocked."""
        is_safe, msg = validate_sql("TRUNCATE TABLE employees")
        assert is_safe is False

    def test_block_multiple_statements(self):
        """Multiple statements should be blocked."""
        is_safe, msg = validate_sql("SELECT 1; DROP TABLE employees")
        assert is_safe is False

    def test_empty_query(self):
        """Empty query should be blocked."""
        is_safe, msg = validate_sql("")
        assert is_safe is False

    def test_comment_only_query(self):
        """Query with only comments should be blocked."""
        is_safe, msg = validate_sql("-- just a comment")
        assert is_safe is False

    def test_block_comment_obfuscation(self):
        """Destructive SQL hidden in comments should still be caught after stripping."""
        # The dangerous part is after the comment
        sql = "/* innocent */ DROP TABLE employees"
        is_safe, msg = validate_sql(sql)
        assert is_safe is False


# ═══════════════════════════════════════════════════════════════
# Database Tests
# ═══════════════════════════════════════════════════════════════

class TestDatabase:
    """Test database initialization and queries."""

    def test_schema_info_not_empty(self):
        """Schema introspection should return content."""
        schema = get_schema_info()
        assert len(schema) > 0
        assert "departments" in schema
        assert "employees" in schema
        assert "projects" in schema

    def test_row_counts(self):
        """All tables should have seed data."""
        counts = get_row_counts()
        assert counts["departments"] >= 5
        assert counts["employees"] >= 20
        assert counts["projects"] >= 20

    def test_execute_simple_query(self):
        """Direct SQL execution should work."""
        results = execute_query("SELECT COUNT(*) as cnt FROM departments")
        assert len(results) == 1
        assert results[0]["cnt"] >= 5

    def test_execute_join_query(self):
        """JOIN queries should work correctly."""
        results = execute_query(
            "SELECT e.name, d.name as dept FROM employees e "
            "JOIN departments d ON e.department_id = d.id LIMIT 5"
        )
        assert len(results) == 5
        assert "name" in results[0]
        assert "dept" in results[0]


# ═══════════════════════════════════════════════════════════════
# Formatter Tests
# ═══════════════════════════════════════════════════════════════

class TestFormatter:
    """Test response formatting."""

    def test_format_success_response(self):
        """Success response should have all required fields."""
        result = format_response(
            question="How many departments?",
            generated_sql="SELECT COUNT(*) FROM departments",
            explanation="Counts all departments.",
            results=[{"count": 5}],
            execution_time="0.123s",
            follow_up_questions=["Which department is largest?"],
        )
        assert result["success"] is True
        assert result["question"] == "How many departments?"
        assert result["generated_sql"] == "SELECT COUNT(*) FROM departments"
        assert result["explanation"] == "Counts all departments."
        assert result["row_count"] == 1
        assert result["execution_time"] == "0.123s"
        assert "follow_up_questions" in result

    def test_format_error_response(self):
        """Error response should have required fields."""
        result = format_error(
            question="bad query",
            error_message="Something broke",
            generated_sql="INVALID SQL",
        )
        assert result["success"] is False
        assert result["error"] == "Something broke"
        assert result["generated_sql"] == "INVALID SQL"

    def test_format_ambiguity_response(self):
        """Ambiguity response should have suggestions."""
        result = format_ambiguity(
            question="Show data",
            suggestions=["Show all employees", "Show all departments"],
            reason="Too vague",
        )
        assert result["success"] is False
        assert "suggestions" in result
        assert len(result["suggestions"]) == 2
        assert result["reason"] == "Too vague"


# ═══════════════════════════════════════════════════════════════
# Integration Tests (require LLM API key)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestIntegration:
    """
    End-to-end tests that call the actual LLM.

    Run with: pytest -m integration
    Requires GEMINI_API_KEY in .env
    """

    def test_employee_count_query(self):
        """Should handle 'How many employees in Engineering?'"""
        response = client.post(
            "/query",
            json={"question": "How many employees are in the Engineering department?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["generated_sql"] is not None
        assert data["row_count"] >= 1

    def test_overdue_projects(self):
        """Should handle overdue projects query."""
        response = client.post(
            "/query",
            json={"question": "List all projects that are overdue."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_highest_avg_salary(self):
        """Should handle highest average salary query."""
        response = client.post(
            "/query",
            json={"question": "Which department has the highest average salary?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["row_count"] >= 1

    def test_employees_hired_after(self):
        """Should handle date-filtered query."""
        response = client.post(
            "/query",
            json={"question": "Show employees hired after January 2023."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_conversation_memory(self):
        """Multi-turn conversation should maintain context."""
        headers = {"X-Session-Id": "test-memory-session"}

        # First turn
        r1 = client.post(
            "/query",
            json={"question": "Show all Engineering employees."},
            headers=headers,
        )
        assert r1.status_code == 200

        # Follow-up
        r2 = client.post(
            "/query",
            json={"question": "Now show only those hired after 2023."},
            headers=headers,
        )
        assert r2.status_code == 200
        data = r2.json()
        assert data["success"] is True
