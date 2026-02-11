# MedSpa Platform API

REST API for medspa locations, services, and appointments. Built with FastAPI, SQLAlchemy, and PostgreSQL.

---

## Database Schema

**CREATE TABLE statements:** See `sql/schema.sql` for the complete PostgreSQL schema including all tables, constraints, and indexes.

---

## Setup instructions

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for DB + optional full stack)
- [Optional] PostgreSQL 15+ if running the API without Docker

### Option A: Run everything with Docker

1. Clone the repo and from the project root run:

   ```bash
   docker-compose up --build
   ```

2. API will be at **http://localhost:8000**. Postgres runs on port 5432; the `migrations` service applies `sql/schema.sql` on first run.

3. Optional: load seed data for manual testing:

   ```bash
   docker-compose exec postgres psql -U postgres -d medspa_db -f /sql/seed.sql
   ```

### Option B: Run API locally with a local or existing Postgres DB

1. Create a database (e.g. `medspa_db`) and run the schema:

   ```bash
   psql -U postgres -d medspa_db -f sql/schema.sql
   ```

2. Create a virtualenv and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Dependencies are pinned with compatible-release specifiers (`~=`); you get reproducible, compatible versions.

3. Set the database URL (optional; default is `postgresql://postgres:postgres@localhost:5432/medspa_db`):

   ```bash
   export DATABASE_URL=postgresql://user:password@host:port/dbname
   ```

4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Open **http://localhost:8000** (root redirects to `/docs`).

### Running tests

**With Docker:**

```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

**Locally** (requires a test database and environment variables in `.env.test`):

```bash
# Option 1: Using the test script
./run_tests.sh

# Option 2: Direct pytest
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest -v                    # Verbose output
pytest -k "appointment"      # Run tests matching "appointment"
```

**Example test output:**

```
==================== test session starts ====================
collected 47 items

tests/unit/repositories/test_appointment_repository.py ........ [ 17%]
tests/unit/repositories/test_medspa_repository.py .....        [ 27%]
tests/unit/repositories/test_service_repository.py .....       [ 38%]
tests/unit/test_appointment_service.py ............            [ 63%]
tests/integration/test_appointments_api.py .............       [ 91%]
tests/integration/test_services_api.py ....                    [100%]

==================== 47 passed in 2.34s =====================
```

### Running linters

Install dev dependencies (includes Ruff and Pyright), then run:

```bash
pip install -r requirements-dev.txt

# Lint (Ruff)
ruff check app tests

# Check formatting (no changes)
ruff format --check app tests

# Type check (Pyright)
pyright app tests
```

To auto-fix lint issues and format code:

```bash
ruff check app tests --fix
ruff format app tests
```

---

## API examples

Base URL: `http://localhost:8000` (or your host). All IDs in URLs are **ULIDs** (e.g. `01ARZ3NDEKTSV4RRFFQ69G5FAV`).

### Health

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

### Medspas

**List medspas**

```bash
curl -s http://localhost:8000/medspas
```

**Get one medspa**

```bash
curl -s http://localhost:8000/medspas/01ARZ3NDEKTSV4RRFFQ69G5FAV
```

**Create medspa**

```bash
curl -s -X POST http://localhost:8000/medspas \
  -H "Content-Type: application/json" \
  -d '{"name":"New MedSpa","address":"100 Test St","phone_number":"555-1234","email":"contact@example.com"}'
```

### Services

**Create service** (under a medspa; **price in cents** per spec)

```bash
curl -s -X POST http://localhost:8000/medspas/01ARZ3NDEKTSV4RRFFQ69G5FAV/services \
  -H "Content-Type: application/json" \
  -d '{"name":"Facial","description":"Standard facial","price":8500,"duration":60}'
```

**List services for a medspa**

```bash
curl -s http://localhost:8000/medspas/01ARZ3NDEKTSV4RRFFQ69G5FAV/services
```

**Get one service**

```bash
curl -s http://localhost:8000/services/01ARZ3NDEKTSV4RRFFQ69G5FB1
```

**Update service** (partial; price in cents)

```bash
curl -s -X PATCH http://localhost:8000/services/01ARZ3NDEKTSV4RRFFQ69G5FB1 \
  -H "Content-Type: application/json" \
  -d '{"price":9000,"duration":45}'
```

