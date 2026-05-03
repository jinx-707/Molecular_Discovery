"""
DriftDetector
=============
Detects data drift between a reference dataset (past training data) and
incoming experimental results using:

  - Population Stability Index (PSI) for continuous features
  - Kolmogorov-Smirnov test (scipy) for distribution comparison
  - Jensen-Shannon divergence as a secondary metric

Drift events are stored in the drift_events table for audit.

Usage
-----
detector = DriftDetector()
report   = detector.check_drift(reference_experiments, new_experiments)
if report["drift_detected"]:
    print(report["summary"])
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger(__name__)

# Thresholds
PSI_LOW      = 0.10   # no significant drift
PSI_MODERATE = 0.20   # moderate drift — monitor
PSI_HIGH     = 0.25   # significant drift — retrain

KS_ALPHA     = 0.05   # p-value threshold for KS test


# ---------------------------------------------------------------------------
# Core statistical functions
# ---------------------------------------------------------------------------

def calculate_psi(
    expected: np.ndarray,
    actual:   np.ndarray,
    bins:     int = 10,
) -> float:
    """
    Population Stability Index.
    PSI < 0.10  → no drift
    PSI 0.10–0.20 → moderate drift
    PSI > 0.20  → significant drift
    """
    if len(expected) < 2 or len(actual) < 2:
        return 0.0

    # Use shared bin edges from the combined range
    combined = np.concatenate([expected, actual])
    bin_edges = np.linspace(combined.min(), combined.max() + 1e-9, bins + 1)

    exp_counts, _ = np.histogram(expected, bins=bin_edges)
    act_counts, _ = np.histogram(actual,   bins=bin_edges)

    # Convert to proportions, avoid division by zero
    exp_pct = (exp_counts + 1e-8) / (len(expected) + 1e-8 * bins)
    act_pct = (act_counts + 1e-8) / (len(actual)   + 1e-8 * bins)

    psi = float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))
    return round(abs(psi), 4)


def ks_test(
    reference: np.ndarray,
    new_data:  np.ndarray,
) -> Tuple[float, float]:
    """
    Two-sample Kolmogorov-Smirnov test.
    Returns (statistic, p_value).
    """
    try:
        from scipy.stats import ks_2samp
        stat, pval = ks_2samp(reference, new_data)
        return round(float(stat), 4), round(float(pval), 4)
    except ImportError:
        # Manual approximation when scipy is absent
        n1, n2 = len(reference), len(new_data)
        if n1 < 2 or n2 < 2:
            return 0.0, 1.0
        ref_sorted = np.sort(reference)
        new_sorted = np.sort(new_data)
        combined   = np.sort(np.concatenate([ref_sorted, new_sorted]))
        cdf1 = np.searchsorted(ref_sorted, combined, side="right") / n1
        cdf2 = np.searchsorted(new_sorted, combined, side="right") / n2
        stat = float(np.max(np.abs(cdf1 - cdf2)))
        # Approximate p-value
        en   = math.sqrt(n1 * n2 / (n1 + n2))
        pval = float(np.exp(-2 * (en * stat) ** 2))
        return round(stat, 4), round(pval, 4)


def js_divergence(
    p: np.ndarray,
    q: np.ndarray,
    bins: int = 10,
) -> float:
    """Jensen-Shannon divergence (0 = identical, 1 = maximally different)."""
    combined  = np.concatenate([p, q])
    bin_edges = np.linspace(combined.min(), combined.max() + 1e-9, bins + 1)

    p_hist, _ = np.histogram(p, bins=bin_edges, density=True)
    q_hist, _ = np.histogram(q, bins=bin_edges, density=True)

    p_hist = p_hist + 1e-10
    q_hist = q_hist + 1e-10
    m      = 0.5 * (p_hist + q_hist)

    jsd = 0.5 * np.sum(p_hist * np.log(p_hist / m)) + \
          0.5 * np.sum(q_hist * np.log(q_hist / m))
    return round(float(np.clip(jsd, 0, 1)), 4)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

_FEATURES = {
    "activity":    lambda e: e.get("measured_activity")    or e.get("activity"),
    "selectivity": lambda e: e.get("measured_selectivity") or e.get("selectivity"),
    "stability":   lambda e: e.get("measured_stability")   or e.get("stability"),
    "temperature": lambda e: e.get("temperature"),
    "pressure":    lambda e: e.get("pressure"),
}


def _extract_feature(experiments: List[Dict], key: str) -> np.ndarray:
    extractor = _FEATURES.get(key, lambda e: e.get(key))
    values = [extractor(e) for e in experiments]
    values = [float(v) for v in values if v is not None]
    return np.array(values) if values else np.array([0.0])


# ---------------------------------------------------------------------------
# DriftDetector
# ---------------------------------------------------------------------------

class DriftDetector:
    """
    Monitors feature distributions between reference and new experimental data.

    Parameters
    ----------
    psi_threshold : float
        PSI value above which drift is flagged (default 0.10).
    ks_alpha : float
        KS test p-value below which drift is flagged (default 0.05).
    """

    def __init__(
        self,
        psi_threshold: float = PSI_LOW,
        ks_alpha:      float = KS_ALPHA,
    ) -> None:
        self.psi_threshold = psi_threshold
        self.ks_alpha      = ks_alpha

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_drift(
        self,
        reference_experiments: List[Dict],
        new_experiments:       List[Dict],
        features:              Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare feature distributions between reference and new data.

        Returns a report dict with:
          drift_detected : bool
          severity       : "none" | "low" | "moderate" | "high"
          features       : per-feature PSI, KS stat/p, JSD
          summary        : human-readable description
          suggestions    : list of actionable recommendations
        """
        if not reference_experiments or not new_experiments:
            return self._empty_report()

        features = features or list(_FEATURES.keys())
        feature_reports: Dict[str, Any] = {}
        max_psi = 0.0

        for feat in features:
            ref_arr = _extract_feature(reference_experiments, feat)
            new_arr = _extract_feature(new_experiments, feat)

            if len(ref_arr) < 2 or len(new_arr) < 2:
                continue

            psi          = calculate_psi(ref_arr, new_arr)
            ks_stat, ks_p = ks_test(ref_arr, new_arr)
            jsd          = js_divergence(ref_arr, new_arr)

            drifted = psi > self.psi_threshold or ks_p < self.ks_alpha
            max_psi = max(max_psi, psi)

            feature_reports[feat] = {
                "psi":          psi,
                "ks_statistic": ks_stat,
                "ks_p_value":   ks_p,
                "jsd":          jsd,
                "drift":        drifted,
                "severity":     self._psi_severity(psi),
                "ref_mean":     round(float(ref_arr.mean()), 3),
                "new_mean":     round(float(new_arr.mean()), 3),
                "ref_std":      round(float(ref_arr.std()),  3),
                "new_std":      round(float(new_arr.std()),  3),
            }

        drift_detected = any(v["drift"] for v in feature_reports.values())
        severity       = self._psi_severity(max_psi)
        drifted_feats  = [k for k, v in feature_reports.items() if v["drift"]]

        return {
            "drift_detected":  drift_detected,
            "severity":        severity,
            "max_psi":         round(max_psi, 4),
            "features":        feature_reports,
            "drifted_features": drifted_feats,
            "summary":         self._summary(drift_detected, severity, drifted_feats),
            "suggestions":     self._suggestions(feature_reports),
            "checked_at":      datetime.now().isoformat(),
            "n_reference":     len(reference_experiments),
            "n_new":           len(new_experiments),
        }

    def persist_drift_event(
        self,
        report:     Dict[str, Any],
        trigger:    str = "scheduled",
    ) -> Optional[str]:
        """Store a drift event in the database. Returns the event ID."""
        try:
            from app.db.session import SessionLocal
            from app.db.models import DriftEvent

            db = SessionLocal()
            try:
                event = DriftEvent(
                    id=str(uuid.uuid4()),
                    drift_detected=report["drift_detected"],
                    severity=report["severity"],
                    max_psi=report["max_psi"],
                    drifted_features=report["drifted_features"],
                    feature_report=report["features"],
                    summary=report["summary"],
                    trigger=trigger,
                )
                db.add(event)
                db.commit()
                return event.id
            finally:
                db.close()
        except Exception as exc:
            log.warning("Could not persist drift event: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _psi_severity(psi: float) -> str:
        if psi < PSI_LOW:
            return "none"
        if psi < PSI_MODERATE:
            return "low"
        if psi < PSI_HIGH:
            return "moderate"
        return "high"

    @staticmethod
    def _summary(
        drift_detected: bool,
        severity:       str,
        drifted_feats:  List[str],
    ) -> str:
        if not drift_detected:
            return "No significant data drift detected. Model predictions remain reliable."
        feat_str = ", ".join(drifted_feats) if drifted_feats else "unknown features"
        return (
            f"{severity.capitalize()} drift detected in: {feat_str}. "
            "Model predictions may be less reliable for new data. "
            "Consider retraining with recent experiments."
        )

    @staticmethod
    def _suggestions(feature_reports: Dict[str, Any]) -> List[str]:
        suggestions = []
        for feat, rep in feature_reports.items():
            if not rep["drift"]:
                continue
            delta = rep["new_mean"] - rep["ref_mean"]
            direction = "higher" if delta > 0 else "lower"
            suggestions.append(
                f"{feat.capitalize()} distribution shifted {direction} "
                f"(ref mean={rep['ref_mean']:.2f}, new mean={rep['new_mean']:.2f}, "
                f"PSI={rep['psi']:.3f}). "
                f"Collect more data in the {direction} range."
            )
        if not suggestions:
            suggestions.append("No specific feature suggestions.")
        return suggestions

    @staticmethod
    def _empty_report() -> Dict[str, Any]:
        return {
            "drift_detected":   False,
            "severity":         "none",
            "max_psi":          0.0,
            "features":         {},
            "drifted_features": [],
            "summary":          "Insufficient data for drift analysis.",
            "suggestions":      [],
            "checked_at":       datetime.now().isoformat(),
            "n_reference":      0,
            "n_new":            0,
        }


import math  # noqa: E402 (needed for ks_test fallback)
