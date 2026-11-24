# SCMS Java Project

Smart Sports Equipment Management System for UCS553 Enterprise Web Application.

This is a hybrid application: Java processes booking eligibility, allocation ranking,
cancellation checks and equipment issue/return validation. FastAPI retains the public
REST APIs, authentication, database persistence, notifications, jobs and analytics.
The frontend is React and the mobile application is Flutter. This is not a fully
Java backend and does not use Spring Boot or JPA.

## Branches

| Branch | Purpose |
|---|---|
| main | Complete integrated project and documentation |
| website | Website development: React frontend and shared backend |
| app | Mobile development: Flutter app and shared backend |

Both development branches initially include the complete source so neither loses
shared features, launch scripts or rollback code.

## Folders

| Folder | Contents |
|---|---|
| code/web_dashboard | Website frontend: React and TypeScript |
| code/backend | Public backend: FastAPI, SQLModel and database integration |
| code/java-rules | Java backend business-rule service |
| code/flutter_app | Flutter mobile application |
| scripts | Windows launcher, isolated demo setup and verification |
| java_docs | Reports, Windows setup, testing and professor demonstration guides |
| screenshots | Original supplied application images |
| Docs | Original project documents and diagrams |

## Start on Windows

From your clone folder, install JDK 17+, Python 3.12, Node.js and Flutter as needed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\code\backend\requirements.txt
Push-Location .\code\web_dashboard
npm.cmd ci --no-audit --no-fund
Pop-Location
.\scripts\Start-SCMS.ps1 -Demo -Diagnostics
```

Choose a private demo password when prompted. Open http://127.0.0.1:5173.
Demo setup uses a separate local SQLite database. No credentials, local databases,
dependency folders or build outputs are included in this repository.
The detailed guides retain paths for the author's existing Windows workspace;
replace that workspace prefix with your clone folder when using another location.

## Documentation

- [Windows setup](java_docs/RUN_PROJECT_WINDOWS.md)
- [Professor demonstration](java_docs/JAVA_DEMONSTRATION_GUIDE.md)
- [Executed tests and limitations](java_docs/TESTING_RESULTS.md)
- [Migration and cleanup](java_docs/JAVA_MIGRATION_SUMMARY.md)

The report describes the earlier proposed Java architecture. The technical guides
describe the implemented hybrid system and its verification limits.

## Attribution

Adapted from the existing SCMS Software Engineering project at
https://github.com/sanveer-singh-suneja/scms . Original project documents and
contributor records are retained. This repository contains the local Java integration.
