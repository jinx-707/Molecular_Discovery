# MolDiscovery — one-command setup and dev launcher
# Usage:
#   make setup   — install all dependencies + copy .env
#   make dev     — start backend (port 8000) + frontend (port 3000)
#   make seed    — seed the database with literature catalysts
#   make test    — run backend integration tests
#   make clean   — remove build artefacts

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
PYTHON       := python
PIP          := pip

# ── Setup ─────────────────────────────────────────────────────────────────

.PHONY: setup
setup: setup-backend setup-frontend
	@echo ""
	@echo "Setup complete."
	@echo "  make dev   — start both servers"
	@echo "  make seed  — populate the database"

.PHONY: setup-backend
setup-backend:
	@echo "==> Setting up backend..."
	@if not exist "$(BACKEND_DIR)\.env" ( \
		copy "$(BACKEND_DIR)\.env.example" "$(BACKEND_DIR)\.env" 2>nul || \
		copy ".env.example" "$(BACKEND_DIR)\.env" 2>nul || \
		echo "DATABASE_URL=sqlite:///./moldiscovery.db" > "$(BACKEND_DIR)\.env" \
	)
	cd $(BACKEND_DIR) && $(PYTHON) -m venv venv
	cd $(BACKEND_DIR) && venv\Scripts\pip install -r requirements.txt
	@echo "Backend ready."

.PHONY: setup-frontend
setup-frontend:
	@echo "==> Setting up frontend..."
	@if not exist "$(FRONTEND_DIR)\.env.local" ( \
		echo NEXT_PUBLIC_API_URL=http://localhost:8000 > "$(FRONTEND_DIR)\.env.local" \
	)
	cd $(FRONTEND_DIR) && npm install
	@echo "Frontend ready."

# ── Dev servers ───────────────────────────────────────────────────────────

.PHONY: dev
dev:
	@echo "Starting backend on :8000 and frontend on :3000"
	@echo "Press Ctrl+C to stop."
	start "MolDiscovery Backend" cmd /k "cd $(BACKEND_DIR) && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
	start "MolDiscovery Frontend" cmd /k "cd $(FRONTEND_DIR) && npm run dev"

.PHONY: backend
backend:
	cd $(BACKEND_DIR) && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000

.PHONY: frontend
frontend:
	cd $(FRONTEND_DIR) && npm run dev

# ── Database ──────────────────────────────────────────────────────────────

.PHONY: seed
seed:
	cd $(BACKEND_DIR) && venv\Scripts\activate && $(PYTHON) scripts/seed_database.py

.PHONY: migrate
migrate:
	cd $(BACKEND_DIR) && venv\Scripts\activate && alembic upgrade head

# ── Testing ───────────────────────────────────────────────────────────────

.PHONY: test
test:
	cd $(BACKEND_DIR) && venv\Scripts\activate && $(PYTHON) -m pytest tests/test_integration.py -v

# ── Models ────────────────────────────────────────────────────────────────

.PHONY: models
models:
	cd $(BACKEND_DIR) && venv\Scripts\activate && $(PYTHON) scripts/download_models.py

# ── Clean ─────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	@if exist "$(BACKEND_DIR)\__pycache__" rmdir /s /q "$(BACKEND_DIR)\__pycache__"
	@if exist "$(BACKEND_DIR)\app\__pycache__" rmdir /s /q "$(BACKEND_DIR)\app\__pycache__"
	@if exist "$(FRONTEND_DIR)\.next" rmdir /s /q "$(FRONTEND_DIR)\.next"
	@if exist "$(BACKEND_DIR)\test_moldiscovery.db" del "$(BACKEND_DIR)\test_moldiscovery.db"
	@echo "Clean complete."
