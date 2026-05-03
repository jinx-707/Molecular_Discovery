#!/usr/bin/env python
"""
scripts/init_db.py
------------------
1. Runs Alembic migrations (creates all tables + TimescaleDB hypertable).
2. Seeds a small synthetic dataset:
     - 50 catalysts
     - 20 enzymes
     - 30 experiments (mix of catalyst and enzyme experiments)
3. Vectorizes all records and pushes to Qdrant.

Usage (from repo root):
    cd backend
    python ../scripts/init_db.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Make sure `app` is importable when running from the scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
log = logging.getLogger("init_db")


# ---------------------------------------------------------------------------
# Step 1 – run Alembic migrations
# ---------------------------------------------------------------------------

def run_migrations() -> None:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "backend" / "alembic.ini"))
    alembic_cfg.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parent.parent / "backend" / "alembic"),
    )
    log.info("Running Alembic migrations …")
    command.upgrade(alembic_cfg, "head")
    log.info("Migrations complete.")


# ---------------------------------------------------------------------------
# Step 2 – seed synthetic data
# ---------------------------------------------------------------------------

async def seed() -> None:
    from app.data.ingestor import DataIngestor, _synthetic_catalyst, _synthetic_enzyme, _synthetic_experiment

    ingestor = DataIngestor()

    # --- Catalysts ---
    log.info("Generating 50 synthetic catalysts …")
    cat_records = [_synthetic_catalyst(i) for i in range(50)]
    await ingestor.vectorize_and_store(catalyst_records=cat_records)
    cat_ids = await ingestor.store_catalysts(cat_records)
    log.info("Inserted %d catalysts.", len(cat_ids))

    # --- Enzymes ---
    log.info("Generating 20 synthetic enzymes …")
    enz_records = [_synthetic_enzyme(i) for i in range(20)]
    await ingestor.vectorize_and_store(enzyme_records=enz_records)
    enz_ids = await ingestor.store_enzymes(enz_records)
    log.info("Inserted %d enzymes.", len(enz_ids))

    # --- Experiments (mix: 20 catalyst, 10 enzyme) ---
    log.info("Generating 30 synthetic experiments …")
    exp_records = []
    for _ in range(20):
        exp_records.append(_synthetic_experiment(
            catalyst_id=random.choice(cat_ids),
            enzyme_id=None,
        ))
    for _ in range(10):
        exp_records.append(_synthetic_experiment(
            catalyst_id=None,
            enzyme_id=random.choice(enz_ids),
        ))
    exp_ids = await ingestor.store_experiments(exp_records)
    log.info("Inserted %d experiments.", len(exp_ids))

    log.info("Seed complete. Summary: %d catalysts | %d enzymes | %d experiments",
             len(cat_ids), len(enz_ids), len(exp_ids))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        run_migrations()
    except Exception as exc:
        log.warning("Migration step failed (DB may already be up-to-date): %s", exc)

    asyncio.run(seed())
    log.info("init_db finished successfully.")


if __name__ == "__main__":
    main()
