# ProcureFlow Architecture

## Architecture Style
Modular monolith.

Chosen for:
- fast SIH demo development
- simple deployment
- clear module boundaries
- future extensibility

Microservices are not required for the demo.

## Frontend
React + Vite + TypeScript.

Target:
installable responsive PWA.

Role experiences:
1. Farmer
2. Centre Staff
3. Administrator

Frontend contains presentation/state logic only.
Scheduling and procurement business rules remain backend-owned.

## Backend
FastAPI.

Planned domains:
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

## Persistence
SQLAlchemy.

Demo:
SQLite.

Future:
PostgreSQL.

Avoid intentional SQLite-specific design.

## Core Dependency Direction

Frontend
    ↓
FastAPI API
    ↓
Domain / application services
    ↓
Scheduling / procurement engines
    ↓
Persistence + integration adapters

## Scheduling Boundary
The scheduling engine must be independently testable.

Future inputs may include:
- farmer
- crop
- quantity
- centre
- centre resources
- resource status
- appointments
- current queue
- historical service times
- disruptions

Future outputs may include:
- recommended centre
- appointment window
- predicted service time
- expected wait
- resource allocation
- confidence
- recommendation explanation

## External Integrations
External services must use replaceable adapters.

Examples:

NotificationService
    ├── DemoSMSAdapter
    ├── DemoVoiceAdapter
    ├── RealSMSAdapter       [later]
    └── RealVoiceAdapter     [later]

Maps/traffic providers must follow the same pattern.

## Multi-Channel Booking
PWA / IVR / assisted services must NOT implement separate
scheduling algorithms.

All channels call the same central services.

## Offline Safety
Offline mode may cache data and queue requests.

Only the server may confirm a dynamic appointment.
