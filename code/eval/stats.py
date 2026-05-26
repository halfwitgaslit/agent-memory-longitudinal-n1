"""Statistical procedures for the eval (architecture/v1.md §4.6).

All implementations are vetted against scipy or the standard estimators in
the relevant statistics literature.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank (paired)


def pairwise_wilcoxon(
    arm_data: Dict[str, Sequence[float]],
    alternative: str = "two-sided",
) -> Dict[Tuple[str, str], Dict[str, float]]:
    """Pairwise Wilcoxon signed-rank tests across arms.

    Returns dict {(arm_a, arm_b) → {statistic, p_value, n_pairs}}.
    Pairs are matched by index (assumed: same index = same task).
    """
    out: Dict[Tuple[str, str], Dict[str, float]] = {}
    for a, b in combinations(sorted(arm_data.keys()), 2):
        ya = np.asarray(arm_data[a], dtype=float)
        yb = np.asarray(arm_data[b], dtype=float)
        n = min(len(ya), len(yb))
        ya = ya[:n]
        yb = yb[:n]
        # Drop NaN pairs
        mask = ~(np.isnan(ya) | np.isnan(yb))
        if mask.sum() < 5:
            out[(a, b)] = {"statistic": float("nan"), "p_value": float("nan"), "n_pairs": int(mask.sum())}
            continue
        try:
            res = stats.wilcoxon(ya[mask], yb[mask], alternative=alternative, zero_method="wilcox")
            out[(a, b)] = {
                "statistic": float(res.statistic),
                "p_value": float(res.pvalue),
                "n_pairs": int(mask.sum()),
            }
        except Exception as e:
            out[(a, b)] = {"statistic": float("nan"), "p_value": float("nan"), "n_pairs": int(mask.sum()), "error": str(e)[:200]}
    return out


# ---------------------------------------------------------------------------
# Bonferroni correction


def bonferroni_correct(p_values: Sequence[float], alpha: float = 0.05) -> Dict[str, List[float]]:
    """Apply Bonferroni correction to a sequence of p-values.

    Returns {p_corrected, reject_h0 (per-test bool list), alpha_corrected (scalar)}.
    """
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    if n == 0:
        return {"p_corrected": [], "reject_h0": [], "alpha_corrected": alpha}
    p_corr = np.minimum(p * n, 1.0)
    return {
        "p_corrected": p_corr.tolist(),
        "reject_h0": (p_corr < alpha).tolist(),
        "alpha_corrected": alpha / n,
    }


# ---------------------------------------------------------------------------
# Bootstrap BCa CI


def bootstrap_ci_bca(
    data: Sequence[float],
    statistic_fn=np.mean,
    B: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Dict[str, float]:
    """Bootstrap Bias-Corrected and Accelerated (BCa) confidence interval.

    Reference: Efron & Tibshirani, "An Introduction to the Bootstrap" (1993),
    chapter 14.

    Returns {point_estimate, ci_low, ci_high, B}.
    """
    x = np.asarray(data, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 2:
        return {"point_estimate": float(statistic_fn(x)) if n else float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan"), "B": B, "n": n}

    rng = np.random.default_rng(seed)
    theta_hat = float(statistic_fn(x))
    # Bootstrap replicates
    idx = rng.integers(0, n, size=(B, n))
    boot_samples = x[idx]
    theta_boot = np.apply_along_axis(statistic_fn, 1, boot_samples)

    # Bias correction
    z0 = stats.norm.ppf((np.sum(theta_boot < theta_hat) + 0.5) / (B + 1))
    # Acceleration via jackknife
    jack = np.array([statistic_fn(np.delete(x, i)) for i in range(n)])
    jack_mean = float(np.mean(jack))
    num = np.sum((jack_mean - jack) ** 3)
    den = 6.0 * (np.sum((jack_mean - jack) ** 2) ** 1.5)
    a = float(num / den) if den != 0 else 0.0

    z_alpha_lo = stats.norm.ppf(alpha / 2)
    z_alpha_hi = stats.norm.ppf(1 - alpha / 2)
    alpha1 = stats.norm.cdf(z0 + (z0 + z_alpha_lo) / (1 - a * (z0 + z_alpha_lo)))
    alpha2 = stats.norm.cdf(z0 + (z0 + z_alpha_hi) / (1 - a * (z0 + z_alpha_hi)))
    alpha1 = max(0.0, min(1.0, alpha1))
    alpha2 = max(0.0, min(1.0, alpha2))
    ci_low = float(np.quantile(theta_boot, alpha1))
    ci_high = float(np.quantile(theta_boot, alpha2))
    return {
        "point_estimate": theta_hat,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "B": B,
        "n": n,
        "z0": float(z0),
        "a": float(a),
    }


# ---------------------------------------------------------------------------
# Effect sizes


def cohens_d(a: Sequence[float], b: Sequence[float], paired: bool = True) -> float:
    """Cohen's d for paired (default) or independent samples."""
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    if paired:
        n = min(len(x), len(y))
        x = x[:n]
        y = y[:n]
        d = x - y
        d = d[~np.isnan(d)]
        if len(d) < 2:
            return float("nan")
        return float(np.mean(d) / np.std(d, ddof=1))
    # Independent samples
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    if len(x) < 2 or len(y) < 2:
        return float("nan")
    pooled_var = ((len(x) - 1) * np.var(x, ddof=1) + (len(y) - 1) * np.var(y, ddof=1)) / (len(x) + len(y) - 2)
    if pooled_var <= 0:
        return float("nan")
    return float((np.mean(x) - np.mean(y)) / math.sqrt(pooled_var))


