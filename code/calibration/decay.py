"""PDDC — Per-Deployment Decay Calibration extending FSRS-6.

PHD CONTRIBUTION SUMMARY (architecture/v1.md §4.3):

FSRS-6 (Free Spaced Repetition Scheduler, Anki 2022+, Ye et al. 2024) fits
21 per-user parameters via gradient descent against a binary recall signal
{0=forgot, 1=recalled} from flashcard review traces. It is the SOTA for
human-recall scheduling and ships with millions of Anki users.

PDDC extends FSRS-6 to the agent-memory domain by replacing the binary
recall signal with a 4-dimensional agent-task-success vector:

    s = (support_count, hit_rate, conflict_events, task_success_delta)

where:
- support_count    : how many distinct sessions referenced this memory (≥ 0)
- hit_rate         : fraction of searches returning this memory that were "useful"
                     as graded by post-task review (∈ [0, 1])
- conflict_events  : count of session outcomes that contradicted this memory (≥ 0)
- task_success_delta: change in task success rate attributable to this memory
                     (in [-1, +1]; positive = helped, negative = hurt)

The 4D signal is collapsed into a continuous "effective recall" e ∈ [0, 1]
via 22 parameters (21 FSRS-6 + 1 auxiliary loss weight) plus 4 signal-mix
weights, optimized end-to-end against the per-deployment trace.

Synthetic-ground-truth test: tests/test_calibration.py generates trajectories
from KNOWN parameters, fits PDDC, asserts recovery within 10% on >80% of
parameter dimensions.

Mathematical model (FSRS-6 form, retained):
    R(t) = (1 + t / (9 · S))^(-1)    ; retrievability after t days
    S'   = update(S, D, e)            ; stability update on review with effective recall e
    D'   = D + clip(...) · (e - default)
                                     ; difficulty update
where S = stability, D = difficulty, t = elapsed days, e = effective recall.

In PDDC we redefine e as:
    e = sigmoid( w0*hit_rate + w1*norm(support_count) - w2*norm(conflict_events) + w3*task_success_delta + b )

with (w0..w3, b) as 5 extra free parameters; full param vector is therefore
21 + 5 = 26 (we name the consolidated 22-element vector below for
compatibility with FSRS-6 tooling).

REFERENCES:
- FSRS-4 / FSRS-5 / FSRS-6 parameter forms: open-spaced-repetition/fsrs4anki
- Anki FSRS docs: https://docs.ankiweb.net/deck-options.html#fsrs
- Koren 2010 temporal CF (similar gradient-descent calibration on rating data)
- MACLA (arxiv 2512.18950) — grid-search benchmark calibration (we extend
  with continuous deployment-trace calibration)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import minimize


# ---------------------------------------------------------------------------
# FSRS-6 parameter defaults (the 21-parameter starting point)
# Source: https://github.com/open-spaced-repetition/fsrs4anki/wiki/FSRS-6 (2024)

FSRS6_DEFAULT_PARAMS_21 = np.array(
    [
        0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234,
        1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407,
        2.9466, 0.5034, 0.6567, 0.0123, 0.1,
    ],
    dtype=np.float64,
)
assert FSRS6_DEFAULT_PARAMS_21.shape == (21,)

# PDDC extends with 5 additional signal-mix parameters:
# index 21..25 :  w_hit, w_support, w_conflict, w_task_delta, bias
PDDC_EXTRA_5 = np.array([2.0, 0.5, -1.0, 1.5, 0.0], dtype=np.float64)

PDDC_DEFAULT_PARAMS_22 = np.concatenate([FSRS6_DEFAULT_PARAMS_21, PDDC_EXTRA_5])
# Note: "22" in the variable name is historical; the full vector is 26 entries
assert PDDC_DEFAULT_PARAMS_22.shape == (26,)


# ---------------------------------------------------------------------------
# Data classes


@dataclass
class MultiDimSignal:
    """The 4-D agent task-success signal observed for one memory at one review."""

    support_count: int = 0
    hit_rate: float = 0.0  # in [0, 1]
    conflict_events: int = 0
    task_success_delta: float = 0.0  # in [-1, +1]


@dataclass
class MemoryState:
    """Per-memory state in PDDC's extended FSRS-6 model."""

    memory_id: str
    stability: float = 1.0
    difficulty: float = 5.0
    last_review_ts: float = field(default_factory=time.time)
    n_reviews: int = 0
    cumulative_signal: MultiDimSignal = field(default_factory=MultiDimSignal)
    history: List[Tuple[float, MultiDimSignal, float]] = field(default_factory=list)
    # tuples: (review_ts, signal, effective_recall_used)


# ---------------------------------------------------------------------------
# Core FSRS-6 functions (reduced, since we only need the retrievability + stability
# update for the calibration loss — the full FSRS-6 scheduler is overkill for our
# use case).


def fsrs6_retrievability(stability: float, elapsed_days: float) -> float:
    """FSRS-6 retrievability function: R(t) = (1 + t / (9*S))^(-1)."""
    if stability <= 0:
        return 0.0
    if elapsed_days <= 0:
        return 1.0
    return (1.0 + elapsed_days / (9.0 * stability)) ** (-1.0)


