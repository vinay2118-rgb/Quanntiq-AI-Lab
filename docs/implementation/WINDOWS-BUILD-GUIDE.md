# Quanntiq AI Lab — Windows Build and Validation Guide

This runbook validates `QAL-IMP-001 — Platform Kernel` on Windows 11 before
approval and freeze. Run every command from PowerShell inside the dedicated
`C:\QUANNTIQ\QUANNTIQ-AI-LAB` repository. Do not place files from any other
Quanntiq project in this repository.

## 1. Verify the required tools

```powershell
py -3.14 --version
git --version
docker --version
docker compose version
```

Expected: Python 3.14 or newer, Git, Docker, and Docker Compose all return a
version without an error. Start Docker Desktop before continuing.

## 2. Open and verify the repository

Extract the delivered repository to:

```text
C:\QUANNTIQ\QUANNTIQ-AI-LAB
```

Then run:

```powershell
Set-Location C:\QUANNTIQ\QUANNTIQ-AI-LAB
git status
git log -1 --oneline
Copy-Item .env.example .env
```

Expected: Git reports the `main` branch and a clean working tree. The `.env`
file is local-only and must remain excluded from Git.

## 3. Create the Python 3.14 environment

```powershell
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Expected: the active interpreter reports Python 3.14 or newer and installation
finishes without dependency errors.

## 4. Run the source quality gates

```powershell
ruff check .
mypy src
pytest --cov=qal_kernel --cov-report=term-missing --cov-fail-under=90
```

Required result: Ruff passes, strict mypy passes, all tests pass, and package
coverage is at least 90 percent. Stop here if any gate fails.

## 5. Build and start the platform services

```powershell
docker compose config
docker compose up --build --detach
docker compose ps
```

Expected: PostgreSQL becomes healthy and the kernel container is running. The
first image build can take several minutes.

## 6. Validate the running kernel

```powershell
Invoke-RestMethod http://localhost:8080/health/live | ConvertTo-Json
Invoke-RestMethod http://localhost:8080/health/ready | ConvertTo-Json
(Invoke-WebRequest http://localhost:8080/metrics).Content |
    Select-String "qal_kernel_lifecycle_state"
docker compose logs --tail 100 kernel
```

Required results:

- Liveness returns HTTP 200 with `status` equal to `ok`.
- Readiness returns HTTP 200 with `status` equal to `ready` and database check
  equal to `true`.
- Metrics include `qal_kernel_lifecycle_state`.
- Kernel logs contain no unhandled exception or repeated restart.

The development API page is available at `http://localhost:8080/docs`.

## 7. Stop safely

```powershell
docker compose down
```

This stops the services and preserves the PostgreSQL volume. Do not add the
`--volumes` option unless an intentional database reset has been approved.

## 8. Approval checkpoint

Record these results before freezing QAL-IMP-001:

```text
Python version:
Ruff:
Mypy:
Pytest passed count:
Coverage:
Docker image build:
PostgreSQL health:
Kernel liveness:
Kernel readiness:
Metrics:
Unhandled errors:
```

Only after every result passes may QAL-IMP-001 be approved and frozen. The next
approved implementation component is the Configuration Manager.