def cliff_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Cliff's delta — non-parametric effect size.

    Returns δ ∈ [-1, +1]: positive means a > b stochastically.
    """
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    if len(x) == 0 or len(y) == 0:
        return float("nan")
    # Vectorized pairwise comparison
    greater = np.sum(x[:, None] > y[None, :])
    less = np.sum(x[:, None] < y[None, :])
    n = len(x) * len(y)
    return float((greater - less) / n)


# ---------------------------------------------------------------------------
# MADCovar (Median-Absolute-Deviation-based covariance adjustment for n=1)
# Reference: arxiv 2506.20523. The published estimator is a robust analog of
# CUPED (Controlled-experiment Using Pre-Experiment Data) using MAD instead of
# variance for adjustment-coefficient estimation. Useful in n=1 settings where
# the experimental unit has high autocorrelation.


def mad_covar(
    y: Sequence[float],
    x: Sequence[float],
) -> Dict[str, float]:
    """Apply MADCovar variance reduction.

    Given outcome `y` and covariate `x` (e.g., time_of_day_bucket), return:
        y_adjusted = y - theta_robust * (x - median(x))
    where theta_robust = MAD(y, x) / MAD(x).

    Returns {y_adjusted: list, theta: float, variance_reduction_pct: float}.
    """
    ya = np.asarray(y, dtype=float)
    xa = np.asarray(x, dtype=float)
    n = min(len(ya), len(xa))
    ya = ya[:n]
    xa = xa[:n]
    mask = ~(np.isnan(ya) | np.isnan(xa))
    ya = ya[mask]
    xa = xa[mask]
    if len(ya) < 5:
        return {"y_adjusted": ya.tolist(), "theta": 0.0, "variance_reduction_pct": 0.0}
    med_x = float(np.median(xa))
    med_y = float(np.median(ya))
    # Robust covariance via MAD
    abs_dev_x = np.abs(xa - med_x)
    abs_dev_y = np.abs(ya - med_y)
    mad_x = float(np.median(abs_dev_x))
    if mad_x <= 1e-12:
        return {"y_adjusted": ya.tolist(), "theta": 0.0, "variance_reduction_pct": 0.0}
    # theta as the sign-aware ratio of co-deviation
    coupled = np.median((ya - med_y) * (xa - med_x)) / (mad_x ** 2 + 1e-12)
    theta = float(coupled)
    y_adj = ya - theta * (xa - med_x)
    var_before = float(np.var(ya, ddof=1))
    var_after = float(np.var(y_adj, ddof=1))
    if var_before <= 0:
        red = 0.0
    else:
        red = 100.0 * (var_before - var_after) / var_before
    return {
        "y_adjusted": y_adj.tolist(),
        "theta": theta,
        "variance_reduction_pct": red,
        "n": len(ya),
    }


# ---------------------------------------------------------------------------
# Multi-judge κ (Cohen's kappa, pairwise mean)


def multi_judge_kappa(judges_labels: Dict[str, Sequence[int]]) -> Dict[str, float]:
    """Compute pairwise Cohen's kappa between judges and return mean / min.

    judges_labels: {judge_name → list of labels for the same items}.
    """
    from sklearn.metrics import cohen_kappa_score  # local import to avoid hard dep

    names = list(judges_labels.keys())
    pairwise: Dict[Tuple[str, str], float] = {}
    for a, b in combinations(names, 2):
        ka = np.asarray(judges_labels[a])
        kb = np.asarray(judges_labels[b])
        n = min(len(ka), len(kb))
        if n < 2:
            pairwise[(a, b)] = float("nan")
            continue
        pairwise[(a, b)] = float(cohen_kappa_score(ka[:n], kb[:n]))
    valid = [v for v in pairwise.values() if not math.isnan(v)]
    return {
        "pairwise": {f"{a}|{b}": v for (a, b), v in pairwise.items()},
        "mean": float(np.mean(valid)) if valid else float("nan"),
        "min": float(np.min(valid)) if valid else float("nan"),
    }
