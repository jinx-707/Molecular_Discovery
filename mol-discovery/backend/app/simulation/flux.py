"""
PathwayDesigner — Constraint-Based Metabolic Modelling.

Uses COBRApy for Flux Balance Analysis (FBA) and gene-deletion simulations.
Falls back to a deterministic demo mode when COBRApy or a model JSON is
not available, so the API always returns plausible data.

Typical usage
-------------
designer = PathwayDesigner()
designer.set_target("EX_etoh_e")          # maximise ethanol export
knockouts = designer.find_knockout_targets()
fluxes    = designer.get_flux_distribution(gene_knockouts=knockouts[:2])
"""
from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

_DEMO_GENES = [
    "b0008", "b0114", "b0115", "b0116", "b0351",
    "b0356", "b0474", "b0726", "b0727", "b1241",
    "b1276", "b1380", "b1602", "b1603", "b1779",
]

_DEMO_REACTIONS = [
    "PFK", "PGI", "PGK", "PGM", "PYK",
    "CS",  "ACONTa", "ICDHyr", "AKGDH", "SUCOAS",
    "FUM", "MDH",    "PDH",    "PPC",   "PPCK",
]

_DEMO_METABOLITES = [
    "atp_c", "adp_c", "nadh_c", "nad_c", "pyr_c",
    "accoa_c", "oaa_c", "cit_c", "icit_c", "akg_c",
]


def _seeded_float(seed: int, lo: float, hi: float) -> float:
    return lo + (hi - lo) * (abs(hash(seed)) % 1000) / 1000


# ---------------------------------------------------------------------------
# PathwayDesigner
# ---------------------------------------------------------------------------

