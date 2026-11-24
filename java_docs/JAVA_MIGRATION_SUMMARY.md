# SCMS migration and local cleanup

## Main project

The only application checkout was moved from `java_docs/source_review` to **`C:\Users\Disha Goyal\Desktop\dishaaa\scms`**. Its local Git history, original code and Java integration moved together. No second application was created. `java_docs/source_review` no longer exists.

```text
dishaaa/
  scms/
    code/
      java-rules/     Java domain rules and internal HTTP server
      backend/        FastAPI APIs, security, ORM, jobs and rollback rules
      web_dashboard/  Existing React dashboard
      flutter_app/    Existing Flutter application
      team_webpage/   Original project webpage
      run-hybrid.ps1  Small compatibility entry point for backend-only startup
    scripts/          Main launcher, isolated demo setup and verification scripts
    .local/           Ignored logs, test XML and optional separate demo database
    Docs/             Original project documents
    journals/         Original project history
    README_JAVA.md
  java_docs/          Academic reports, guides, diagrams and API snapshot
  Scrrenshots/        Original supplied images, unchanged
```

Original proposals, journals and diagrams were retained because they are project records, not duplicate runtime applications. Installed `.venv`, node_modules and Java build outputs are local dependencies, not additional application copies.

## Implemented Java responsibilities

- Booking eligibility: suspension, ACTIVE defaulter, slot existence/status, cutoff, zero capacity, duplicate booking and daily issued-transaction limit, in the original error order.
- Cancellation eligibility and ownership decision.
- Equipment-issue checks, including confirmed booking and matching available item.
- Return-state and required-damage-report checks.
- Batch ranking using seven-day usage, recency penalty and request-time tie-breaker. Scores remain ranked before the Python adapter stores rounded decimal values.
- Internal HTTP authentication, bounded worker pool, exception responses and development-only operation/class/status diagnostics.

Java source is under `scms/code/java-rules/src/edu/tiet/scms`. It uses interfaces, records, private fields, classes, custom exceptions, inheritance and collections. It is built directly with JDK 17; it is not a Spring Boot application. No direct Java JDBC/JPA layer is claimed.

## Retained components

FastAPI still owns public routes, JWT authentication and authorization, request/response models, database sessions and writes, notifications, waitlist promotion, administrative CRUD, analytics and scheduled jobs. Java-mode services use the same ORM persistence code after the Java decision. React and Flutter retain their existing UI. Flutter gained only an optional compile-time API-base setting; its original emulator address remains the default.

The original Python rule implementations remain as explicit `SCMS_RULES_ENGINE=python` rollback paths. Java mode uses `SCMS_RULES_ENGINE=java`; there is no automatic fallback. Java service errors fail closed before affected workflow writes, with the existing source's configuration initialization behavior retained. Existing transaction boundaries and concurrency limitations are not represented as fixed by this migration.

## Added and modified files

- Added five Java source files, build.ps1 and the Java build-output ignore rule under `code/java-rules`.
- Modified `code/backend/app/services/booking.py`, `fairness_engine.py` and `transaction.py` to call Java in Java mode while keeping Python rollback implementations.
- Added `code/backend/app/services/java_rules.py`, `tests/test_java_rules.py` and `tests/live_smoke.py`.
- Added `scripts/Start-SCMS.ps1`, `init_demo.py`, `verify_launcher.py` and `verify_demo.py`; replaced the initial code/run-hybrid.ps1 with a thin main-launcher wrapper.
- Modified Flutter app_constants.dart to support `SCMS_API_BASE_URL`; retained its existing default. Flutter SDK resolution updated matcher, meta, test_api and vector_math in pubspec.lock.
- Extended .gitignore for `.local` and local verification XML outputs; added README_JAVA.md.
- Added the four requested guides and moved the generated OpenAPI inventory to `java_docs/SCMS_API_CONTRACT.json`.

## Files removed locally

The following were one-time migration/report-revision experiments that were no longer imported or used by the final application or launcher:

- `java_docs/implement_java.py` — old migration generator targeting the removed source_review location.
- `java_docs/compact_report.py`
- `java_docs/final_compact.py`
- `java_docs/simplify_report.py`
- `java_docs/restore_screenshots.py`
- `scms/verification-java.xml` and `scms/verification-python.xml` — superseded initial results; current main-folder results are under `.local`.

The source_review directory was **moved**, not deleted as an extra copy. The API snapshot was also moved, not discarded. Disposable `scms/.local/launcher-smoke.db`, `scms/.local/demo.db` used for setup verification, and temporary smoke databases were removed by their verification scripts after checks. No existing user database was deleted. Python rollback functions were deliberately retained. Original report DOCX/PDF, template and supplied screenshots were not changed.

## Compatibility and remaining work

The 51 public API paths / 57 operations keep the original methods, DTOs, status envelopes and authentication dependencies. Database model and migration files are unchanged. No data migration was performed. The Java endpoint is internal and adds no frontend API requirement.

All work is local. No commit, push, pull request, remote branch change, hard reset or Git clean was performed.

The launcher and isolated demo are verified. Production PostgreSQL, real-device mobile operation, camera scanning and every manually operated browser workflow still need verification. See TESTING_RESULTS.md for executed results and limits. The academic report remains unchanged and describes an earlier proposal; these technical guides document what is now implemented.