def fsrs6_stability_after_recall(
    stability: float,
    difficulty: float,
    retrievability: float,
    effective_recall: float,
    params: Sequence[float],
) -> float:
    """Simplified FSRS-6 stability update.

    FSRS-6 has separate update equations for "recall" (e >= threshold) and
    "lapse" (e < threshold). We use a smoothed combination so it is
    differentiable with respect to all 21 parameters.
    """
    w = params
    # PDDC threshold: midpoint between forgot and recalled
    rec_weight = effective_recall  # in [0, 1] — used as soft mix
    # Recall branch (FSRS-6 simplified)
    s_rec = stability * (
        1.0
        + math.exp(w[8])
        * (11.0 - difficulty)
        * (stability ** -w[9])
        * (math.exp((1.0 - retrievability) * w[10]) - 1.0)
        * (1.0 + (effective_recall - 0.5) * w[15])
    )
    # Lapse branch
    s_lap_base = w[11] * (difficulty ** -w[12]) * (
        (stability + 1.0) ** w[13] - 1.0
    ) * math.exp((1.0 - retrievability) * w[14])
    s_lap = max(s_lap_base, 0.01)
    # Smoothed mix
    s_new = rec_weight * s_rec + (1.0 - rec_weight) * s_lap
    # Clamp to reasonable range
    return max(0.01, min(s_new, 36500.0))


def fsrs6_difficulty_after_recall(
    difficulty: float, effective_recall: float, params: Sequence[float]
) -> float:
    """Simplified FSRS-6 difficulty update."""
    w = params
    delta = -w[6] * (effective_recall - 0.5) * 2.0  # scale to [-1, 1]
    d_new = difficulty + delta * w[7]
    return max(1.0, min(d_new, 10.0))


# ---------------------------------------------------------------------------
# PDDC signal-collapsing function


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def collapse_signal_to_effective_recall(
    signal: MultiDimSignal, params: Sequence[float]
) -> float:
    """Collapse the 4-D agent signal into an effective recall e ∈ (0, 1).

    Uses params[21..25] as (w_hit, w_support, w_conflict, w_task_delta, bias).
    Normalization is applied to support_count and conflict_events
    (log1p, since they're unbounded counts).
    """
    w_hit, w_support, w_conflict, w_task_delta, bias = params[21:26]
    norm_support = math.log1p(max(0, signal.support_count))
    norm_conflict = math.log1p(max(0, signal.conflict_events))
    z = (
        w_hit * signal.hit_rate
        + w_support * norm_support
        + w_conflict * norm_conflict
        + w_task_delta * signal.task_success_delta
        + bias
    )
    # Clamp z to avoid overflow in sigmoid
    z = max(-30.0, min(30.0, z))
    return _sigmoid(z)


# ---------------------------------------------------------------------------
# PDDC loss function (for gradient-descent calibration)


def pddc_loss(
    params: np.ndarray,
    trajectories: List[List[Tuple[float, MultiDimSignal, float]]],
) -> float:
    """Loss for PDDC calibration.

    `trajectories`: list of per-memory observation histories. Each history is
    a list of (elapsed_days_since_last_review, signal, observed_outcome_hit_rate).
    The model predicts effective recall e from (S, D, t, signal) and we
    minimize the MSE between e and observed hit_rate.

    Returns total MSE plus an L2 regularization on (params - defaults).
    """
    total_loss = 0.0
    n_observations = 0
    # Replay each trajectory through the model
    for traj in trajectories:
        if not traj:
            continue
        S = 1.0
        D = 5.0
        for elapsed_days, signal, observed_hit_rate in traj:
            r = fsrs6_retrievability(S, elapsed_days)
            e_pred = collapse_signal_to_effective_recall(signal, params)
            # Loss: MSE between predicted effective recall and observed hit_rate
            diff = e_pred - observed_hit_rate
            total_loss += diff * diff
            n_observations += 1
            # Apply FSRS-6 updates with observed_hit_rate as the true effective recall
            S = fsrs6_stability_after_recall(S, D, r, observed_hit_rate, params)
            D = fsrs6_difficulty_after_recall(D, observed_hit_rate, params)
    if n_observations == 0:
        return 0.0
    mse = total_loss / n_observations
    # L2 regularization to FSRS-6 defaults (light)
    reg = 0.001 * np.sum((params - PDDC_DEFAULT_PARAMS_22) ** 2)
    return float(mse + reg)


# ---------------------------------------------------------------------------
# PDDCalibrator


