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

Farmer and Staff authentication, catalog, availability, recommendations, bookings,
queue operations, disruptions and notifications are implemented. Roles come from
the database, never request payloads. Frontend integration remains a later phase.
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
eligibility and ownership. Queue actions synchronize booking/queue state in one
transaction. `active_count` means baseline availability before active incidents;
estimates subtract each distinct-unit incident once, without also decrementing
the stored baseline for that same incident.

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
No role/user header or booking owner field can grant identity. The stored login
flow also limits session permissions: Farmer OTP sessions cannot gain Staff scope
even if the account has both profiles/roles. Staff OTP sessions permit only
Staff/centre_manager operations at the currently assigned centre.

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

One `eta_service.calculate_eta` boundary calculates deterministic estimates for
recommendations, booking details, Farmer status and Staff queue responses:

- Queue minutes = ceil(relevant remaining queued quantity / 600 × 10 / resource factor).
- Processing minutes = ceil(requested quantity / 600 × 10 / resource factor).
- Disruption delay = sum of 5/15/30 minutes for active low/medium/high incidents.
- Completion minutes = reference travel + queue + processing + disruption delay.

The resource slowdown and explicit disruption delay are distinct components; each
is included once. This is not ML or live traffic. Travel uses persisted reference
minutes, not GPS. Missing travel yields a null completion ETA and no recommendation.
Unavailable resource/capacity results also have null queue/processing/completion
ETAs, never a fake finite capacity. If no time is supplied, each centre's best
feasible slot is returned; ties use time then stable centre code. Only the best
finite result is marked recommended. Resource capacity allocation still reserves
the full active booking quantity; remaining-work estimates are separate.

Development CORS is limited to configured `DEV_CORS_ORIGINS` (default localhost and
127.0.0.1 on port 5173), GET/POST/PATCH and Authorization/Content-Type headers. No wildcard
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

## Staff authentication and operational APIs (P6C)

Migration `0003` adds persistent Staff password-attempt/OTP records and a constrained
`auth_method` on sessions. Existing sessions are safely classified as Farmer OTP
sessions. Migrations `0001` and `0002` remain unchanged. Run the same explicit
`alembic upgrade head` command above; startup never migrates the developer database.

Staff authentication requires a provisioned active User, a StaffProfile with a
unique employee code and assigned centre, a stored scrypt password hash, and a
`staff` or `centre_manager` role. The development seed remains inactive with no
password: this phase introduces no public Staff registration, automatic activation,
or default credentials. Tests provision accounts only in disposable databases.

1. POST `/api/auth/staff/login` with `{identifier, password}`. `identifier` is the
   exact StaffProfile employee code. Only a correct stored hash issues a challenge.
2. POST `/api/auth/staff/otp/verify` with `{challenge_id, otp}`.
3. Use the returned bearer token. `/api/auth/me` includes user, Staff profile,
   effective session roles and `permitted_centre_ids`.

Staff challenges use the same development/test gate, secret, expiry and five-OTP-
attempt limit as Farmer challenges. Password attempts are persisted without raw
identifiers/passwords. At most five login attempts per identifier per hour and
1000 globally per hour are allowed; successful challenge resends require 60 seconds.
Unknown/incorrect credentials return the same 401. Changing the password or
disabling/removing Staff eligibility invalidates an outstanding challenge. OTPs
are single-use and cannot be exchanged across Farmer and Staff verification routes.
Production/staging remains 503 until a real delivery adapter is implemented.

Reusable `require_staff`, `require_staff_or_manager`, and `require_centre_access`
dependencies are available. Mutation services revalidate persisted session, roles
and assignment inside their transaction. District/state/super-admin roles receive
no implicit cross-centre privileges in P6C. A foreign centre returns 403.

| Method | Full path | Behavior |
| --- | --- | --- |
| POST | `/api/bookings/{booking_id}/check-in` | Staff only; `{expected_version, reason?}` uses booking version |
| GET | `/api/queue` | Assigned centre; optional `centre_id`, `date`, `stage`, `held`, `commodity`, `limit`, `offset` |
| GET | `/api/queue/{booking_id}` | Booking owner or assigned centre operator |
| PATCH | `/api/queue/{queue_id}` | `{action, expected_version, reason?}` uses queue version |
| GET | `/api/disruptions` | Assigned centre; optional centre/status and pagination |
| POST | `/api/disruptions` | Resource type, severity, note, expected recovery, optional verified centre ID |
| PATCH | `/api/disruptions/{id}/resolve` | Mark active incident resolved; repeat returns 409 |
| GET | `/api/notifications` | Recipient only; optional unread/limit/offset |
| PATCH | `/api/notifications/{id}/read` | `{read: boolean}`; recipient only, repeated setting is safe |

