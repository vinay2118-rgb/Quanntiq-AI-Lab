# QAL-IMP-003 — Dependency Injection Container Implementation Specification

Status: Contract approved and locked for implementation. Approval and freeze require every acceptance gate to pass on the mandatory Python 3.14 and Docker toolchain.

## Contract

The Dependency Injection Container is the kernel-owned composition mechanism for explicit dependency registration and deterministic singleton resolution. It hardens the existing `Container` interface without redesigning the approved Platform Kernel or introducing hidden global state.

## Runtime boundaries

- Preserve `Container`, `register_instance()`, `register_factory()`, and `resolve()`.
- Support explicit singleton instances and thread-safe lazy singleton factories.
- Detect circular dependency graphs and raise a dedicated kernel error.
- Reject factory results that do not satisfy the registered contract.
- Do not cache failed or invalid factory resolutions.
- Provide `is_registered()` and deterministic registered-contract introspection.
- Preserve duplicate-registration and missing-dependency behavior.
- Keep container creation and ownership inside `build_kernel()`.
- Exclude scoped and transient lifetimes, automatic constructor injection, decorators, third-party DI frameworks, and service-locator globals.
- Preserve all approved QAL-IMP-001 and QAL-IMP-002 behavior.

## Operational guarantees

Factory-backed dependencies are created at most once after successful resolution, including under concurrent access. Nested resolution remains deterministic. Circular graphs fail explicitly instead of deadlocking or recursing indefinitely. Factory exceptions propagate without poisoning the container, allowing a later resolution attempt. Invalid factory results are rejected and never cached. Registration metadata is stable and does not expose mutable internal state.

## Acceptance gates

1. Existing instance and lazy singleton factory interfaces remain compatible.
2. Concurrent factory resolution creates exactly one successful singleton instance.
3. Nested acyclic dependency resolution succeeds deterministically.
4. Direct and indirect circular dependencies raise the dedicated circular-dependency error.
5. Factory exceptions propagate, are not cached, and allow a later retry.
6. Factory results that violate the registered contract are rejected and not cached.
7. Duplicate and missing-dependency behavior remains unchanged.
8. `is_registered()` and registered-contract introspection are deterministic.
9. Existing QAL-IMP-001 and QAL-IMP-002 tests remain green.
10. Ruff, strict mypy, and tests pass with at least 90% package coverage.
11. Docker and PostgreSQL-backed kernel runtime checks remain compatible.
12. No scoped/transient lifetime, automatic injection, global locator, or third-party DI framework is introduced.