 #QAL-IMP-004 — Event Bus Implementation Specification



 ##Purpose



Harden the existing typed asynchronous in-process event bus for reliable kernel-level event delivery while preserving the approved QAL-IMP-001 through QAL-IMP-003 behavior.



 ##Scope



QAL-IMP-004 will:



- Validate event topics.

- Preserve immutable event envelopes.

- Prevent duplicate subscriptions.

- Support safe handler unsubscription.

- Execute subscribed handlers asynchronously.

- Isolate individual handler failures.

- Report delivery outcomes to the publisher.

- Preserve subscriber registration order in delivery results.

- Safely publish events with no subscribers.

- Maintain concurrency-safe subscription state.



 ##Event Contract



An event contains:



- `topic`: non-empty normalized routing identifier.

- `payload`: event-specific data.

- `event_id`: automatically generated unique identifier.

- `occurred_at`: timezone-aware UTC timestamp.



The event envelope remains immutable after creation.



 ##Delivery Contract



Publishing returns an immutable delivery report containing:



- Event identifier.

- Topic.

- Number of matched handlers.

- Number of successful deliveries.

- Details of failed deliveries.



A failing handler must not prevent other matched handlers from executing. Handler exceptions must be captured in the report and must not be raised directly from `publish()`.



 ##Subscription Contract



- A topic may have multiple handlers.

- Registering the same handler for the same topic more than once is idempotent.

- The same handler may subscribe to different topics.

- Unsubscribing an existing handler returns `True`.

- Unsubscribing a missing handler returns `False`.

- Topics with no remaining handlers are removed from internal state.

- Subscription mutations are protected against concurrent access.



 ##Validation Rules



A topic must:



- Be a string.

- Contain non-whitespace characters.

- Match the approved topic format: lowercase segments separated by periods.

- Use only lowercase letters, digits, underscores, hyphens, and periods.

- Contain no empty segments.



Invalid topics fail immediately with a dedicated event-topic validation error.



 ##Failure Isolation



Each handler invocation is evaluated independently. A delivery failure records:



- Stable handler identity.

- Exception type.

- Sanitized error message.



Failure reporting must not include traceback data or mutable exception objects.



Cancellation and process-control exceptions must not be converted into ordinary delivery failures.



 ##Boundaries



QAL-IMP-004 does not introduce:



- External message brokers.

- Persistent event storage.

- Distributed delivery.

- Automatic retries.

- Dead-letter queues.

- Topic wildcards.

- Event replay.

- Cross-process communication.

- Priority scheduling.



These capabilities require separately approved future components.



 ##Acceptance Criteria



1. Existing QAL-IMP-001 through QAL-IMP-003 tests remain green.

2. Valid events receive unique identifiers and UTC timestamps.

3. Invalid topics are rejected consistently during event creation, subscription, unsubscription, and publication.

4. Duplicate subscriptions do not cause duplicate handler execution.

5. Unsubscription behavior is deterministic and tested.

6. All matched handlers are given an execution opportunity when one fails.

7. Publishing returns an immutable and accurate delivery report.

8. Publishing without subscribers succeeds with zero delivery counts.

9. Delivery-result ordering follows subscriber registration order.

10. Event-bus tests cover validation, subscription, unsubscription, concurrency, success, failure isolation, and empty delivery.

11. Ruff passes.

12. Strict mypy passes.

13. Total package test coverage remains at least 90 percent.

14. `qal_kernel.events` maintains at least 95 percent test coverage.

15. No unrelated files are modified.