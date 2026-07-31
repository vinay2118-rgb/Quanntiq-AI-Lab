.PHONY: install lint typecheck test validate run

install:
	python -m pip install -e '.[dev]'

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest --cov=qal_kernel --cov-report=term-missing --cov-fail-under=90

validate: lint typecheck test

run:
	uvicorn qal_kernel.main:app --host 0.0.0.0 --port 8080

