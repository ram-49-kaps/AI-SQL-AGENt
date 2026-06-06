#  AI SQL Agent — Natural Language to SQL

An AI-powered database assistant that converts plain English questions into SQL queries, executes them against a real database, and returns clean, structured results.

Built as a production-quality FastAPI application with safety guardrails, error recovery, and conversation memory.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?logo=sqlite)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-f55036?logo=groq)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red?logo=streamlit)

---

##  Features

| Feature | Description |
|---------|-------------|
| ️ **Natural Language Queries** | Ask questions in plain English — get SQL results |
|  **SQL Safety Validation** | Blocks destructive queries (DROP, DELETE, UPDATE, etc.) |
|  **Auto-Retry on Failure** | If SQL fails, the AI regenerates a corrected query |
|  **Conversation Memory** | Multi-turn conversations — the agent remembers context |
|  **SQL Explanation** | Every query comes with a plain English explanation |
|  **Ambiguity Detection** | Vague questions get clarification suggestions |
|  **Follow-up Questions** | Get contextual suggestions for deeper analysis |
| ⏱️ **Execution Metrics** | Response includes execution time and row count |
|  **Interactive API Docs** | Swagger UI built-in at `/docs` |
|  **Streamlit Web UI** | Premium dark-themed chat interface |

---

## ️ Architecture

```
User Question (POST /query)
        │
        ▼
┌─────────────────┐
│  routes/query.py │  ← FastAPI endpoint + Pydantic validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    agent.py      │  ← Orchestrator: chains all steps together
└────────┬────────┘
         │
    ┌────┴────────────────────────────┐
    │                                  │
    ▼                                  ▼
┌──────────┐  ambiguous?   ┌──────────────────┐
│ LLM:     │──── yes ────▶│ Return           │
│ Ambiguity│               │ suggestions      │
│ Check    │               └──────────────────┘
└────┬─────┘
     │ no
     ▼
┌──────────┐               ┌──────────────────┐
│ LLM:     │──────────────▶│ safety.py        │
│ Generate │  SQL query     │ Validate SQL     │
│ SQL      │               └────────┬─────────┘
└──────────┘                        │
                              safe? │
                         ┌──────────┴──────────┐
                         │ yes                  │ no
                         ▼                      ▼
                  ┌──────────┐          ┌──────────────┐
                  │database.py│          │ Return safety│
                  │Execute SQL│          │ error        │
                  └─────┬────┘          └──────────────┘
                        │
                   success?
              ┌─────────┴─────────┐
              │ yes                │ no
              ▼                    ▼
       ┌───────────┐        ┌──────────┐
       │ LLM:      │        │ LLM:     │
       │ Explain + │        │ Retry    │
       │ Follow-ups│        │ SQL      │
       └─────┬─────┘        └────┬─────┘
             │                    │
             ▼                    ▼
       ┌───────────┐        (re-validate & execute)
       │formatter.py│
       │Format JSON │
       └───────────┘
```

### Project Structure

```
ai-sql-agent/
├── app/
│   ├── main.py          # FastAPI app initialization
│   ├── agent.py         # Core orchestrator + conversation memory
│   ├── llm_service.py   # Google Gemini API wrapper
│   ├── database.py      # SQLAlchemy engine + query execution
│   ├── safety.py        # SQL validation guardrails
│   ├── prompts.py       # All LLM prompt templates
│   ├── formatter.py     # Response formatting
│   └── routes/
│       └── query.py     # POST /query endpoint
├── data/
│   ├── schema.sql       # Database DDL
│   └── seed.sql         # Realistic dummy data
├── models/
│   ├── department.py    # Department ORM model
│   ├── employee.py      # Employee ORM model
│   └── project.py       # Project ORM model
├── tests/
│   └── test_queries.py  # Unit + integration tests
├── .streamlit/
│   └── config.toml      # Streamlit theme config
├── streamlit_app.py     # Streamlit web UI
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
├── run.py               # Server entry point
└── README.md
```

---

##  Setup Instructions

### Prerequisites

