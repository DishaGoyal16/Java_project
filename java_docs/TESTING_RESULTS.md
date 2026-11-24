# SCMS testing results

Verified locally on 24 November 2026 from `C:\Users\Disha Goyal\Desktop\dishaaa\scms`. This is a hybrid Java/Python application, not a full Java backend conversion.

## Completed checks

| Check | Actual result |
|---|---|
| Java build | Passed with `code/java-rules/build.ps1`; JDK 17.0.20; executable JAR produced |
| Java startup | Passed; authenticated loopback HTTP service on port 8091 |
| Backend in Java mode | **41 passed** in 42.01 seconds; includes existing tests and new Java integration tests |
| Backend in Python mode | **26 passed, 15 Java-only tests skipped** in 35.09 seconds |
| Ranking parity | 100 deterministic batches compared with the source Python formula, including empty batches, ties and no-history students |
| Error contracts | Java checks for suspension, active defaulters, missing resources, invalid cancellation/issue/return states and required damage report passed |
| Internal security and outage | Missing internal token rejected; unavailable Java service maps to 503; no silent fallback; invalid engine selection rejected |
| Public workflow | Booking → allocation → issue → return → completed booking, history and notifications passed through the public API test client |
| Real API startup | Passed with a temporary SQLite database: health, registration, login, authenticated reads and student denial on an administrator route |
| Windows launcher | Passed from main folder; Java → API → dashboard startup, health checks and owned-process shutdown |
| Live frontend proxy integration | Dashboard HTML served; real request through Vite `/api` proxy → FastAPI → Java returned the expected SLOT_NOT_FOUND error |
| Diagnostic proof | Captured `operation=booking handler=WorkflowRules.validate status=404 fallback=false` from the live Java process |
| Log privacy | Launcher retested after disabling SQL parameter echo; API output contains no INSERT parameter logging |
| Demo provisioning | Fresh setup and repeated setup passed: two staff/admin accounts, one student, four items, four slots, one fairness configuration; no duplicate rows or password output |
| React tests | **69 passed across 14 files**, using one worker to fit laptop memory |
| React build | Passed; 2,884 modules transformed. Existing large-bundle warning remains |
| TypeScript | `tsc --noEmit` passed |
| Flutter dependencies and tests | Resolved successfully on retry; **28 tests passed** on Flutter 3.47.0 / Dart 3.13.0 |
| API/schema source checks | Public routers, DTO schemas, entity models and database migration files unchanged; API snapshot contains 51 paths / 57 operations |
| Source hygiene | `git diff --check` passed; academic reports and supplied screenshots were not edited during finalization |

Backend result files are in `scms/.local/verification-java.xml` and `verification-python.xml`. The latest launcher logs are in `.local/java.out.log`, `.local/api.out.log`, `.local/api.err.log` and `.local/launcher-verification.log`. These are local ignored outputs, not remote artifacts.

## Problems encountered and resolution

- The first dashboard test launch hit a blocked native Rollup module. The subsequent normal production build succeeded. A later default parallel test run exhausted memory. Running `npm.cmd run test:run -- --maxWorkers=1 --minWorkers=1` passed all 69 tests; application source was not changed to work around the tests.
- The first Flutter package download failed with a TLS error. A later ordinary retry resolved packages and all 28 tests passed. Four transitive packages in pubspec.lock were adjusted by the installed Flutter SDK. Unrelated generated platform-file changes were restored to their original contents.
- The first live smoke completed its assertions but had a Windows process-tree cleanup problem. The test now terminates its owned process tree. The main-folder test completed successfully. A simultaneous extra smoke attempt briefly collided with its fixed port; do not run two live smoke scripts at once.
- The initial launcher allowed the existing development SQL echo setting. It was changed to production error/log settings and the full launcher verification passed again without SQL parameter output.

## Verification limits

- No existing PostgreSQL URL or production database was supplied. Real PostgreSQL connectivity, production records, PostgreSQL constraints and concurrent write behavior were **not verified**. Tests and demo setup use isolated SQLite databases. No existing database was intentionally accessed, seeded or migrated.
- React component tests cover authentication, route protection, inventory, slots, bookings, transactions, staff, analytics, fairness settings and defaulters using test data. The live launcher check covers HTML serving and a real proxy/API/Java path. It does not prove every workflow in a manually operated browser.
- Flutter tests mostly cover models, response handling and role values; the existing widget test is a placeholder. A physical phone, emulator login, QR camera scanning and full mobile-to-server session were **not demonstrated live**.
- The Android debug build did not reach compilation: it remained at Gradle assembleDebug while the required gradle-9.1.0-all.zip.part stayed at zero bytes. The stalled verification attempt was stopped. No APK build pass is claimed. Retry the documented build command once the Gradle distribution download is available.
- Java uses no JDBC/JPA connection. Database operations remain in the existing Python layer. Spring Boot was not introduced.
- The original Python fallback is retained because full production and device verification is incomplete. Existing source behavior, including capacity/promotion bookkeeping, was preserved rather than silently redesigned.
