"""HONEST-Mem 15-field reproducibility-grade methods reporting.

Auto-generates the methods section of the paper from run metadata. The
"HONEST-Mem" name is borrowed from the HMA-1 adversarial-review-driven
methodology (see HMA-1 root: distillation/code/hma_audit_mini/) and adapted
for the agent-memory eval substrate.
"""

from .honest_mem import HONEST_MEM_FIELDS, render_honest_mem_methods

__all__ = ["HONEST_MEM_FIELDS", "render_honest_mem_methods"]
