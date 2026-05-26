"""LOCKED experimental constants. Any change requires a new pre-registration hash.

These are the pre-registered constants from architecture/v1.md §5. The file
hash (sha256) is the priority timestamp; do not edit casually.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPERIMENTAL_CONSTANTS = {
    "study_id": "PhD-LongN1-RoomD-v1",
    "study_title": "Pre-Registered N-of-1 Longitudinal Evaluation of Agent-Memory Frameworks on a Coding-CLI Substrate",
    "subject": {
        "n": 1,
        "subject_id": "vector",  # anonymized identifier; real identity disclosed in datasheet
        "consent": "obtained 2026-05-25; self-given",
    },
    "n_arms": 6,
    "arms": ["null", "random", "mem0", "letta", "hindsight", "cognee"],
    "arm_descriptions": {
        "null": "No memory retrieval. Negative control.",
        "random": "Returns k random previously-added memories. Negative control #2.",
        "mem0": "Mem0 v2.0.2 with fastembed BAAI/bge-small-en-v1.5 + qdrant on-disk + Anthropic Haiku fact extraction",
        "letta": "Letta 0.16.8 server (local) with default model/embedding stack",
        "hindsight": "hindsight-api 0.6.2 with embedded pg0 + LocalSTEmbeddings (MiniLM-L6) + Anthropic Haiku",
        "cognee": "cognee 1.1.0 with LanceDB + fastembed + Anthropic Haiku graph extraction",
    },
    "metrics": {
        "primary": [
            "task_success_binary",
            "task_success_5pt",
            "time_to_first_useful_output_s",
        ],
        "secondary": [
            "total_session_duration_s",
            "total_token_spend_usd",
            "retry_count",
            "had_to_remind_count",
            "prior_knowledge_recall",
            "conflict_events",
        ],
    },
    "statistical_procedures": {
        "pairwise_test": "Wilcoxon signed-rank (two-sided)",
        "alpha_raw": 0.05,
        "alpha_corrected": 0.05 / 15,  # Bonferroni for 15 pairwise comparisons (6 choose 2)
        "bootstrap_B": 10000,
        "bootstrap_ci_method": "BCa (Bias-Corrected and Accelerated)",
        "effect_sizes": ["cohens_d", "cliff_delta"],
        "variance_reduction": "MADCovar with time_of_day and project covariates",
    },
    "multi_judge": {
        "n_judges": 3,
        "judges": ["claude-sonnet-4-6", "claude-opus-4-7", "gpt-5"],
        "kappa_threshold": 0.7,
        "permutation_averaging": True,
        "permutation_N": 6,
    },
    "design": {
        "type": "Within-subject SCED/N-of-1 with arm-randomized switchback (per E2 RBSD arxiv 2506.12654)",
        "irreversibility_adaptation": "No washout; each arm's MemoryBackend is clear()'d between cells in isolated mode; an additional additive-mode pre-registration is also locked",
        "randomization_seed_source": "first 8 bytes of SHA-256(pre_registration_commit_hash)",
        "n_target_sessions_total": 120,
        "n_min_sessions_per_arm_cell": 5,
        "task_unit_definition": "A coherent user goal pursued end-to-end in one or more contiguous sessions; identified ad-hoc by the subject and logged via phd_mem record-task",
        "stratification": ["time_of_day_bucket", "project"],
        "time_of_day_buckets": ["morning_0600_1200", "afternoon_1200_1800", "evening_1800_0000", "night_0000_0600"],
        "switchback_design": "Latin square per stratum cell",
    },
    "decontamination": {
        "policy": "The roomd corpus is the substrate; no held-out test set is used for tuning model parameters or PDDC.",
        "PDDC_calibration_split": "70% in-deployment / 30% held-out for model selection only",
    },
    "llm_backbones_in_use": ["claude-sonnet-4-5", "claude-sonnet-4-6", "claude-opus-4-7", "gpt-5"],
    "embeddings_locked": {
        "initial": "BAAI/bge-small-en-v1.5 (fastembed)",
        "phase_2_target": "Qwen3-Embedding-8B-MLX (M4 Max optimized)",
    },
    "vector_stores_locked": {
        "initial": "qdrant on-disk",
        "comparison": "LanceDB (Cognee uses it natively)",
    },
    "spend_caps": {
        "phase_1_cap_usd": 100,
        "phase_2_cap_usd": 300,
        "session_cap_usd": 500,
    },
    "reproducibility": {
        "license_system": "MIT",
        "license_corpus": "CC-BY-NC (per E3 dataset-ethics consolidated)",
        "datasheet": "phd/paper/datasheet.md",
        "model_card": "phd/paper/model_card.md (when applicable)",
        "frozen_requirements": "phd/code/requirements_frozen.txt",
        "preregistration_path": "phd/preregistration/v1.md",
        "honest_mem_methods_path": "phd/paper/methods_honest_mem.md",
    },
    "version": "1.0",
    "locked_at_utc": "2026-05-25T22:00:00Z",
}


def freeze_constants_hash() -> str:
    """Return a stable SHA-256 over the constants dict; this hash IS the priority timestamp."""
    s = json.dumps(EXPERIMENTAL_CONSTANTS, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
