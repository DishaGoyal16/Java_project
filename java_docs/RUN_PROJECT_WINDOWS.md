# Run SCMS on Windows

The main application is `C:\Users\Disha Goyal\Desktop\dishaaa\scms`. There is one checkout. The reports stay in `java_docs`; the supplied images stay in `Scrrenshots`.

## Dependencies

Open PowerShell and run:

```powershell
Set-Location 'C:\Users\Disha Goyal\Desktop\dishaaa\scms'
java -version
javac -version
python --version
node --version
npm.cmd --version
flutter.bat --version
```

The Java service requires JDK 17 or newer and is compiled for Java 17. Verification used Temurin 17.0.20, Python 3.12 and Node 24.20.0. Java uses the JDK HTTP server; Maven, Spring Boot and a separate Java database driver are not required. Verification used Flutter 3.47.0 and Dart 3.13.0. Flutter uses the existing pubspec and SDK dependency resolution.

The local Python environment and dashboard dependencies are already installed. To install them again on a fresh checkout:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r .\code\backend\requirements.txt
Push-Location .\code\web_dashboard
npm.cmd ci --no-audit --no-fund
Pop-Location
Push-Location .\code\flutter_app
flutter.bat pub get
Pop-Location
```

## Start a separate local demonstration

```powershell
.\scripts\Start-SCMS.ps1 -Demo -Diagnostics
```

Enter a password of at least eight characters when asked. It is hashed in the separate `.local/demo.db` database and is not written to a script or printed. New demo accounts are `admin@example.com`, `staff@example.com` and `student@example.com`. Existing demo accounts keep their existing password. This mode never seeds or modifies the existing PostgreSQL database.

The script builds Java, starts Java, waits for its authenticated health check, starts FastAPI, waits for its health check, then starts the dashboard. Open **http://127.0.0.1:5173** and log in with the admin demo account and the password you chose. API documentation is at **http://127.0.0.1:8000/docs**.

Keep this PowerShell session open. Press Enter in it to stop its service process trees. Logs are in `scms/.local`. The script restores the environment values it changed. It refuses to start over listeners on its required ports.

## Use the existing database

No existing PostgreSQL connection was provided or verified. Keep the current database and its data. Do not run the original demo seeder against it.

Set `DATABASE_URL` and the same stable `SECRET_KEY` already used by your installation, either in `code/backend/.env` or in the process environment. The `.env` file is loaded from the backend working directory. To enter an existing connection string without displaying it:

```powershell
$dbSecret = Read-Host 'Existing PostgreSQL connection URL' -AsSecureString
$env:DATABASE_URL = [Net.NetworkCredential]::new('', $dbSecret).Password
$jwtSecret = Read-Host 'Existing SECRET_KEY' -AsSecureString
$env:SECRET_KEY = [Net.NetworkCredential]::new('', $jwtSecret).Password
.\scripts\Start-SCMS.ps1 -Diagnostics
```

The connection URL must use the existing PostgreSQL SQLAlchemy format. No table migration was added. The retained backend still calls its original `create_all` startup function, which can create missing tables; it does not drop existing tables. Test first against a database copy before changing a live installation. Do not point a demo at production data.

## Ports and connections

| Component | Address | Purpose |
|---|---|---|
| React Vite | 127.0.0.1:5173 | Browser dashboard; `/api` is proxied to port 8000 |
| FastAPI | 0.0.0.0:8000 | Existing public APIs, authentication and database operations |
| Java | 127.0.0.1:8091 | Authenticated internal business-rule service |
| PostgreSQL | Existing URL | Retained database; port comes from that URL |

The launcher enables `SCMS_RULES_ENGINE=java` and generates a shared internal token. It sets `APP_ENV=production` to suppress SQL parameter logging and detailed internal error responses. `-Diagnostics` enables safe operation/class/status logs. Java is loopback-only; do not expose it directly to phones or browsers. A Java outage produces a 503 response, never an automatic Python fallback.

## Run components separately

The launcher is recommended because both processes need the same internal token. For separate terminals, set the same privately generated `SCMS_RULES_TOKEN` (at least 32 characters) in both terminals; do not put it in source control. Set the existing database environment as above.

```powershell
# Java terminal, from scms
.\code\java-rules\build.ps1
$env:SCMS_RULES_DIAGNOSTICS = 'true'
java -jar .\code\java-rules\build\scms-rules.jar

# API terminal, from scms, with the same token
$env:SCMS_RULES_ENGINE = 'java'
$env:SCMS_RULES_URL = 'http://127.0.0.1:8091'
$env:APP_ENV = 'production'
Set-Location .\code\backend
& ..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Dashboard terminal, from scms
Set-Location .\code\web_dashboard
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Stop these foreground commands with Ctrl+C. For Python rollback, set `SCMS_RULES_ENGINE=python` in the API terminal and restart FastAPI. Java is then not used. Keep the same database and JWT secret. This is an explicit operational choice, not a silent fallback.

## Flutter

Start the main launcher first. In another PowerShell:

```powershell
Set-Location 'C:\Users\Disha Goyal\Desktop\dishaaa\scms\code\flutter_app'
flutter.bat devices
flutter.bat run --dart-define=SCMS_API_BASE_URL=http://10.0.2.2:8000
```

`10.0.2.2` is the existing Android-emulator host address. On a physical phone, use your laptop's actual LAN IPv4 address instead; find it with `ipconfig`. Both devices need network access and the Windows firewall must allow the API. For example, pass `--dart-define=SCMS_API_BASE_URL=http://YOUR_ACTUAL_LAPTOP_IP:8000`. No trailing `/api` is needed because the Flutter endpoint paths already include it. The default remains the original emulator address. Java communication is internal, so the phone still connects only to FastAPI.

## Tests

```powershell
# From scms/code/backend, with Java service and matching token running
$env:DATABASE_URL = 'sqlite://'
$env:APP_ENV = 'test'
$env:SCMS_RULES_ENGINE = 'java'
& ..\..\.venv\Scripts\python.exe -m pytest tests -q
& ..\..\.venv\Scripts\python.exe tests/live_smoke.py

# Dashboard, from scms/code/web_dashboard
npm.cmd run test:run -- --maxWorkers=1 --minWorkers=1
npm.cmd run build

# Mobile, from scms/code/flutter_app
flutter.bat test
flutter.bat build apk --debug --no-pub
```

Run database-test commands in a separate terminal from your normal server. The pytest fixtures use isolated SQLite databases. The live smoke creates a temporary database, and `scripts/verify_launcher.py` tests all launched services with a disposable `.local/launcher-smoke.db`. It refuses to overwrite that file if it already exists.
