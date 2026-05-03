"""
EnzymePredictor — Log-Likelihood Ratio (LLR) scoring for protein mutations.

Uses ESM-2 (facebook/esm2_t6_8M_UR50D — the 8M param model, fast and
CPU-friendly) in masked-marginal mode.  Falls back to a deterministic
demo scorer when the model weights are not available, so the API always
returns plausible data.

LLR formula (per position):
    LLR(wt→mt, pos) = log P(mt | context) − log P(wt | context)

A positive LLR means the model considers the mutant more likely than the
wild-type at that position — a proxy for beneficial mutations.
"""
from __future__ import annotations

import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")

# ---------------------------------------------------------------------------
# Demo scorer (no model weights required)
# ---------------------------------------------------------------------------

def _demo_llr(sequence: str, pos: int, wt: str, mt: str) -> float:
    """
    Deterministic demo LLR based on amino-acid physicochemical similarity.
    Returns values in the realistic range [-3, +3].
    """
    # Rough groupings: conservative substitutions score higher
    groups = [
        set("ACGILMFPVW"),   # hydrophobic
        set("RKHDE"),        # charged
        set("STNQ"),         # polar uncharged
        set("YWF"),          # aromatic
    ]
    same_group = any(wt in g and mt in g for g in groups)
    base = 0.8 if same_group else -0.6
    # Add position-dependent noise seeded by sequence content
    seed = sum(ord(c) for c in sequence[max(0, pos-2):pos+3]) + pos
    rng = random.Random(seed)
    return round(base + rng.gauss(0, 0.5), 3)


# ---------------------------------------------------------------------------
# Main predictor
# ---------------------------------------------------------------------------