- Python 3.11 or higher
- A [Groq API key](https://console.groq.com/keys) (free tier works)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-sql-agent.git
cd ai-sql-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=your_actual_api_key_here
```

### 5. Run the API Server

```bash
python run.py
```

The database is automatically created and seeded on first startup. No manual setup needed.

The API will be available at: **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

### 6. Run the Streamlit UI (Optional)

In a **separate terminal**:

```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

The web UI will open at: **http://localhost:8501**

> **Note:** The FastAPI backend must be running (`python run.py`) for the Streamlit UI to work.

---

##  Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key | *required* |
| `DATABASE_URL` | SQLite database path | `sqlite:///data/company.db` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

---

## ️ Database Schema

The database contains three related tables with realistic company data:

- **departments** (5 rows) — Engineering, HR, Marketing, Finance, Sales
- **employees** (25 rows) — Realistic names, salaries ($45k–$160k), hire dates (2018–2024)
- **projects** (22 rows) — Active, Completed, Delayed, and Pending projects

```
departments ──┐
              │ 1:N
employees ────┤
              │ 1:N
projects ─────┘
```

The database is **auto-initialized** on server startup. To reset, simply delete `data/company.db` and restart.

---

##  API Usage

### Endpoint

```
POST /query
Content-Type: application/json
```

### Request

```json
{
  "question": "How many employees are in the Engineering department?"
}
```

### Multi-Turn Conversation

Pass an `X-Session-Id` header to enable conversation memory:

```bash
# First question
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: my-session" \
  -d '{"question": "Show all Engineering employees."}'

# Follow-up (agent remembers context)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: my-session" \
  -d '{"question": "Now show only those hired after 2023."}'
```

---

##  Example Requests & Responses

### 1. Employee Count by Department

**Request:**
```json
{"question": "How many employees are in the Engineering department?"}
```

**Response:**
```json
{
  "success": true,
  "question": "How many employees are in the Engineering department?",
  "generated_sql": "SELECT COUNT(*) as employee_count FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = 'Engineering'",
  "explanation": "This query counts the number of employees who belong to the Engineering department by joining the employees and departments tables.",
  "execution_time": "1.234s",
  "row_count": 1,
  "result": [{"employee_count": 7}],
  "follow_up_questions": [
    "What is the average salary in the Engineering department?",
    "List all projects assigned to Engineering employees."
  ]
}
```

### 2. Overdue Projects

```json
{"question": "List all projects that are overdue."}
```

### 3. Highest Average Salary

```json
{"question": "Which department has the highest average salary?"}
```

### 4. Employees Hired After a Date

```json
{"question": "Show employees hired after January 2023."}
```

---

## ️ Error Handling

### Destructive Query Blocked

**Request:**
```json
{"question": "Delete all employees from the database"}
```

**Response:**
```json
{
  "success": false,
  "question": "Delete all employees from the database",
  "error": "Unsafe query blocked. The query contains a destructive operation (DELETE). Only read-only SELECT queries are allowed.",
  "generated_sql": "DELETE FROM employees"
}
```

### Ambiguous Query

**Request:**
```json
{"question": "Show data"}
```

**Response:**
```json
{
  "success": false,
  "question": "Show data",
  "message": "Your request is ambiguous. Please try one of the suggested questions below.",
  "suggestions": [
    "Show all employees with their department names",
    "Show all departments and their locations",
    "Show all active projects with their deadlines"
  ]
}
```

### Invalid SQL (Auto-Retry)

If the LLM generates invalid SQL, the agent:
1. Catches the database error
2. Sends the error back to the LLM
3. Gets a corrected query
4. Retries execution

If retry also fails, a friendly error is returned.

---

##  Running Tests

```bash
# Run unit tests (no API key needed)
python -m pytest tests/ -v

# Run all tests including integration (requires API key)
python -m pytest tests/ -v -m integration
```

---

##  Future Improvements

- [ ] **Query History Dashboard** — Save and browse past queries
- [ ] **Multi-Database Support** — PostgreSQL, MySQL adapters
- [ ] **Authentication** — API key or JWT-based access control
- [ ] **Response Caching** — Cache frequent queries for performance
- [ ] **Streaming Responses** — Stream results for large datasets
- [ ] **Rate Limiting** — Prevent LLM API abuse
- [x] **Web UI** — Streamlit chat interface with premium dark theme
- [ ] **Export Results** — CSV / Excel download

---

##  License

MIT License — see [LICENSE](LICENSE) for details.
