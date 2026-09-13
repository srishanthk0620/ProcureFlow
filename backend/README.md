# ProcureFlow backend

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

Farmer authentication, catalog, availability, recommendations and booking APIs
are implemented. Staff authentication/queue operations and disruption APIs are
deferred. Roles come from the database, never request payloads.
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
appointments are centre-local dates/times. Booking services enforce dates, capacity,
eligibility and ownership. Queue transitions and queue-entry creation remain P6C
work. In this phase `active_count` means baseline availability before active
incidents; estimates subtract each persisted incident once. P6C must preserve this
contract rather than also decrementing the baseline for the same incident.

## Prototype authentication

`APP_ENV` must be exactly `development` or `test`, and `AUTH_OTP_SECRET` must contain
at least 32 private random characters. Generate a local value without committing it:

```powershell
$env:AUTH_OTP_SECRET = & .\.venv\Scripts\python.exe -B -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep the same secret securely configured across restarts if outstanding OTPs must
remain usable. Changing it invalidates their verification. The app still imports
without this setting, but OTP operations return 503. Production/staging OTP
operations also return 503: no SMS provider is connected, and no development OTP
is exposed outside explicit development/test mode. Do not expose development mode
publicly: possession of the response code does not establish mobile ownership.

Request a code with exactly ten ASCII mobile digits. Successful request responses
include `challenge_id`, UTC `expires_at`, `retry_after_seconds`, and a clearly named
`development_otp`. Auth responses use `Cache-Control: no-store`. OTPs are generated
server-side, stored only as secret-keyed HMAC digests, expire after five minutes,
allow five failed attempts, and are single-use. Resend invalidates the prior code.
Limits are persisted: one request per mobile per 60 seconds, five per hour, and
1000 globally per hour. 429 responses contain retry metadata and `Retry-After`.

Successful verification finds the active Farmer for that mobile or creates an
explicit development Farmer/profile with a server-assigned Farmer role. It never
activates an existing inactive user or changes existing roles. Inactive P6A seed
identities remain inactive. No Staff default password or OTP is introduced.

Bearer tokens use 256 bits of randomness, with only SHA-256 digests stored in the
database. Sessions expire after one hour by default, survive restart, are bound to
the environment, and are revoked by logout. Identity, active status, roles and
expiry are checked server-side; writes recheck after reserving the transaction.
No role/user header or booking owner field can grant identity. Full Staff login
remains deferred; the Principal/session boundary supports Staff roles and centres.

## API overview

All paths below are prefixed with `/api`:

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | Preserved liveness response |
| POST | `/auth/farmer/otp/request` | `{mobile}`; explicit dev/test only |
| POST | `/auth/farmer/otp/verify` | `{challenge_id, otp}`; token + user/profile |
| GET | `/auth/me` | Authenticated identity/profile |
| POST | `/auth/logout` | Revoke bearer token; 204 |
| GET | `/commodities` | Active persisted commodities |
| GET | `/centres` | `commodity` ID/code, `district`, `active` (default true) |
| GET | `/centres/recommendations` | `commodity`, `quantity`, `appointment_date`, optional `start_time` |
| GET | `/centres/{id}` | Centre, supported commodities, baseline resources |
| GET | `/centres/{id}/slots` | `appointment_date`, `commodity` ID/code, `quantity` (default 50) |
| GET | `/bookings` | Owner only; `active`, `history`, `status`, `group` filters |
| POST | `/bookings` | Farmer only; confirmed persisted booking, 201 |
| GET | `/bookings/{id}` | Owner only; includes centre/commodity/group/version |
| POST | `/bookings/{id}/cancel` | `{expected_version, reason?}`; owner only |

Catalog routes are public; booking routes require an active Farmer bearer session.
Missing and other-owner booking IDs return 404. Ownership query parameters cannot
expand the session's scope. Contradictory active/history filters return 400.
Schemas reject extra mutation fields such as owner, role, token and status.
Business errors use 400, unauthenticated 401, unauthorized 403, absent 404,
capacity/version/state conflicts 409, schema errors 422, and throttling 429.

## Capacity and deterministic ETA

Migration `0002` adds only OTP challenges, sessions and recurring slot policies;
`0001` is unchanged. Resource counts alone cannot express quantity-per-slot limits,
so persisted policies are essential for safe booking. The explicit development seed
adds 09:00–11:00, 11:00–13:00 and 14:00–16:00 policies, each with an illustrative
3000kg nominal limit. Existing policies and records are never overwritten.
No policy means no available slot; no capacity is silently fabricated at runtime.

Visits must be tomorrow through seven days ahead in India local time. Quantities
must be whole units from 50 to 20000. Slots are centre-local naive times. Group
bookings use the same quantity budget, with optional group name, 2–20 farmers and
contact name. Mixed commodity units at a centre fail closed against a shared policy.

Effective resource factor is the minimum working/total fraction across gate,
quality desk, weighbridge and Staff; missing or zero critical resources make it
zero. Each active incident removes one corresponding baseline resource; resolved
incidents have no effect. Policy capacity × factor gives effective slot capacity.
Load sums nonterminal booking quantity for the same centre/date/start time across
commodities. Remaining capacity is nonnegative. Cancelled **and completed** bookings
do not consume the active budget; this is a prototype active-workload budget, not
a historical daily procurement limit. Policy units must match supported commodities.

Booking creation/cancellation uses `BEGIN IMMEDIATE` before reading state, so
SQLite serializes competing allocations even across connections. No process-local
lock is relied upon. Lock contention/conflicts return 409; no confirmation is
returned until commit succeeds. Other database write dialects fail closed pending
a separate locking design. Repeated requests may create separate bookings if they
fit; clients must not silently retry uncertain POSTs (idempotency keys are deferred).

Cancellation is allowed only while `booked`, with a matching version. Checked-in,
completed and cancelled bookings return 409. Rebooking is a new POST with a new
server-generated reference. No general update or separate group API is exposed.

One `estimate_slot` service boundary calculates deterministic reference estimates:

- Queue minutes = ceil(same-slot active quantity / 600 × 10 / resource factor).
- Processing minutes = ceil(requested quantity / 600 × 10 / resource factor).
- Disruption delay = sum of 5/15/30 minutes for active low/medium/high incidents.
- Completion minutes = reference travel + queue + processing + disruption delay.

The resource slowdown and explicit disruption delay are distinct components; each
is included once. This is not ML or live traffic. Travel uses persisted reference
minutes, not GPS. Missing travel yields a null completion ETA and no recommendation.
Unavailable resource/capacity results also have null queue/processing/completion
ETAs, never a fake finite capacity. If no time is supplied, each centre's best
feasible slot is returned; ties use time then stable centre code. Only the best
finite result is marked recommended. P6C should reuse this boundary for booking ETA.

Development CORS is limited to configured `DEV_CORS_ORIGINS` (default localhost and
127.0.0.1 on port 5173), GET/POST and Authorization/Content-Type headers. No wildcard
origin is enabled; production adds no CORS middleware in this phase.

## Example integration smoke flow (after explicit migration/seed)

1. POST a development mobile to `/api/auth/farmer/otp/request`.
2. POST its challenge ID and `development_otp` to `/api/auth/farmer/otp/verify`.
3. Use the returned token as `Authorization: Bearer <token>` and check `/auth/me`.
4. GET commodities/centres, then slots for tomorrow and the desired commodity.
5. POST centre/commodity IDs, quantity, appointment date, start time and optional
   group metadata to `/bookings`. Check the returned persisted token/version.
6. Cancel using its current version, check released capacity, then optionally rebook.
7. Logout and verify that the old bearer token is rejected.

## Verification

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

Tests use migrated disposable SQLite files, not `DATABASE_URL`, and exercise
migrations, foreign keys, constraints, relationships, persistence, optimistic
conflicts, seeding and auth/error boundaries. No developer database is modified.
