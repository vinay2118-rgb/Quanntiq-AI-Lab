# Quanntiq AI Lab Platform Kernel

QAL-IMP-001 implements the platform bootstrap boundary: typed configuration,
dependency injection, service registration, deterministic lifecycle management,
in-process event delivery, structured logging, Prometheus metrics, and Kubernetes-
compatible health endpoints.

## Run

```bash
cp .env.example .env
docker compose up --build
```

The API listens on `http://localhost:8080`. Operational endpoints are:
`/health/live`, `/health/ready`, and `/metrics`.

## Verify

```bash
python -m pip install -e '.[dev]'
ruff check .
mypy src
pytest --cov=qal_kernel --cov-fail-under=90
```

Python 3.14+ is mandatory. Configuration uses the `QAL_` environment prefix.

