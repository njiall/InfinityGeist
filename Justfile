# Geist project task runner

# Run linter (ruff)
lint:
    cd services/api && python -m ruff check src/ tests/
    cd services/api && python -m ruff format --check src/ tests/

# Fix linting issues
lint-fix:
    cd services/api && python -m ruff check --fix src/ tests/
    cd services/api && python -m ruff format src/ tests/

# Run type checker (mypy)
typecheck:
    cd services/api && python -m mypy --strict src/geist_api/

# Run tests
test:
    cd services/api && python -m pytest tests/ -v

# Run tests with coverage
test-cov:
    cd services/api && python -m pytest tests/ --cov=geist_api --cov-report=term-missing

# Run all quality checks
check: lint typecheck test

# Index chunks into ChromaDB
index:
    python -m geist_api.cli.index data/processed/chunks_all.jsonl

# Index with full reindex (ignore existing hashes)
index-full:
    python -m geist_api.cli.index data/processed/chunks_all.jsonl --full
