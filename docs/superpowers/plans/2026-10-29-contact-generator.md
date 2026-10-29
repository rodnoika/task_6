# Contact Generator Implementation Plan

Updated after the user's Python interface migration and 2026-10-30 frontend cleanup. The current implementation uses Python-rendered HTML throughout.

**Goal:** Deliver the SQL-only fake contact generator described in the course assignment.

**Architecture:** PostgreSQL stored procedures own all generation. FastAPI validates arguments, calls procedures with bound parameters, and renders Jinja2 HTML or JSON results.

**Tech Stack:** PostgreSQL 17, Python 3.12/FastAPI/Jinja2/psycopg 3, HTML/CSS, small JavaScript helpers, pytest, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-29-contact-generator-design.md`

## Global constraints

- No fake contact generation in Python or JavaScript.
- Shared lookup tables distinguish locales with a locale column.
- Support `en_US`, `de_DE`, and 1,000,000 addressable positions.
- Seed 1–64 characters; batch size 1–100; batch zero-based; positions one-based.
- Every contact exposes all fields in the API contract.
- Do not deploy, publish, or modify unrelated local applications.

## Backend/data engineer: SQL and API

- [x] Create `database/001_schema.sql`, `002_lookup_data.sql`, and `003_procedures.sql`; use ordered Docker initialization.
- [x] Add independently callable procedures for RNG, normal samples, sphere coordinates, lookup selection, formatted fields, person and batch.
- [x] Bundle broad static locale data with attribution; document cardinalities.
- [x] Implement parameterized procedure calls in `backend/app/main.py` with validation and HTTP 503 on connection failure.
- [x] Test input errors and database error translation in `backend/tests/`.
- [x] Document every procedure argument, algorithm, reproducibility boundary, and invocation in `docs/stored-procedures.md`.

The public SQL entry point is `CALL faker.generate_batch('en_US', '42', 0, 10, NULL)` and returns the complete API response in JSONB. The API exposes `GET /api/users`, `/api/locales`, and `/api/health`.

## Frontend designer: generator interface

- [x] Render the primary interface from `backend/app/templates/`, with styles and local helpers in `backend/app/static/`.
- [x] Implement locale/seed controls with separate draft/applied state and pagination that follows applied arguments.
- [x] Render SQL-generated contacts and expandable details, plus Python CSV export, error pages, and mobile layout.
- [x] Test applied arguments, HTML output, safe CSV, and navigation with Python acceptance tests.

`GET /?locale=en_US&seed=42&batch=0&batch_size=10` renders the SQL batch as HTML. `GET /api/users` exposes the same procedure result as JSON.

## QA engineer: acceptance and review

- [x] Write live API and direct SQL tests under `tests/` before implementation is ready.
- [x] Check deterministic repeat calls, interleaving and page partition invariance.
- [x] Check locale and seed separation, high positions, last partial batch, and invalid arguments.
- [x] Check deterministic normal and equal-area sphere samples using broad statistical tolerances.
- [x] Review lookup cardinalities, formatting variation, and required UI fields; report concrete findings in `docs/qa.md`.

## Integration owner

- [x] Supply Docker Compose, Dockerfiles, environment examples, ignore rules, and native setup instructions.
- [x] Start a real PostgreSQL instance and install backend dependencies.
- [x] Run `python -m pytest backend/tests tests` with live services configured.
- [x] Verify Python-rendered HTML, forms and navigation; inspect desktop/mobile UI.
- [x] Resolve observed failures and update README with commands and actual verification limitations.
