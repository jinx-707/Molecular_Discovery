# MolDiscovery - AI Platform for Catalyst and Enzyme Discovery

## Overview
MolDiscovery is an enterprise-grade AI platform for accelerating catalyst and enzyme discovery.

**Key Features:**
- Molecular property prediction
- Catalyst screening
- Enzyme annotation
- Interactive dashboard

## Tech Stack
- Backend: FastAPI (Python 3.11)
- Frontend: Next.js 14
- DBs: PostgreSQL, Qdrant, Neo4j, Redis

## Quickstart (Local)

1. Setup:
   ```bash
   make setup  # Copy .env, install deps
   ```

2. Start:
   ```bash
   make dev  # Backend:8000 + Frontend:3000
   ```

3. Access:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## DB Setup (macOS):
```bash
brew install postgresql redis neo4j
brew install --cask qdrant
brew services start postgresql redis neo4j
qdrant
```

## Commands
```
make lint    # Fix linting
make test    # Run tests
make clean   # Cleanup
```

## Project Structure
```
mol-discovery/
├── backend/     # FastAPI app
├── frontend/    # Next.js dashboard
└── ...
```

See TODO.md for next steps.

