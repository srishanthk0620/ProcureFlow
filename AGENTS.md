# PROCUREFLOW — CODEX OPERATING RULES

## 1. Task Discipline
- Work only inside explicitly supplied scope.
- Inspect required files before changing them.
- Read only files needed for the current task.
- Never redesign unrelated modules.
- Never implement roadmap features unless explicitly requested.
- Never delete files unless explicitly authorized.
- Never install dependencies unless explicitly requested.
- Prefer simple maintainable implementations.
- Prefer small targeted changes over large rewrites.
- Stop immediately after successful verification.

## 2. Quota Efficiency
- Do not repeatedly analyze the entire repository.
- Reuse project documentation before rediscovering architecture.
- Run the smallest relevant verification first.
- Do not repeatedly run full test suites for isolated changes.
- Keep reports concise.
- Stop after success.
- Do not propose extra work automatically.

## 3. Architecture
ProcureFlow uses a modular-monolith architecture.

Frontend:
- React
- Vite
- TypeScript
- installable PWA

Backend:
- FastAPI
- SQLAlchemy

Persistence:
- SQLite during demo development
- PostgreSQL-compatible design later

Rules:
- Frontend must not contain scheduling/business logic.
- Backend owns domain/business rules.
- Scheduling logic must remain isolated from API/UI code.
- Procurement workflow must use explicit domain states.
- External providers must be behind adapter/interface boundaries.
- Demo integrations must be replaceable by real providers.
- Avoid premature microservices.
- Avoid unnecessary infrastructure.

## 4. Planned Backend Domains
- auth
- farmers
- centres
- appointments
- scheduling
- procurement
- queues
- notifications
- integrations
- analytics
- demo
- core

These are architectural boundaries only.
Do not implement them unless explicitly scoped.

## 5. Product Constraints
ProcureFlow is intended to support:
- farmer-facing installable PWA
- multilingual-friendly design
- Farmer Circle / delegated farmer access
- FPO/cooperative-assisted access later
- PACS/CSC-assisted access later
- village travel cohorts
- crop + quantity based procurement requests
- procurement-centre comparison
- intelligent centre recommendation
- capacity-aware appointments
- multi-stage resource-aware scheduling
- quality/weighing/unloading stage modelling
- bottleneck detection
- resource conflict prevention
- live queue prediction
- dynamic service ETA
- leave-time guidance
- QR/token based check-in
- staff operational workspace
- admin monitoring
- equipment outage/disruption handling
- missed-slot recovery
- safe rescheduling
- simulated then real SMS/voice integrations
- offline-safe PWA behaviour
- future optional ML residual correction

Do not implement roadmap items without explicit task scope.

## 6. Scheduling Safety
The scheduling system must eventually:
- never knowingly double-allocate the same resource
- model stage/resource capacity rather than only farmer count
- allow safe parallel work across different resources
- account for processing-time uncertainty
- preserve resilience capacity where appropriate
- handle equipment/staff disruptions
- protect near-term/frozen appointments from unnecessary movement
- never confirm a booking when capacity state is uncertain
- expose an explanation for important recommendations

Scheduling logic must remain independent from UI code.

## 7. Multi-Channel Access
Future channels may include:
- PWA
- SMS
- IVR
- automated voice calls
- missed-call callback
- delegated friend/family
- FPO
- cooperative
- PACS
- CSC

All channels must call the SAME backend booking/scheduling services.

Do not duplicate scheduling logic per channel.

## 8. Offline Behaviour
Never confirm a new dynamic booking solely from stale offline state.

Offline clients may:
- read cached information
- display existing token/booking
- store a pending request

A new offline request remains pending until validated centrally.

## 9. Application Error Handling
- Never swallow exceptions silently.
- Validate inputs at API boundaries.
- Validate business constraints at service/domain boundaries.
- Prefer explicit domain errors.
- Use transactions for multi-step persistent operations.
- Prevent partial state wherever possible.
- Treat DB/network/provider failures as expected failure modes.
- Never report success when final state is uncertain.
- Never expose secrets in logs/errors.
- Use predictable conflict handling.
- Prefer fail-safe behaviour over guessing.

Future domain failures may include:
RESOURCE_CONFLICT
INVALID_CONSIGNMENT
CENTRE_UNAVAILABLE
RESOURCE_UNAVAILABLE
DELEGATION_NOT_AUTHORIZED
BOOKING_STATE_CHANGED
OFFLINE_CONFIRMATION_NOT_ALLOWED

## 10. Codex Error Handling
When a task/check fails:
1. capture concise evidence;
2. classify failure;
3. retry at most once only if cause is clearly understood, safe, non-destructive, and in-scope;
4. otherwise stop;
5. provide at most two feasible remedies.

Never:
- use --force automatically
- delete environments automatically
- change runtime versions automatically
- install unrelated dependencies
- disable tests
- comment out broken code merely to pass
- widen scope without authorization
- rewrite architecture to bypass an error

If partial changes exist, report them.

## 11. Verification Protocol
Each future task should verify:
SUCCESS PATH
+
relevant FAILURE PATH

Use targeted checks first.

If verification fails:
- diagnose before modifying;
- retry at most once when safe;
- otherwise stop.

After PASS:
- report;
- stop.

## 12. Reporting Protocol
Return only:
TASK
STATUS
FILES
CHECKS
BLOCKERS

Avoid tutorials and verbose commentary unless requested.
