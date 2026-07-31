# QAL-IMP-001 — Platform Kernel Implementation Specification

Status: Implemented; validation evidence is recorded in the repository and must pass
on the mandatory Python 3.14/Docker toolchain before approval and freeze.

## Contract

The Platform Kernel is the process composition root. It owns typed environment
configuration, singleton dependency resolution, service discovery, lifecycle state,
in-process event delivery, database connectivity, structured logs, Prometheus metrics,
and liveness/readiness endpoints. It contains no business-domain behavior.

## Runtime boundaries

- `config.py`: immutable `QAL_`-prefixed configuration with startup validation.
- `di.py`: explicit singleton/factory dependency container; replacement is rejected.
- `services.py`: service descriptors and aggregate readiness.
- `lifecycle.py`: guarded startup/shutdown state machine and ordered hooks.
- `events.py`: immutable event envelopes and concurrent async subscribers.
- `database.py`: SQLAlchemy async engine, transaction boundary, and health probe.
- `kernel.py`: composition root and runtime facade.
- `api.py`: FastAPI factory, error mapping, health endpoints, and metrics export.

## Operational guarantees

Startup fails on invalid configuration or lifecycle hook failure. Readiness returns HTTP
503 unless the lifecycle is running and every registered service is healthy. Shutdown
hooks run in reverse order. Database sessions commit on success and roll back on failure.
Containers run as UID/GID 10001, read-only, without Linux capabilities or privilege
escalation. Secrets are externalized and the example password is never suitable for a
deployed environment.

## Acceptance gates

1. Python 3.14 package build succeeds.
2. Ruff and strict mypy succeed.
3. Unit and API integration suites succeed with at least 90% package coverage.
4. Docker image builds and starts as the non-root user.
5. PostgreSQL-backed readiness changes from 503 to 200 after database health.
6. Container health check and Prometheus scrape succeed.
7. No critical/high dependency or image vulnerability is accepted without review.