### Appointments

**Create appointment** (services by ULID; `start_time` must be in the future, ISO 8601)

```bash
curl -s -X POST http://localhost:8000/medspas/01ARZ3NDEKTSV4RRFFQ69G5FAV/appointments \
  -H "Content-Type: application/json" \
  -d '{"start_time":"2026-03-01T14:00:00Z","service_ids":["01ARZ3NDEKTSV4RRFFQ69G5FB1","01ARZ3NDEKTSV4RRFFQ69G5FB2"]}'
```

**Get one appointment**

```bash
curl -s http://localhost:8000/appointments/<appointment_id>
```

**List appointments** (optional filters: `medspa_id`, `status`)

```bash
curl -s "http://localhost:8000/appointments?medspa_id=01ARZ3NDEKTSV4RRFFQ69G5FAV&status=scheduled"
```

**Update appointment status** (`scheduled` | `completed` | `canceled` per spec)

```bash
curl -s -X PATCH http://localhost:8000/appointments/<appointment_id> \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

Interactive API docs: **http://localhost:8000/docs** (Swagger), **http://localhost:8000/redoc** (ReDoc).

---

## AI usage

**Tools used:** Cursor IDE, Claude

**Where AI helped:**
- **Test generation**: AI wrote most of the test boilerplate for unit and integration tests, including fixtures, mock setups, and common test patterns. I provided the test scenarios and assertions; AI handled the repetitive structure.
- **Repository layer**: Generated CRUD boilerplate for repositories (basic SELECT/INSERT/UPDATE patterns). I reviewed and adjusted for specific query logic (e.g., conflict detection, ULID resolution).
- **Route handlers**: AI scaffolded FastAPI route structure, dependency injection patterns, and response models. I refined error handling and validation logic.
- **SQL schema**: AI helped generate initial CREATE TABLE statements from my data model description. I reviewed for constraint accuracy and added indexes.
- **Code navigation**: Used AI to quickly understand existing patterns and find related code across files.

**Where I overrode or made critical decisions:**
- **Architecture and layering**: Chose the repository → service → route pattern myself based on maintainability and testability goals. AI suggested alternatives but I stayed with this separation.
- **ULID over UUID/sequential IDs**: Decided on ULIDs for sortable, URL-safe public identifiers. AI recommended UUIDs initially; I switched for time-ordering benefits.
- **Pagination style**: Chose simple offset/limit over cursor-based pagination. Evaluated tradeoffs (complexity vs performance at scale) and decided offset is sufficient for this scope.
- **Transaction boundaries**: Designed where to commit/rollback (in services vs routes). AI suggested route-level commits; I moved to service layer for better encapsulation.
- **Appointment conflict logic**: Designed the "one appointment per service per timeslot" rule and 409 conflict behavior. This was a product decision AI couldn't make.
- **Status transition rules**: Defined the state machine (scheduled → completed/canceled only) based on domain understanding.

**What I learned:**
- AI excels at boilerplate and standard patterns but needs guidance on domain-specific rules and tradeoffs.
- Effective prompting requires clear context about the existing architecture and conventions (the `AGENTS.md` file helped maintain consistency).
- Testing patterns were the biggest time saver—AI understood pytest patterns well and generated comprehensive test cases quickly.

---

## Assumptions

- **ULIDs** for identifiers: stable, URL-safe, and sortable; internal IDs.
- **Single tenant by design**: No auth or tenant isolation in this scope; the API is “open” for the exercise.
- **Price in cents**: Per spec, `price` (services) and `total_price` (appointments) are stored in cents (integer).
- **Appointment status**: Simple state machine with three states—`scheduled`, `completed`, `canceled`. Only `scheduled` may transition (to `completed` or `canceled`); `completed` and `canceled` are final. PATCH to an invalid transition returns 400.
- **Timezone**: `start_time` is stored in UTC; naive datetimes in requests are treated as UTC for “no past” validation.
- **Postgres**: Target DB is PostgreSQL; schema uses `SERIAL`, `TIMESTAMPTZ`, and `NUMERIC(10,2)`.
- **No soft deletes**: Deletes are hard (e.g. cascade from medspa); no “archived” or “deleted_at” in scope.

---

## Tradeoffs

- **One appointment per timeslot per service**: A given service can be booked in only one appointment at a time for overlapping slots; creating another appointment that would overlap for that service returns 409. Keeps availability simple; a real product might support concurrent bookings or resource pools.
- **ULID vs UUID**: Chose ULID for time-sortable, compact public IDs; no dependency on UUID extension in Postgres.
- **Stored totals on appointments**: Redundant with summing services at write time, but reads (get, list) heavily outnumber writes (create, status update). Storing totals avoids a JOIN + aggregation over services on every read and keeps appointment detail a single-row fetch; preserves history if service prices change later. Totals in cents to match service prices.
- **No auth in scope**: Keeps the exercise focused on data model and CRUD; real product would add auth and tenant scoping.
- **Sync SQLAlchemy**: Simpler for this scope. Async starts to pay off at high concurrency (e.g. hundreds of concurrent connections or thousands of req/s) where the event loop can overlap I/O; at typical medspa API volumes (tens to low hundreds of req/s) sync is sufficient and easier to reason about.
- **Global exception handler**: Custom `AppException` returns consistent `{"detail": "..."}` and status codes (e.g. 404) without repeating logic in every route.

---

## Scope decisions

- **Out of scope (and why)**  
  - **Concurrent bookings per service / resource pools**: One appointment per timeslot per service only; no double-booking of the same service in overlapping slots. Supporting multiple concurrent bookings or pool-based resources would require availability and capacity model changes.
  - **Authentication / authorization**: Not in requirements; would be a separate pass (e.g. API keys or JWT + tenant ID).
  - **Filtering beyond current params**: Appointment list supports only `medspa_id` and `status`; no date range or search by customer.  
  - **Customer / user entity**: Appointments are not tied to a “customer”; adding it would imply schema and API changes.  
  - **Idempotency**: No idempotency keys on POST/PATCH; could be added for safe retries.  
  - **Rate limiting / caching**: Not implemented.  
  - **Running migrations**: Schema is a single SQL file applied at startup (Docker) or manually; no migration versioning (e.g. Alembic) in this scope.
  - **Observability / APM**: Basic request and error logging (including request IDs and exception logging) are included; structured logging, metrics collection (Prometheus), distributed tracing (OpenTelemetry), and centralized log aggregation are not in scope for this exercise but would be required for production.

---

## Scope change response

**PM ask:** Add a `customer_notes` field to appointments so customers can leave special instructions.

**How I'd handle it**

- **Clarify**: Understand the reason for the new field and how they want to use it; get context around the problem so the implementation fits the workflow. If I don't have that end-user context, sync with the frontend team on when and how the field will be added in the UI and used in the flow. Possible questions (for stakeholders or for myself): Is this new field required? What are the security concerns with an open-ended text field? What size of notes do they expect (drives max length)? Can we use predefined notes or templates instead of or in addition to free text? Can they edit the notes? The answers define how the API is shaped—e.g. if the field is optional, we can follow the current implementation plan (nullable column, optional on create/PATCH).
- **Estimate**: Small change—one migration, one schema/serialization touch, a few tests. If we don't have migrations yet, add Alembic first (on the order of an hour), then this migration + API (another hour or two).
- **Plan**: Propose the single-column + optional request/response field; get quick sign-off; implement migration and API together; add a line under Scope decisions that `customer_notes` is in scope.

**What I'd change**

- **Schema**: Add nullable `customer_notes` (e.g. `TEXT`) to `appointments`. One column, no new tables or FKs.
- **Migrations**: Use a migration tool (e.g. Alembic) instead of hand-run SQL. One migration: add column with a default of `NULL` so existing rows stay valid and the change is non-breaking. Migrations make this easier because: (1) the change is versioned and reversible (rollback = drop column), (2) we avoid manual `ALTER TABLE` in production, and (3) dev/staging/prod stay in sync. Right now we have a single `schema.sql`; introducing Alembic is a one-time setup (e.g. `alembic init`), then this change is a single new migration file.
- **API**: Optional `customer_notes` on `POST /medspas/{id}/appointments` (create) and on `PATCH /appointments/{id}` (e.g. allow updating notes without changing status). Include in `AppointmentResponse`. No new endpoints; existing list/get already return the full appointment.
- **Validation**: Optional string; if we need a cap (e.g. 2k characters) for UX or storage, add it in the schema and Pydantic.
