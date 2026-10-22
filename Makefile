.PHONY: help install test lint format clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install     - Install development dependencies"
	@echo "  make test        - Run test suite with pytest"
	@echo "  make lint        - Run ruff check and mypy"
	@echo "  make format      - Format code with ruff format"
	@echo "  make docker-up   - Start local services with docker-compose"
	@echo "  make docker-down - Stop local services"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/

docker-up:
	docker-compose -f deploy/docker-compose.yml up --build -d

docker-down:
	docker-compose -f deploy/docker-compose.yml down

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
