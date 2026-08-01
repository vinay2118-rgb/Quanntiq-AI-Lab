# QAL-IMP-002 - Configuration Manager Implementation Specification

Status: Contract approved and locked for implementation. Approval and freeze require every acceptance gate to pass on the mandatory Python 3.14 and Docker toolchain.

## Contract

The Configuration Manager is the platform's single immutable and validated configuration authority. It preserves the existing `Settings` and `get_settings()` interfaces while providing deterministic environment loading, deployment-profile validation, and secret-safe diagnostics.

## Runtime boundaries

- `config.py`: validated `QAL_` configuration and process-wide cached access.
- Supported profiles: development, testing, staging, and production.
- Explicit initialization values override environment-provided values.
- Staging and production reject placeholder database credentials.
- Configuration diagnostics and representations must redact credentials.
- `.env.example` contains non-sensitive example values only.
- `compose.yaml` receives credentials through external environment values.
- No hot reload, remote configuration service, administration UI, or business-domain behavior is included.

## Operational guarantees

Configuration is immutable after creation. Invalid values fail during startup. Port numbers, environment names, log levels, and database URLs are validated. Staging and production cannot start with placeholder database credentials such as `change-me`. The cached configuration entry point returns one process-wide instance. Existing QAL-IMP-001 API, kernel, lifecycle, database, health, and metrics behavior remains compatible.

## Acceptance gates

1. Valid configuration loads from defaults and `QAL_` environment variables.
2. Explicit initialization values override environment values deterministically.
3. Invalid ports, environments, log levels, and database URLs fail at startup.
4. Staging and production reject placeholder database credentials.
5. Approved diagnostics and object representations do not expose credentials.
6. Configuration remains immutable and process-cached.
7. Existing QAL-IMP-001 tests remain green.
8. Ruff, strict mypy, and tests pass with at least 90% package coverage.
9. Compose validation and PostgreSQL-backed runtime checks pass.
10. Tracked configuration contains no deployable secrets.
