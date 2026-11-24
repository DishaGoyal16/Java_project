# SCMS Java demonstration

## Explain the implementation accurately

“SCMS uses Java for booking eligibility, cancellation checks, issue and return checks, and fair allocation scoring. React and Flutter keep the existing interfaces. FastAPI still handles public APIs, JWT authentication, database reads and writes, notifications and scheduled jobs. It calls an authenticated Java service on localhost before saving the affected operations. The complete backend is not Java.”

Java uses the JDK 17 HTTP server. This integration does not implement Spring Boot, Hibernate, JPA or direct JDBC persistence. Those remain possible later steps. The current design keeps the existing API and schema while moving real decisions into Java.

## Important code

Paths below are relative to the main `scms` folder.

| File | What to show |
|---|---|
| `code/java-rules/src/edu/tiet/scms/AllocationPolicy.java` | Interface and immutable candidate/score records |
| `UsageRecencyPolicy.java` in the same folder | Implements the interface; uses ArrayList, Comparator and stable sorting |
| `WorkflowRules.java` | Booking, cancel, issue and return rules; preserves error order, codes and messages |
| `RuleViolation.java` | Custom exception extending RuntimeException |
| `RulesServer.java` | HTTP entry point, loopback binding, shared-token check, JSON responses and diagnostics |
| `code/backend/app/services/java_rules.py` | Python-to-Java adapter, five-second timeout, errors and explicit engine selection |
| `code/backend/app/services/fairness_engine.py` | Database history goes to Java; returned scores are saved through the original data layer |

The Java API adapter calls domain classes. `AllocationPolicy` provides abstraction; its implementation shows polymorphism. Records and private fields provide encapsulation. The exception class demonstrates inheritance and exception handling. Collection processing implements a real allocation rule. Database connectivity belongs to the retained SQLModel/PostgreSQL layer, not the Java process.

## Prove Java execution

Start from the main project:

```powershell
Set-Location 'C:\Users\Disha Goyal\Desktop\dishaaa\scms'
.\scripts\Start-SCMS.ps1 -Demo -Diagnostics
```

In another terminal:

```powershell
Get-Content 'C:\Users\Disha Goyal\Desktop\dishaaa\scms\.local\java.out.log' -Wait
```

After a booking request, a line identifies `operation=booking`, `handler=WorkflowRules.validate`, its HTTP status and `fallback=false`. Allocation uses `operation=rank handler=UsageRecencyPolicy.rank`. Cancellation, issue and return have their own operation labels. A rejected business rule is still proof that Java executed; a successful operation reports status 200. The log deliberately excludes request payloads, student IDs, passwords and tokens.

The API diagnostic log also identifies `engine=java` or an explicitly selected `engine=python`. Java mode has no automatic fallback. Stopping Java and repeating a rule-dependent request yields 503; it does not quietly process the request in Python. Do this only with the separate demo database, and restart through the launcher afterward.

## Suggested eight-minute viva

1. **Minute 0–1:** Show the main `scms/code` folder and explain React → FastAPI → Java → FastAPI database write. Show the Java classes above.
2. **Minute 1–2:** Run the demo launcher and open http://127.0.0.1:5173. Sign in as `admin@example.com` with the password chosen at setup. Show inventory and slots. Do not display passwords or token storage.
3. **Minute 2–4:** Open Flutter on a connected Android emulator. Sign in as `student@example.com`, browse equipment and request tomorrow's slot. Show REQUESTED and the Java booking log. If no device is available, use the API docs for the student request and state that mobile interaction is not being demonstrated live.
4. **Minute 4–5:** In the dashboard Slots page, use the existing “Run batch allocation” control for that slot. Show the result and the Java `rank` log. A non-empty batch is required to invoke ranking. Empty batches are closed by the retained orchestration.
5. **Minute 5–6:** Sign in as the staff demo account on Flutter. Show the issue/return workflow if the device and QR scanner are available. Otherwise show the executed full-workflow test and explain its scope rather than pretending a scanner was tested.
6. **Minute 6–7:** Show `tests/test_java_rules.py`, particularly the 100 ranking comparison batches, error contracts and complete booking → allocation → issue → return API test. Show the saved backend XML results.
7. **Minute 7–8:** Show TESTING_RESULTS.md and explain the limits: production PostgreSQL and a physical phone session were not verified. Press Enter in the launcher terminal to stop its services.

The registration/login UI and role checks remain the existing application. No new presentation UI was added. The reports and supplied screenshots are unchanged; screenshots are evidence of the earlier application, not new Java test evidence.
