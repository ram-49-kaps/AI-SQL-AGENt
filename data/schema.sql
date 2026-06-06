-- ═══════════════════════════════════════════
-- AI SQL Agent — Database Schema
-- ═══════════════════════════════════════════
-- Three related tables: departments, employees, projects
-- with proper foreign key constraints.

CREATE TABLE IF NOT EXISTS departments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    location    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    department_id   INTEGER NOT NULL,
    salary          REAL    NOT NULL,
    hire_date       TEXT    NOT NULL,  -- ISO format: YYYY-MM-DD
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    employee_id     INTEGER NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('Active', 'Completed', 'Delayed', 'Pending')),
    deadline        TEXT    NOT NULL,  -- ISO format: YYYY-MM-DD
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
