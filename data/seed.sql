-- ═══════════════════════════════════════════
-- AI SQL Agent — Seed Data
-- ═══════════════════════════════════════════
-- Realistic dummy data for demo and testing.

-- ───────────────────────────────────────────
-- Departments (5 rows)
-- ───────────────────────────────────────────
INSERT OR IGNORE INTO departments (id, name, location) VALUES
    (1, 'Engineering',  'San Francisco, CA'),
    (2, 'HR',           'New York, NY'),
    (3, 'Marketing',    'Chicago, IL'),
    (4, 'Finance',      'Boston, MA'),
    (5, 'Sales',        'Austin, TX');

-- ───────────────────────────────────────────
-- Employees (25 rows)
-- ───────────────────────────────────────────
INSERT OR IGNORE INTO employees (id, name, department_id, salary, hire_date) VALUES
    -- Engineering (7 employees)
    (1,  'Alice Johnson',       1, 135000.00, '2020-03-15'),
    (2,  'Bob Smith',           1, 128000.00, '2021-06-01'),
    (3,  'Charlie Brown',       1, 142000.00, '2019-11-20'),
    (4,  'Diana Ross',          1, 115000.00, '2023-01-10'),
    (5,  'Ethan Hunt',          1, 155000.00, '2018-07-22'),
    (6,  'Fiona Green',         1, 98000.00,  '2024-02-14'),
    (7,  'George Lee',          1, 110000.00, '2023-08-05'),

    -- HR (4 employees)
    (8,  'Hannah White',        2, 82000.00,  '2020-09-01'),
    (9,  'Ian Black',           2, 75000.00,  '2022-04-18'),
    (10, 'Julia Chen',          2, 88000.00,  '2019-12-03'),
    (11, 'Kevin Park',          2, 71000.00,  '2024-06-15'),

    -- Marketing (5 employees)
    (12, 'Laura Martinez',      3, 92000.00,  '2021-02-28'),
    (13, 'Michael Davis',       3, 87000.00,  '2020-10-12'),
    (14, 'Nina Patel',          3, 95000.00,  '2022-07-30'),
    (15, 'Oscar Wilson',        3, 78000.00,  '2023-03-22'),
    (16, 'Patricia Kim',        3, 84000.00,  '2024-01-08'),

    -- Finance (5 employees)
    (17, 'Quentin Adams',       4, 105000.00, '2019-05-14'),
    (18, 'Rachel Turner',       4, 112000.00, '2021-08-19'),
    (19, 'Samuel Wright',       4, 98000.00,  '2022-11-25'),
    (20, 'Tina Brooks',         4, 125000.00, '2020-01-07'),
    (21, 'Uma Sharma',          4, 91000.00,  '2023-09-12'),

    -- Sales (4 employees)
    (22, 'Victor Nguyen',       5, 72000.00,  '2021-04-05'),
    (23, 'Wendy Taylor',        5, 68000.00,  '2023-06-17'),
    (24, 'Xavier Lopez',        5, 85000.00,  '2020-08-30'),
    (25, 'Yara Ahmed',          5, 79000.00,  '2024-03-01');

-- ───────────────────────────────────────────
-- Projects (22 rows)
-- ───────────────────────────────────────────
INSERT OR IGNORE INTO projects (id, name, employee_id, status, deadline) VALUES
    -- Engineering projects
    (1,  'Cloud Migration',             1,  'Active',       '2026-12-31'),
    (2,  'API Gateway v2',              2,  'Active',       '2026-09-15'),
    (3,  'ML Pipeline Optimization',    3,  'Completed',    '2025-03-01'),
    (4,  'Mobile App Redesign',         4,  'Delayed',      '2026-05-30'),
    (5,  'Infrastructure Automation',   5,  'Active',       '2027-03-15'),
    (6,  'Security Audit Tool',         6,  'Pending',      '2027-06-01'),
    (7,  'Data Lake Architecture',      7,  'Active',       '2026-11-30'),

    -- HR projects
    (8,  'Employee Onboarding Portal',  8,  'Active',       '2026-10-15'),
    (9,  'Performance Review System',   9,  'Delayed',      '2026-04-30'),
    (10, 'Diversity Initiative',        10, 'Completed',    '2025-02-28'),

    -- Marketing projects
    (11, 'Brand Refresh Campaign',      12, 'Active',       '2026-08-31'),
    (12, 'SEO Optimization',            13, 'Completed',    '2025-01-15'),
    (13, 'Social Media Analytics',      14, 'Active',       '2026-12-01'),
    (14, 'Content Strategy 2025',       15, 'Pending',      '2026-11-30'),
    (15, 'Customer Journey Mapping',    16, 'Delayed',      '2026-05-15'),

    -- Finance projects
    (16, 'Budget Forecasting Tool',     17, 'Active',       '2026-09-30'),
    (17, 'Expense Automation',          18, 'Completed',    '2025-06-15'),
    (18, 'Quarterly Audit Dashboard',   19, 'Active',       '2026-11-01'),
    (19, 'Revenue Analytics Platform',  20, 'Delayed',      '2026-03-31'),

    -- Sales projects
    (20, 'CRM Integration',             22, 'Active',       '2026-10-31'),
    (21, 'Lead Scoring Model',          23, 'Pending',      '2027-02-28'),
    (22, 'Sales Pipeline Dashboard',    24, 'Active',       '2026-07-15');
