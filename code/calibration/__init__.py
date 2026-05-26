"""Per-Deployment Decay Calibration (PDDC).

Extends FSRS-6 (Free Spaced Repetition Scheduler, Ye et al. 2024; Anki
production since 2022) by replacing the binary recall signal with a
multi-dimensional agent-task-success signal.

See architecture/v1.md §4.3 and the FSRS-6 reference:
https://github.com/open-spaced-repetition/fsrs4anki
"""

from .decay import (
    PDDC_DEFAULT_PARAMS_22,
    FSRS6_DEFAULT_PARAMS_21,
    MemoryState,
    MultiDimSignal,
    PDDCalibrator,
    fsrs6_retrievability,
    fsrs6_stability_after_recall,
    pddc_loss,
)

__all__ = [
    "PDDC_DEFAULT_PARAMS_22",
    "FSRS6_DEFAULT_PARAMS_21",
    "MemoryState",
    "MultiDimSignal",
    "PDDCalibrator",
    "fsrs6_retrievability",
    "fsrs6_stability_after_recall",
    "pddc_loss",
]
