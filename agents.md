# Agent guidelines: REST API with FastAPI

Patterns and conventions for developing and modifying this FastAPI REST API.

---

## 1. Project layout

- **`app/api/routes/`** — HTTP layer only. Route handlers, request/response mapping, `Depends()` for DB and auth. No business logic.
- **`app/schemas/`** — Pydantic models for request/response (and query params when shared). Use for validation and OpenAPI.
- **`app/services/`** — Business logic, orchestration, calls to DB. No FastAPI imports.
- **`app/models/`** — SQLAlchemy ORM models (DB shape).
- **`app/db/`** — Database connection, session factory, `get_db` dependency.
- **`app/exceptions.py`** — Custom exceptions that map to HTTP status codes; registered in `main.py`.

Keep routes thin: parse input → call service → map to response. Do not put business rules in route handlers.

---

## 2. Routes (API layer)

- Use **`APIRouter()`** per resource; mount with `app.include_router(router, tags=[...])` in `main.py`.
- Prefer **path parameters** for resource identity: `/appointments/{appointment_ulid}`, `/medspas/{medspa_ulid}/appointments`.
- Use **query parameters** for list filters and pagination: `?medspa_ulid=...&status=...`.
- Declare **`response_model`** on every route so OpenAPI and serialization are correct.
- Set **`status_code=201`** for `POST` that create a resource.
- Use **`Depends(get_db)`** for DB session; pass the session into services, do not create engines or sessions inside routes.
- Resolve external IDs (e.g. ULID) to internal IDs (e.g. DB id) in the route or a small helper, then pass to the service.

Example pattern:

```python
@router.post("/medspas/{medspa_ulid}/appointments", response_model=AppointmentResponse, status_code=201)
def create_appointment(medspa_ulid: str, data: AppointmentCreate, db: Session = Depends(get_db)):
    medspa = MedspaService.get_medspa_by_ulid(db, medspa_ulid)
    appointment = AppointmentService.create_appointment(db, medspa.id, data)
    return _to_response(appointment)
```

---

## 3. Schemas (Pydantic)

- **Request bodies**: one schema per create/update (e.g. `AppointmentCreate`, `AppointmentStatusUpdate`).
- **Responses**: one schema per resource shape (e.g. `AppointmentResponse`). Use `model_validate()` or explicit constructors to build from ORM/dicts.
- Use **`Field(..., description="...")`** for important fields so OpenAPI stays clear.
- For enums (e.g. status), define a Pydantic/StrEnum in schemas and use it in both request and response schemas.
- Do not expose internal IDs if the API is keyed by ULID; expose `ulid` (or whatever the public identifier is) and keep `id` internal if needed for joins.

---

## 4. Services (business logic)

- Services are **plain Python**. No `fastapi`, `APIRouter`, or request/response types.
- They receive **`db: Session`** (and optionally other dependencies) and perform reads/writes.
- They **raise** `NotFoundError`, `BadRequestError`, or other `AppException` subclasses when the operation is invalid or the resource is missing; the route layer does not catch these (the global handler in `main.py` does).
- Return **ORM instances or simple structs**; the route layer maps them to response schemas.
- Keep services focused: one main entity per service module; orchestration across entities is fine inside a service.

---

## 5. Exceptions and HTTP status

- Use **`AppException`** and subclasses in `app/exceptions.py` for known API errors.
- **`NotFoundError`** → 404 (e.g. medspa or appointment not found by ULID).
- **`BadRequestError`** → 400 (e.g. invalid payload or business rule violation).
- Add other subclasses (e.g. `ConflictError` → 409) as needed; set `status_code` and `detail` and register in `main.py` with `@app.exception_handler`.
- In routes and services, **raise** these exceptions; do not return error response objects from handlers for these cases.
- Let FastAPI and the exception handler produce the final JSON (e.g. `{"detail": "..."}`).

---

## 6. Database and dependencies

- Use **one `get_db`** generator that yields a `Session` and ensures `session.close()` (and optionally rollback on exception).
- Inject the session with **`db: Session = Depends(get_db)`** in route handlers and pass it to services.
- Do not open sessions or engines inside services; keep session lifecycle in the dependency.
- Prefer **read-only operations** where possible (no commit when only reading).

---

## 7. Naming and REST conventions

- **URLs**: plural nouns for collections (`/appointments`, `/medspas`, `/services`). Nested resources: `/medspas/{medspa_ulid}/appointments`.
- **Methods**: `GET` (read), `POST` (create), `PATCH` (partial update), `PUT` (full replace, if used), `DELETE` (delete).
- **IDs in paths**: use the **public identifier** (e.g. ULID) in URLs; resolve to internal id in the app.
- **Consistent response shape**: single resource → one object; list → array of the same response schema. Use the same `response_model` for list and get-by-id when the shape is the same.

---

## 8. Adding a new resource

1. **Models**: add SQLAlchemy model in `app/models/` if a new table.
2. **Schemas**: add create/update and response schemas in `app/schemas/`.
3. **Service**: add a module in `app/services/` with functions that take `db` and raise `AppException` subclasses.
4. **Routes**: add a new router in `app/api/routes/`; mount it in `main.py` with a tag.
5. **Exceptions**: extend `app/exceptions.py` only when you need a new HTTP status type; reuse `NotFoundError`/`BadRequestError` when they fit.

---

## 9. Testing

- **Integration tests**: hit the FastAPI app (e.g. `TestClient`), use a test DB or fixtures. Test status codes, response shape, and key fields.
- **Unit tests**: test services with a mocked or in-memory DB/session; no HTTP.
- Prefer **realistic payloads and paths** (e.g. real ULIDs and schema-valid bodies) in integration tests so that validation and serialization are exercised.

---

## 10. Security and validation

- Validate input with **Pydantic schemas** for body and (where useful) query params. Use `Query()` for optional/filter params.
- Do not trust path parameters: **resolve ULIDs to entities** and raise `NotFoundError` when not found.
- Keep **passwords and secrets** out of code and logs; use config/env and inject where needed.
- Add auth dependencies (e.g. `Depends(require_user)`) to protected routes when you add authentication; leave routes without auth only for public endpoints.

---

## Summary

| Layer      | Responsibility |
|-----------|-----------------|
| **Routes** | HTTP, dependency injection, map request → service call → response schema, no business logic |
| **Schemas** | Request/response validation and OpenAPI shape |
| **Services** | Business logic, DB access, raise `AppException` subclasses |
| **Models** | ORM and DB schema |
| **Exceptions** | Consistent HTTP error responses via `AppException` and handlers in `main.py` |

Stick to these boundaries so the API stays consistent, testable, and easy to extend.
