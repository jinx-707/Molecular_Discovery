# MolDiscovery Project TODO

## ✅ Completed
- [x] Root config files (README, docker-compose, .env.example, pyproject.toml, package.json frontend, Makefile, CI)
- [x] Dockerfiles (backend/frontend)
- [x] Backend skeleton (app/main.py, core/config.py, api/, models/, services/, ml/)
- [x] Frontend skeleton (next.config, tailwind, src/app layout/page)
- [x] Monorepo setup (.gitignore, root package.json)

## 🔄 In Progress
## ⏳ Planned Steps

### 1. Backend Implementation
- [ ] API routers: catalysts.py, enzymes.py, simulations.py, molecules.py
- [ ] Database models (SQLAlchemy): Molecule, Catalyst, EnzymeReaction
- [ ] ML pipelines: catalyst screening (OpenCatalyst integration)
- [ ] Simulation service (PySCF DFT, MD interfaces)
- [ ] Prefect workflows for training/inference
- [ ] Authentication/JWT

### 2. Frontend Components
- [ ] shadcn/ui components: MoleculeViewer3D, SearchTable, Dashboard
- [ ] RDKit molecule renderer
- [ ] TanStack Query for API calls
- [ ] Dashboard pages: /catalysts, /enzymes, /screening

### 3. Data & Scripts
- [ ] /scripts/db_init.py (collections, indexes)
- [ ] /notebooks/01_data_exploration.ipynb
- [ ] Sample datasets (QM9, OpenCatalyst)

### 4. Testing
- [ ] Backend pytest (80% coverage)
- [ ] Frontend Jest + React Testing Library
- [ ] E2E Cypress

### 5. Deployment
- [ ] docker-compose.prod.yml
- [ ] Kubernetes manifests (/k8s)
- [ ] GPU Dockerfiles

### 6. Documentation
- [ ] Backend API docs (/docs)
- [ ] ML model cards
- [ ] User guide

## Commands to Run
```bash
make setup  # Install everything
make up     # Full stack
make test   # Run tests
```

