"""Eval harness — pre-registered, arm-randomized, switchback-design longitudinal n=1 eval.

See architecture/v1.md §4.6.
"""

from .experimental_constants import EXPERIMENTAL_CONSTANTS, freeze_constants_hash
from .metrics import MetricSet, compute_session_metrics
from .stats import (
    bonferroni_correct,
    bootstrap_ci_bca,
    cliff_delta,
    cohens_d,
    mad_covar,
    pairwise_wilcoxon,
)
from .pre_registration import generate_preregistration, write_preregistration

__all__ = [
    "EXPERIMENTAL_CONSTANTS",
    "MetricSet",
    "bonferroni_correct",
    "bootstrap_ci_bca",
    "cliff_delta",
    "cohens_d",
    "compute_session_metrics",
    "freeze_constants_hash",
    "generate_preregistration",
    "mad_covar",
    "pairwise_wilcoxon",
    "write_preregistration",
]
