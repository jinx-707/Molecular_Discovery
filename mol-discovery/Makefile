.PHONY: help setup dev lint test train run clean

help:
	@echo "MolDiscovery - Local Development Commands"
	@echo "========================================="
	@echo "make setup       # Copy env, install deps"
	@echo "make dev         # Start backend + frontend dev servers"
	@echo "make lint        # Lint code"
	@echo "make test        # Run tests"
	@echo "make train       # ML placeholder"
	@echo "make clean       # Clean installs"

setup: .env
	@echo "✅ .env ready"
	cd backend && poetry install --with dev
	cd frontend && npm ci

.env:
	cp .env.example .env
	@echo "📝 Edit .env (DATABASE_URL, QDRANT_URL=http://localhost:6333, etc.)"
	@echo "💡 Install DBs manually: brew install postgresql redis neo4j"
	@echo "💡 Qdrant: brew install --cask qdrant or download standalone"

dev:
	poetry --directory backend run uvicorn app.main:app --host 0.0.0.0 --reload --port 8000 &
	npm --prefix frontend run dev

lint:
	cd backend && poetry run ruff check . --fix && poetry run black .
	cd frontend && npm run lint --fix

test:
	@echo "Backend tests"
	cd backend && poetry run pytest tests/ -v --cov=backend/app
	@echo "Frontend tests"
	cd frontend && npm test -- --coverage
	@echo "E2E scenario"
	cd backend && poetry run pytest tests/e2e/ -v
	@echo "Performance"
	cd backend && poetry run pytest tests/performance/ -v
	@echo "✅ All tests passed!"

train:
	cd backend && echo "ML training placeholder - see TODO.md"

clean:
	rm -rf backend/__pypackages__ backend/.venv frontend/node_modules .env

