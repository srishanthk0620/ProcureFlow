# ProcureFlow backend foundation

Run commands from `backend/`, using the existing virtual environment. Configuration
loads `.env` in that working directory; environment variables take precedence.
The default `DATABASE_URL` is `sqlite:///./procureflow.db`. Keep database files and
credentials out of Git. PostgreSQL configuration/driver is deferred.

## Explicit setup

```powershell
.\.venv\Scripts\python.exe -B -m alembic upgrade head
.\.venv\Scripts\python.exe -B -m app.db.seed
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Startup never creates tables, migrates or seeds. Alembic is the only schema
initialization mechanism; there is no application `create_all` path. Back up
existing data before future schema changes. Initial downgrade drops foundation
tables: use only on disposable databases, never as a routine reset.

Seeding is explicit, transactional, additive and idempotent. It is permitted only
in `development` or `test`. Seed users are inactive and have no password, mobile
number or login credential. Development centres, capacities, travel references
and price records are illustrative. Seeding is not production user provisioning.

## Boundaries

Only `GET /api/health` is exposed. Service Protocols are contracts, not business
implementations. Authorization denies access until a server-backed session
adapter exists. Roles must come from the database, never request payloads.
No secret setting is needed until a token implementation is chosen in P6B.
Passwords use versioned, salted scrypt (N=131072, r=8, p=1) with constant-time
comparison. No plaintext passwords are persisted or seeded.

Requests get separate SQLAlchemy sessions. Services must own explicit transaction
boundaries and commit before reporting success. SQLite foreign keys are enabled
on every connection. ORM version checks protect Booking and QueueEntry updates;
bulk SQL updates bypass these checks and must not implement workflow transitions.

All IDs are UUID strings (seed UUIDs are deterministic); human tokens/codes are
separate. Group metadata shares a booking's quantity. Holds live on QueueEntry,
preserving the actual workflow stage rather than replacing it with `held`.
Frontend mapping for P6E: `checkedIn` → `checked_in`, `quality` →
`quality_inspection`, `complete` → `completed`; resource `quality` →
`quality_desk`, `weighing` → `weighbridge`.

Timestamps are naive UTC in persistence and serialize with UTC offsets in reads;
appointments are centre-local dates/times. Future services must enforce permitted
dates, slot capacity, centre/commodity eligibility, actor scope, legal stage
transitions and booking/queue consistency in a transaction. Those algorithms are
deliberately absent. Resource counts represent stored availability; future
disruption logic must avoid deducting the same outage twice.

## Verification

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

Tests use migrated disposable SQLite files, not `DATABASE_URL`, and exercise
migrations, foreign keys, constraints, relationships, persistence, optimistic
conflicts, seeding and auth/error boundaries. No developer database is modified.