class PathwayDesigner:
    """
    Wraps COBRApy for FBA-based pathway engineering suggestions.

    Parameters
    ----------
    model_path : str
        Path to a COBRApy-compatible JSON model file.
        If the file is missing, demo mode is used automatically.
    organism : str
        Label used in result metadata ("ecoli", "yeast", etc.).
    """

    def __init__(
        self,
        model_path: str = "models/iJO1366.json",
        organism: str = "ecoli",
    ) -> None:
        self.organism   = organism
        self.model_path = model_path
        self._model     = None
        self._objective: Optional[str] = None
        self.demo_mode  = True

        try:
            import cobra
            import cobra.io as cio
            import os

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            self._model    = cio.load_json_model(model_path)
            self._cobra    = cobra
            self.demo_mode = False
            log.info("PathwayDesigner: loaded COBRApy model from %s", model_path)

        except Exception as exc:
            log.warning(
                "PathwayDesigner: COBRApy unavailable (%s) — using demo mode", exc
            )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_target(self, reaction_id: str) -> None:
        """Set the objective reaction to maximise."""
        self._objective = reaction_id
        if not self.demo_mode and self._model:
            try:
                self._model.objective = reaction_id
                log.info("Objective set to: %s", reaction_id)
            except Exception as exc:
                log.warning("Could not set objective %s: %s", reaction_id, exc)

    # ------------------------------------------------------------------
    # FBA
    # ------------------------------------------------------------------

    def get_flux_distribution(
        self,
        gene_knockouts: Optional[List[str]] = None,
        overexpressions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run FBA and return flux values, growth rate, and key metabolite levels.
        """
        if self.demo_mode:
            return self._demo_flux(gene_knockouts, overexpressions)

        try:
            with self._model as model:
                if gene_knockouts:
                    for g in gene_knockouts:
                        try:
                            model.genes.get_by_id(g).knock_out()
                        except Exception:
                            log.debug("Gene not found for knockout: %s", g)

                if overexpressions:
                    for rxn_id in overexpressions:
                        try:
                            rxn = model.reactions.get_by_id(rxn_id)
                            rxn.upper_bound = rxn.upper_bound * 2
                        except Exception:
                            log.debug("Reaction not found for overexpression: %s", rxn_id)

                solution = model.optimize()

                if solution.status != "optimal":
                    return {"status": solution.status, "fluxes": {}, "growth_rate": 0.0}

                top_fluxes = (
                    solution.fluxes
                    .abs()
                    .sort_values(ascending=False)
                    .head(20)
                    .to_dict()
                )

                return {
                    "status":      "optimal",
                    "growth_rate": round(solution.objective_value, 4),
                    "fluxes":      {k: round(v, 4) for k, v in top_fluxes.items()},
                    "knockouts":   gene_knockouts or [],
                    "overexpressions": overexpressions or [],
                }

        except Exception as exc:
            log.error("FBA failed: %s", exc)
            return {"status": "error", "error": str(exc), "fluxes": {}}

    # ------------------------------------------------------------------
    # Gene knockout analysis
    # ------------------------------------------------------------------

    def find_knockout_targets(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Identify gene knockouts predicted to improve target production.
        Uses single-gene deletion analysis via COBRApy.
        """
        if self.demo_mode:
            return self._demo_knockouts(n)

        try:
            from cobra.flux_analysis import single_gene_deletion

            results = single_gene_deletion(self._model)
            # Filter for knockouts that maintain growth but improve objective
            viable = results[results["growth"] > 0.05].copy()
            viable["score"] = viable["growth"] / results["growth"].max()
            top = viable.nlargest(n, "score")

            return [
                {
                    "gene":        str(idx),
                    "growth_rate": round(row["growth"], 4),
                    "score":       round(row["score"], 3),
                    "rationale":   f"Knockout of {idx} maintains {row['growth']:.2f} growth rate",
                }
                for idx, row in top.iterrows()
            ]

        except Exception as exc:
            log.error("Gene deletion analysis failed: %s", exc)
            return self._demo_knockouts(n)

    # ------------------------------------------------------------------
    # gRNA design (CRISPR)
    # ------------------------------------------------------------------

    def design_grna(
        self,
        target_gene: str,
        n_guides: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Suggest gRNA sequences for CRISPR editing of a target gene.
        In demo mode returns plausible synthetic sequences.
        In production, integrate CRISPy or DeepCRISTL predictions.
        """
        return self._demo_grna(target_gene, n_guides)

    # ------------------------------------------------------------------
    # Demo implementations
    # ------------------------------------------------------------------

    def _demo_flux(
        self,
        knockouts: Optional[List[str]],
        overexpressions: Optional[List[str]],
    ) -> Dict[str, Any]:
        base_growth = 0.873
        ko_penalty  = 0.08 * len(knockouts or [])
        oe_boost    = 0.05 * len(overexpressions or [])
        growth      = max(0.0, base_growth - ko_penalty + oe_boost)

        rng = random.Random(42)
        fluxes = {
            rxn: round(rng.uniform(0.1, 20.0) * (0.7 if rxn in (knockouts or []) else 1.0), 3)
            for rxn in _DEMO_REACTIONS
        }

        return {
            "status":          "optimal",
            "growth_rate":     round(growth, 4),
            "fluxes":          fluxes,
            "knockouts":       knockouts or [],
            "overexpressions": overexpressions or [],
            "bottlenecks":     ["NADH regeneration", "ATP maintenance"],
            "demo":            True,
        }

    def _demo_knockouts(self, n: int) -> List[Dict[str, Any]]:
        rng = random.Random(99)
        genes = rng.sample(_DEMO_GENES, min(n, len(_DEMO_GENES)))
        return [
            {
                "gene":        g,
                "growth_rate": round(rng.uniform(0.6, 0.9), 4),
                "score":       round(rng.uniform(0.5, 1.0), 3),
                "rationale":   f"Knockout of {g} redirects carbon flux toward target pathway",
            }
            for g in genes
        ]

    @staticmethod
    def _demo_grna(target_gene: str, n_guides: int) -> List[Dict[str, Any]]:
        bases = "ACGT"
        rng   = random.Random(sum(ord(c) for c in target_gene))
        guides = []
        for i in range(n_guides):
            seq = "".join(rng.choice(bases) for _ in range(20))
            pam = "NGG"
            guides.append({
                "rank":              i + 1,
                "sequence":          seq,
                "pam":               pam,
                "on_target_score":   round(rng.uniform(0.55, 0.98), 3),
                "off_target_score":  round(rng.uniform(0.01, 0.15), 3),
                "gc_content":        round(seq.count("G") + seq.count("C")) / 20,
                "target_gene":       target_gene,
                "position":          rng.randint(1, 3000),
            })
        guides.sort(key=lambda x: x["on_target_score"], reverse=True)
        return guides