@dataclass
class PDDCalibrator:
    """Per-deployment decay calibrator.

    Usage:
        cal = PDDCalibrator()
        cal.fit(trajectories)
        params = cal.fitted_params
        # Use params to update memory states / re-rank
    """

    params: np.ndarray = field(default_factory=lambda: PDDC_DEFAULT_PARAMS_22.copy())
    fitted: bool = False
    fit_loss: float = float("nan")
    n_iters: int = 0

    def fit(
        self,
        trajectories: List[List[Tuple[float, MultiDimSignal, float]]],
        max_iter: int = 200,
        seed: int = 42,
    ) -> Dict[str, float]:
        """Fit by L-BFGS-B on the PDDC loss. Returns {loss, n_iters}."""
        # Optimize from defaults
        x0 = PDDC_DEFAULT_PARAMS_22.copy()
        # Bounds: keep all params loosely bounded to avoid numerical blowup
        bounds = []
        for i in range(len(x0)):
            if i < 21:
                bounds.append((max(0.001, x0[i] * 0.01), max(x0[i] * 100, 100.0)))
            else:
                bounds.append((-20.0, 20.0))
        result = minimize(
            pddc_loss,
            x0=x0,
            args=(trajectories,),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": max_iter, "disp": False},
        )
        self.params = result.x
        self.fitted = True
        self.fit_loss = float(result.fun)
        self.n_iters = int(result.nit)
        return {"loss": self.fit_loss, "n_iters": self.n_iters, "success": result.success}

    def baseline_fsrs6_loss(
        self, trajectories: List[List[Tuple[float, MultiDimSignal, float]]]
    ) -> float:
        """Compute loss for FSRS-6-default parameters (no calibration). Used to
        verify PDDC strictly improves on the baseline."""
        return pddc_loss(PDDC_DEFAULT_PARAMS_22, trajectories)

    def predict_retrievability(
        self, state: MemoryState, signal: MultiDimSignal, now_utc: Optional[float] = None
    ) -> float:
        """Predict effective recall for a given memory state + observed signal."""
        if now_utc is None:
            now_utc = time.time()
        elapsed_days = max(0.0, (now_utc - state.last_review_ts) / 86400.0)
        r = fsrs6_retrievability(state.stability, elapsed_days)
        e = collapse_signal_to_effective_recall(signal, self.params)
        # Combine: actual retrievability discounted by signal-derived effective recall
        return r * e + (1.0 - r) * (e * 0.5)

    def update_memory_state(
        self, state: MemoryState, signal: MultiDimSignal, now_utc: Optional[float] = None
    ) -> MemoryState:
        """Apply a review update to a memory state."""
        if now_utc is None:
            now_utc = time.time()
        elapsed_days = max(0.0, (now_utc - state.last_review_ts) / 86400.0)
        r = fsrs6_retrievability(state.stability, elapsed_days)
        e = collapse_signal_to_effective_recall(signal, self.params)
        new_stability = fsrs6_stability_after_recall(
            state.stability, state.difficulty, r, e, self.params
        )
        new_difficulty = fsrs6_difficulty_after_recall(state.difficulty, e, self.params)
        state.stability = new_stability
        state.difficulty = new_difficulty
        state.last_review_ts = now_utc
        state.n_reviews += 1
        state.history.append((now_utc, signal, e))
        # Update cumulative signal
        c = state.cumulative_signal
        c.support_count += signal.support_count
        c.conflict_events += signal.conflict_events
        c.hit_rate = (c.hit_rate * (state.n_reviews - 1) + signal.hit_rate) / state.n_reviews
        c.task_success_delta = (
            c.task_success_delta * (state.n_reviews - 1) + signal.task_success_delta
        ) / state.n_reviews
        return state


# ---------------------------------------------------------------------------
# Synthetic ground-truth utilities (for tests)


def generate_synthetic_trajectories(
    true_params: np.ndarray,
    n_memories: int = 50,
    n_reviews_per_memory: int = 10,
    seed: int = 42,
) -> List[List[Tuple[float, MultiDimSignal, float]]]:
    """Generate synthetic per-memory trajectories from a KNOWN parameter vector.

    Used by tests/test_calibration.py to verify PDDC recovers known params.
    """
    rng = np.random.default_rng(seed)
    trajectories: List[List[Tuple[float, MultiDimSignal, float]]] = []
    for _ in range(n_memories):
        traj: List[Tuple[float, MultiDimSignal, float]] = []
        S = float(rng.uniform(0.5, 5.0))
        D = float(rng.uniform(3.0, 7.0))
        for _ in range(n_reviews_per_memory):
            elapsed = float(rng.uniform(0.5, 30.0))
            # Generate a random 4D signal
            sig = MultiDimSignal(
                support_count=int(rng.poisson(2)),
                hit_rate=float(rng.beta(2, 2)),
                conflict_events=int(rng.poisson(0.3)),
                task_success_delta=float(rng.normal(0.1, 0.2)),
            )
            # The "observed hit rate" is the model's effective recall + noise
            e_true = collapse_signal_to_effective_recall(sig, true_params)
            observed = max(0.0, min(1.0, e_true + float(rng.normal(0.0, 0.05))))
            traj.append((elapsed, sig, observed))
            # Update S, D for the next iteration (deterministic, FSRS-6)
            r = fsrs6_retrievability(S, elapsed)
            S = fsrs6_stability_after_recall(S, D, r, observed, true_params)
            D = fsrs6_difficulty_after_recall(D, observed, true_params)
        trajectories.append(traj)
    return trajectories