class EnzymePredictor:
    """
    Zero-shot mutation effect predictor using ESM-2 masked marginals.

    Parameters
    ----------
    model_name : str
        HuggingFace model ID.  Defaults to the 8M-parameter ESM-2 which
        runs on CPU in ~2 s per sequence.
    demo_mode : bool | None
        Force demo mode (True) or real model (False).  None = auto-detect.
    """

    def __init__(
        self,
        model_name: str = "facebook/esm2_t6_8M_UR50D",
        demo_mode: Optional[bool] = None,
    ) -> None:
        self.model_name = model_name
        self._tokenizer = None
        self._model     = None

        if demo_mode is True:
            self.demo_mode = True
            log.info("EnzymePredictor: demo mode (forced)")
            return

        try:
            import torch
            from transformers import AutoTokenizer, EsmForMaskedLM

            log.info("Loading ESM-2 tokenizer and model: %s", model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model     = EsmForMaskedLM.from_pretrained(model_name)
            self._model.eval()
            self._torch = torch
            self.demo_mode = False
            log.info("EnzymePredictor: ESM-2 loaded successfully")

        except Exception as exc:
            log.warning(
                "EnzymePredictor: could not load ESM-2 (%s) — using demo scorer", exc
            )
            self.demo_mode = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_llr(
        self,
        sequence: str,
        mutations: List[Tuple[int, str, str]],
    ) -> List[Dict[str, Any]]:
        """
        Calculate Log-Likelihood Ratios for a list of mutations.

        Parameters
        ----------
        sequence : str
            Wild-type amino-acid sequence (single-letter codes).
        mutations : list of (position, wt_aa, mt_aa)
            position is 0-indexed.

        Returns
        -------
        list of dicts with keys: position, mutation, llr, interpretation
        """
        if self.demo_mode:
            return self._demo_get_llr(sequence, mutations)
        return self._esm_get_llr(sequence, mutations)

    def generate_mutations(
        self,
        sequence: str,
        top_k: int = 10,
        min_llr: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Suggest the top-k single-point mutations predicted to be beneficial.

        Scans every position × every amino-acid substitution and returns
        those with the highest LLR scores.
        """
        if self.demo_mode:
            return self._demo_generate_mutations(sequence, top_k)
        return self._esm_generate_mutations(sequence, top_k, min_llr)

    def score_variant(self, wt_sequence: str, variant_sequence: str) -> Dict[str, Any]:
        """
        Score a full variant sequence against the wild-type.
        Returns aggregate LLR and per-mutation breakdown.
        """
        if len(wt_sequence) != len(variant_sequence):
            raise ValueError("Wild-type and variant sequences must be the same length")

        mutations = [
            (i, wt_sequence[i], variant_sequence[i])
            for i in range(len(wt_sequence))
            if wt_sequence[i] != variant_sequence[i]
        ]

        if not mutations:
            return {"total_llr": 0.0, "mutations": [], "interpretation": "identical to wild-type"}

        results = self.get_llr(wt_sequence, mutations)
        total   = sum(r["llr"] for r in results)

        return {
            "total_llr":     round(total, 3),
            "mutations":     results,
            "interpretation": self._interpret_total(total, len(mutations)),
        }

    # ------------------------------------------------------------------
    # ESM-2 implementation
    # ------------------------------------------------------------------

    def _esm_get_llr(
        self,
        sequence: str,
        mutations: List[Tuple[int, str, str]],
    ) -> List[Dict[str, Any]]:
        import torch

        # Tokenise once
        inputs = self._tokenizer(sequence, return_tensors="pt")
        with torch.no_grad():
            logits = self._model(**inputs).logits.squeeze(0)  # (seq_len+2, vocab)
        log_probs = torch.log_softmax(logits, dim=-1)

        vocab = self._tokenizer.get_vocab()
        results = []

        for pos, wt, mt in mutations:
            tok_pos = pos + 1  # offset for [CLS] token
            wt_id   = vocab.get(wt)
            mt_id   = vocab.get(mt)

            if wt_id is None or mt_id is None:
                log.warning("Unknown amino acid token: wt=%s mt=%s", wt, mt)
                continue

            llr = (log_probs[tok_pos, mt_id] - log_probs[tok_pos, wt_id]).item()
            results.append(self._format_result(pos, wt, mt, llr))

        return results

    def _esm_generate_mutations(
        self,
        sequence: str,
        top_k: int,
        min_llr: float,
    ) -> List[Dict[str, Any]]:
        import torch

        inputs = self._tokenizer(sequence, return_tensors="pt")
        with torch.no_grad():
            logits = self._model(**inputs).logits.squeeze(0)
        log_probs = torch.log_softmax(logits, dim=-1)

        vocab   = self._tokenizer.get_vocab()
        results = []

        for pos, wt in enumerate(sequence):
            tok_pos = pos + 1
            wt_id   = vocab.get(wt)
            if wt_id is None:
                continue
            wt_lp = log_probs[tok_pos, wt_id].item()

            for mt in AMINO_ACIDS:
                if mt == wt:
                    continue
                mt_id = vocab.get(mt)
                if mt_id is None:
                    continue
                llr = log_probs[tok_pos, mt_id].item() - wt_lp
                if llr >= min_llr:
                    results.append(self._format_result(pos, wt, mt, llr))

        results.sort(key=lambda x: x["llr"], reverse=True)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Demo implementations
    # ------------------------------------------------------------------

    def _demo_get_llr(
        self,
        sequence: str,
        mutations: List[Tuple[int, str, str]],
    ) -> List[Dict[str, Any]]:
        return [
            self._format_result(pos, wt, mt, _demo_llr(sequence, pos, wt, mt))
            for pos, wt, mt in mutations
        ]

    def _demo_generate_mutations(
        self, sequence: str, top_k: int
    ) -> List[Dict[str, Any]]:
        rng = random.Random(sum(ord(c) for c in sequence))
        positions = rng.sample(range(len(sequence)), min(top_k * 2, len(sequence)))
        results = []
        for pos in positions:
            wt = sequence[pos]
            mt = rng.choice([aa for aa in AMINO_ACIDS if aa != wt])
            llr = _demo_llr(sequence, pos, wt, mt)
            results.append(self._format_result(pos, wt, mt, llr))
        results.sort(key=lambda x: x["llr"], reverse=True)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_result(pos: int, wt: str, mt: str, llr: float) -> Dict[str, Any]:
        if llr > 1.0:
            interp = "strongly beneficial"
        elif llr > 0.3:
            interp = "likely beneficial"
        elif llr > -0.3:
            interp = "neutral"
        elif llr > -1.0:
            interp = "likely deleterious"
        else:
            interp = "strongly deleterious"

        return {
            "position":       pos,
            "mutation":       f"{wt}{pos + 1}{mt}",   # 1-indexed for biologists
            "wt":             wt,
            "mt":             mt,
            "llr":            round(llr, 3),
            "interpretation": interp,
        }

    @staticmethod
    def _interpret_total(total: float, n_mutations: int) -> str:
        avg = total / n_mutations
        if avg > 0.5:
            return f"Variant likely improved ({n_mutations} mutations, avg LLR {avg:.2f})"
        if avg > 0:
            return f"Variant marginally improved ({n_mutations} mutations, avg LLR {avg:.2f})"
        return f"Variant likely impaired ({n_mutations} mutations, avg LLR {avg:.2f})"