### Queue lifecycle and ordering

Booking creation does **not** create a physical queue entry. Staff check-in uses
the booking ID and current booking version, only on its appointment day and while
the centre is active/open. Early arrival within that day is allowed; future/past
appointments fail with 409. A unique booking relationship prevents duplicates.
The existing UUID/reference can be presented at reception; no new public Staff
booking-list or report endpoint is introduced in this phase.

Canonical stages reuse P6A values:

`booked` → check-in → `checked_in` (waiting) → `quality_inspection` → `weighing` → `completed`.

PATCH actions are lowercase `advance`, `hold`, `resume`, `complete`. `advance`
only performs waiting→quality or quality→weighing; `complete` only performs
weighing→completed. There is no invented final-processing stage. A held booking
must resume before progression/completion. Duplicate holds/resumes, stale versions,
skipped stages and all terminal mutations return 409. Cancellation remains allowed
only before check-in. Both booking and queue revisions change on operational actions.

Physical order includes nonheld, nonterminal checked-in entries, ordered by actual
check-in timestamp, appointment date/start and stable queue ID. It includes unfinished
carryover arrivals, not every future booking. Held entries have no service position;
resume restores their original check-in priority. Completed entries are excluded
from active lists by default; request `stage=completed` for persisted completion
data. Filtering/pagination never renumbers the underlying service order.

Status includes queue ID (null before check-in), checked-in flag, booking stage,
held flag, position/ahead count where meaningful, timestamps, queue/booking versions,
centre/resources and ETA. The Farmer summary contains only a display name. Pre-arrival
responses show scheduled workload estimates without claiming a physical queue position.

### Shared operational ETA

Remaining processing weight is 1 at `checked_in`, 2/3 at quality, 1/3 at weighing,
and 0 at completion. The three equal work portions are a deterministic prototype
assumption, not measured service durations. Staff stage changes therefore reduce
remaining processing. Actual queue ETA sums remaining work of preceding nonheld
entries; completion/hold/resume changes position and wait for other Farmers.

Before check-in, the estimate uses same-centre/date/slot workload, excludes the
booking itself and retains reference travel. Recommendation candidates use the
same workload function without that exclusion. After check-in travel is zero.
Held bookings have unknown queue/completion ETA; remaining processing remains
visible. Zero critical capacity makes queue/processing/completion unknown. Terminal
bookings return zero remaining ETA components. The same component sum is used
everywhere; delay is added once and no fake clock countdown is applied.

### Disruptions and notifications

Each resource incident means **one distinct unavailable unit** of its specified
type. Staff must report separate physical units as separate incidents. Replayed
active reports with the same type/note return 409; additional unit reports are
rejected once no working unit remains. Baseline counts are never mutated. `other`
incidents add delay only. Low/medium/high severities add 5/15/30 minutes independently
of the unit reduction. Recovery minutes are informational; only explicit resolution
restores capacity. This policy avoids subtracting an incident from both baseline
and effective counts. Physical asset identification is not modeled yet.

Every check-in, advance, hold, resume and completion creates one persistent recipient
notification within the mutation transaction. Medium/high disruptions notify relevant
nonterminal bookings; resolution notifies still-active bookings that received that
incident's original notice. Failed/duplicate operations generate no notifications.
Per-booking incident notices are intentional; low-severity incidents do not broadcast.
Staff inbox broadcasts/report aggregation remain deferred.

### Polling and transaction behavior

Poll status/queue every 5–10 seconds while visible, refresh immediately after writes,
and back off on errors. Queue/status responses have `updated_at`, `server_time`,
`version`, and `eta.calculated_at`; `stale=false` denotes a freshly read database
snapshot, not a promise that no change can occur after the response. Centre queue
and disruption changes contribute to status `updated_at`. Resource inventory has
no P6C mutation API. Operations responses use `Cache-Control: no-store`.

All mutations use SQLite `BEGIN IMMEDIATE`, recheck authorization/version/state,
update related records, write notifications and commit together. On any failure
everything rolls back. No WebSockets, SSE, external messaging or infrastructure
is added. Existing Farmer APIs remain scoped to Farmer ownership.

## Verification

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

Tests use migrated disposable SQLite files, not `DATABASE_URL`, and exercise
migrations, foreign keys, constraints, relationships, persistence, optimistic
conflicts, seeding and auth/error boundaries. No developer database is modified.
