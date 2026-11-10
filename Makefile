.PHONY: all test run lint clean docker-build

all: lint test

test:
	pytest -v tests/

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

lint:
	ruff check .

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__

docker-build:
	docker build -t app:latest .
