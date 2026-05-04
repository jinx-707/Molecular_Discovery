# MolDiscovery — cross-platform (macOS/Linux)

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
PYTHON       := python3
PIP          := pip3

# ── Setup ─────────────────────────────────────

.PHONY: setup
setup: setup-backend setup-frontend
	@echo ""
	@echo "Setup complete."
	@echo "Run: make dev"

.PHONY: setup-backend
setup-backend:
	@echo "==> Setting up backend..."

	@if [ ! -f "$(BACKEND_DIR)/.env" ]; then \
		cp "$(BACKEND_DIR)/.env.example" "$(BACKEND_DIR)/.env" 2>/dev/null || \
		echo "DATABASE_URL=sqlite:///./moldiscovery.db" > "$(BACKEND_DIR)/.env"; \
	fi

	cd $(BACKEND_DIR) && $(PYTHON) -m venv venv
	cd $(BACKEND_DIR) && source venv/bin/activate && $(PIP) install -r requirements.txt

	@echo "Backend ready."

.PHONY: setup-frontend
setup-frontend:
	@echo "==> Setting up frontend..."

	@if [ ! -f "$(FRONTEND_DIR)/.env.local" ]; then \
		echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > "$(FRONTEND_DIR)/.env.local"; \
	fi

	cd $(FRONTEND_DIR) && npm install
	@echo "Frontend ready."

# ── Dev ───────────────────────────────────────

.PHONY: dev
dev:
	@echo "Starting backend + frontend..."

	@echo "Backend → http://localhost:8000"
	@echo "Frontend → http://localhost:3000"

	@bash -c "cd $(BACKEND_DIR) && source venv/bin/activate && uvicorn app.main:app --reload --port 8000" & \
	bash -c "cd $(FRONTEND_DIR) && npm run dev"

.PHONY: backend
backend:
	cd $(BACKEND_DIR) && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

.PHONY: frontend
frontend:
	cd $(FRONTEND_DIR) && npm run dev

# ── DB ────────────────────────────────────────

.PHONY: seed
seed:
	cd $(BACKEND_DIR) && source venv/bin/activate && $(PYTHON) scripts/seed_database.py

.PHONY: migrate
migrate:
	cd $(BACKEND_DIR) && source venv/bin/activate && alembic upgrade head

# ── Test ──────────────────────────────────────

.PHONY: test
test:
	cd $(BACKEND_DIR) && source venv/bin/activate && pytest tests/test_integration.py -v

# ── Clean ─────────────────────────────────────

.PHONY: clean
clean:
	rm -rf $(BACKEND_DIR)/__pycache__
	rm -rf $(BACKEND_DIR)/app/__pycache__
	rm -rf $(FRONTEND_DIR)/.next
	rm -f $(BACKEND_DIR)/test_moldiscovery.db
	@echo "Clean complete."