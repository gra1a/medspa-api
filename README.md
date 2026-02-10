# MedSpa Platform API

REST API for medspa locations, services, and appointments. Built with FastAPI, SQLAlchemy, and PostgreSQL.

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

- With Docker: `docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit`
- Locally (with DB and env as in `.env.test`): `./run_tests.sh` or `pytest`

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
  -d '{"start_time":"2026-03-01T14:00:00Z","service_ulids":["01ARZ3NDEKTSV4RRFFQ69G5FB1","01ARZ3NDEKTSV4RRFFQ69G5FB2"]}'
```

**Get one appointment**

```bash
curl -s http://localhost:8000/appointments/<appointment_ulid>
```

**List appointments** (optional filters: `medspa_ulid`, `status`)

```bash
curl -s "http://localhost:8000/appointments?medspa_ulid=01ARZ3NDEKTSV4RRFFQ69G5FAV&status=scheduled"
```

**Update appointment status** (`scheduled` | `completed` | `canceled` per spec)

```bash
curl -s -X PATCH http://localhost:8000/appointments/<appointment_ulid> \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

Interactive API docs: **http://localhost:8000/docs** (Swagger), **http://localhost:8000/redoc** (ReDoc).

---

## AI usage

- **Cursor / IDE**: Used for code navigation, reading routes/schemas/services, and editing the README.
- **No AI-generated business logic**: Core app logic (appointments, services, medspas) was implemented manually; AI was used only to draft this README and to double-check curl examples against the codebase.

---

## Assumptions

- **ULIDs** for public identifiers: stable, URL-safe, and sortable; internal IDs remain integer PKs.
- **Single tenant by design**: No auth or tenant isolation in this scope; the API is “open” for the exercise.
- **Price in cents**: Per spec, `price` (services) and `total_price` (appointments) are stored in cents (integer).
- **Medspa field names**: Spec uses `phone_number`; schema and API use `phone_number` accordingly.
- **Appointment status**: Spec values `scheduled`, `completed`, `canceled` (US spelling); no extra statuses.
- **Appointment semantics**: One appointment = one medspa, one start time, one or more services; `total_price` and `total_duration` are stored at creation for historical accuracy.
- **Timezone**: `start_time` is stored in UTC; naive datetimes in requests are treated as UTC for “no past” validation.
- **Postgres**: Target DB is PostgreSQL; schema uses `SERIAL`, `TIMESTAMPTZ`, and `NUMERIC(10,2)`.
- **No soft deletes**: Deletes are hard (e.g. cascade from medspa); no “archived” or “deleted_at” in scope.

---

## Tradeoffs

- **ULID vs UUID**: Chose ULID for time-sortable, compact public IDs; no dependency on UUID extension in Postgres.
- **Stored totals on appointments**: Redundant with summing services, but preserves history if service prices change later; avoids recomputation and keeps reads simple. Totals are in cents to match service prices.
- **No auth in scope**: Keeps the exercise focused on data model and CRUD; real product would add auth and tenant scoping.
- **Sync SQLAlchemy**: Simpler for a small API; async could be added later for higher concurrency.
- **Global exception handler**: Custom `AppException` returns consistent `{"detail": "..."}` and status codes (e.g. 404) without repeating logic in every route.

---

## Scope decisions

- **Out of scope (and why)**  
  - **Authentication / authorization**: Not in requirements; would be a separate pass (e.g. API keys or JWT + tenant ID).  
  - **Pagination**: List endpoints return all matching rows; acceptable for a small dataset; would add `limit`/`offset` or cursor pagination for production.  
  - **Filtering beyond current params**: Appointment list supports only `medspa_ulid` and `status`; no date range or search by customer.  
  - **Customer / user entity**: Appointments are not tied to a “customer”; adding it would imply schema and API changes.  
  - **Idempotency**: No idempotency keys on POST/PATCH; could be added for safe retries.  
  - **Rate limiting / caching**: Not implemented.  
  - **Running migrations**: Schema is a single SQL file applied at startup (Docker) or manually; no migration versioning (e.g. Alembic) in this scope.

---

## Scope change response

*(If your assignment included a specific PM scenario question, paste it here and replace this paragraph with your answer.)*

**Generic response to a PM scope change (e.g. “We need to support customers and link them to appointments”):**

1. **Clarify** – Confirm whether “customers” are required for every appointment or optional (e.g. walk-ins). Ask if we need customer-facing fields (name, email, phone) and any privacy/consent requirements.
2. **Impact** – New `customers` table (or `users` with a type); `appointments` gets optional `customer_id` FK; API: create/update customer, optional `customer_id` (or nested payload) on appointment create; list appointments by `customer_id`. Adjust validation so either customer is required or we allow null for anonymous.
3. **Estimate** – Rough estimate: schema + migration (e.g. Alembic), CRUD for customers, appointment linkage and list filter, tests and docs. Suggest breaking into: (a) customer entity + CRUD, (b) link to appointments + filters.
4. **Plan** – Propose a small design (tables + one or two key endpoints), get PM sign-off, then implement in the order above and add a short note to the README under “Scope decisions” that customers are now in scope.

This keeps the change bounded and allows the PM to prioritize (e.g. “customers optional” vs “required” vs “full profile”).
