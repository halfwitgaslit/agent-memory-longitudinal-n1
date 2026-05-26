"""HONEST-Mem 15-field methods reporter (architecture/v1.md §4.7).

The 15 fields are derived from the HMA-1 adversarial-review-driven
methodology and adapted to the longitudinal n=1 agent-memory eval substrate.

Each field is auto-populated from:
- eval/experimental_constants.py (locked constants)
- eval/pre_registration.py (frozen hash)
- distillation/data/.spend_ledger.json (cumulative spend by probe)
- results JSONL (counts, latencies, judge κ, etc.)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


HONEST_MEM_FIELDS = [
    "1_substrate",
    "2_population_of_interest",
    "3_preregistration",
    "4_randomization_scheme",
    "5_arms",
    "6_metrics",
    "7_statistical_procedures",
    "8_multi_judge_protocol",
    "9_effect_sizes",
    "10_decontamination_certification",
    "11_spend_ledger",
    "12_ablation_table_pointer",
    "13_negative_controls_outcomes",
    "14_datasheet_pointer",
    "15_limitations",
]


def render_honest_mem_methods(
    constants: Dict[str, Any],
    preregistration_hash: str,
    spend_ledger: Optional[Dict[str, Any]] = None,
    results_summary: Optional[Dict[str, Any]] = None,
    judge_kappa_summary: Optional[Dict[str, Any]] = None,
    datasheet_path: str = "phd/paper/datasheet.md",
    paper_table_paths: Optional[Dict[str, str]] = None,
    limitations: Optional[str] = None,
) -> str:
    """Render the methods section as markdown."""
    c = constants
    spend = spend_ledger or {}
    res = results_summary or {}
    kappa = judge_kappa_summary or {}
    paths = paper_table_paths or {}

    total_spend = spend.get("total_usd", 0.0)
    by_probe = spend.get("by_probe", {})
    n_sessions_processed = res.get("n_processed", "TBD-Phase2")

    md = f"""## Methods (HONEST-Mem 15-field auto-generated)

### 1. Substrate

The corpus comprises **{n_sessions_processed}** real coding-CLI sessions collected
between 2026-04 and 2026-05 from a single developer's `roomd` project across:

- Claude Code: ~/.claude/projects/-Users-aiSandbox-github-roomd*/*.jsonl
  (176 JSONL files across 42 project directories: main + 32 worktrees + sandboxes
  + 6 agent-orchestration + 7 memory + 10 RCAEval-benchmarking)
- Codex: ~/.codex/sessions/**/*.jsonl + ~/.codex/archived_sessions/*.jsonl
  (924 JSONL files; filtered to those whose session_meta.cwd contains 'roomd')

Adapters at `phd/code/adapters/{{claude_code_jsonl.py, codex_rollout_jsonl.py}}`
parse both into a unified Pydantic `Turn` schema (v1.0). Lossless round-trip
preservation of metadata is asserted by 34 pytest tests on real fixtures.

### 2. Population of interest

**N = 1.** The subject is the developer who built the `roomd` corpus
(anonymized as `vector`; consent self-given 2026-05-25). All sessions are
the subject's own real work; no synthetic substitution. The n=1 design is
adapted from medical N-of-1 (Guyatt 1986; Kravitz 2021; CONSORT N-of-1 2015)
with an irreversibility-adaptation specific to LLM agent memory (no washout
possible). The methodology lineage is SCED (Kazdin 2011; Kratochwill 2010;
WWC standards 2013).

### 3. Pre-registration

The pre-registration hash (`sha256(eval/experimental_constants.py canonical JSON)`):

```
{preregistration_hash}
```

Committed to git at the time of Phase 2 deployment kickoff. The commit
timestamp IS the priority lock; subsequent arXiv pre-print follows venue
submission. See `phd/preregistration/v1.md` for the full document.

### 4. Randomization scheme

Per-task arm assignment uses a **Latin-square switchback** stratified by
(`time_of_day_bucket`, `project`), with seed = first 8 bytes of
SHA-256(pre-registration commit hash). Reference: arxiv 2506.12654 RBSD
switchback design.

Time-of-day buckets: {", ".join(c["design"]["time_of_day_buckets"])}.
The switchback rotates arm assignment within each (bucket, project) cell
to control for the documented 20% variance contribution from time-of-day.

### 5. Arms

Six arms ({c["n_arms"]} total) with backend versions explicitly pinned:

""" + "\n".join(
        f"- **`{arm}`**: {c['arm_descriptions'][arm]}" for arm in c["arms"]
    ) + f"""

Each arm is wrapped behind the `MemoryBackend` ABC (`phd/code/memory/base.py`)
with identical `add` / `search` / `inspect` / `decay_step` / `lifecycle_promote` /
`clear` surface. Per-backend health is tracked in `inspect()` output and
recorded into the eval JSONL.

### 6. Metrics

**Primary:**
""" + "\n".join(f"- `{m}`" for m in c["metrics"]["primary"]) + """

**Secondary:**
""" + "\n".join(f"- `{m}`" for m in c["metrics"]["secondary"]) + f"""

Operational definitions live in `phd/code/eval/metrics.py`. The reminder-count
metric uses a 6-pattern regex with manual spot-check on 10% of sessions
(documented in the validation appendix). Token-spend is approximated from the
JSONL `usage` fields per published per-model pricing.

### 7. Statistical procedures

- **Pairwise test:** {c["statistical_procedures"]["pairwise_test"]}
- **α (raw):** {c["statistical_procedures"]["alpha_raw"]}
- **α (Bonferroni-corrected for 15 pairwise comparisons):** {c["statistical_procedures"]["alpha_corrected"]:.6f}
- **Bootstrap:** {c["statistical_procedures"]["bootstrap_B"]} replicates, {c["statistical_procedures"]["bootstrap_ci_method"]} confidence intervals
- **Effect sizes:** {", ".join(c["statistical_procedures"]["effect_sizes"])}
- **Variance reduction:** {c["statistical_procedures"]["variance_reduction"]}

Implementations: `phd/code/eval/stats.py`. Versions: scipy {{scipy.__version__}},
numpy {{numpy.__version__}}, scikit-learn {{sklearn.__version__}}.

### 8. Multi-judge protocol

For all LLM-graded metrics (notably `prior_knowledge_recall`):

- **N judges:** {c["multi_judge"]["n_judges"]}
- **Judges:** {", ".join(c["multi_judge"]["judges"])}
- **κ threshold:** {c["multi_judge"]["kappa_threshold"]} (pairwise Cohen's κ, all pairs ≥ threshold required)
- **Permutation averaging:** {c["multi_judge"]["permutation_averaging"]} (N permutations = {c["multi_judge"]["permutation_N"]})

Observed κ summary: {json.dumps(kappa, default=str)[:400]}.

### 9. Effect sizes

For every pairwise comparison we report both **Cohen's d** (parametric) and
**Cliff's δ** (non-parametric). For paired observations (same Vector task
exposed to different arms — separate task instances per pre-reg), Cohen's d
is computed paired.

### 10. Decontamination certification

{c["decontamination"]["policy"]}

For PDDC parameter fitting: {c["decontamination"]["PDDC_calibration_split"]}.
The held-out 30% trajectories are used ONLY for model selection
(parameter-set CV); no metric or analysis decision uses held-out data
post-locking of the pre-registration.

### 11. Spend ledger

- **Cumulative subscription spend:** ${total_spend:.2f} (cap: ${c["spend_caps"]["phase_2_cap_usd"]} Phase-2; ${c["spend_caps"]["session_cap_usd"]} session)
- **By-probe breakdown:** {json.dumps({k: f"${v:.3f}" for k, v in by_probe.items()}, indent=2) if by_probe else "(none yet)"}

All LLM calls billed against subscription via `claude -p`; no separate API
keys consumed for Anthropic. OpenAI calls (Codex) billed via OpenAI Plus.

### 12. Ablation table

See {paths.get("ablation_table", "phd/paper/tables/ablation.md")} for the full
ablation matrix:

- full system (mem0 + PDDC + GCMP)
- vs full system minus PDDC (FSRS-6 defaults)
- vs full system minus GCMP (full inheritance, no cross-query)
- vs full system minus decay (no calibration; static scores)
- vs default Mem0 (no PDDC, no GCMP)
- vs null baseline

### 13. Negative-controls outcomes

The pre-registered negative controls are:

1. **`null` arm**: no memory retrieval. Any positive arm must beat null on at
   least one primary metric to claim utility.
2. **`random` arm**: returns k random previously-added memories. Any arm
   losing to random is anti-helpful (failure mode: bad embeddings on small
   corpora).

Results are reported in `{paths.get("negative_controls", "phd/paper/tables/negative_controls.md")}`.

### 14. Datasheet

See `{datasheet_path}` (Gebru et al. 2021 format). The corpus is released
under {c["reproducibility"]["license_corpus"]} on paper acceptance, with
Croissant metadata, full provenance, and an anonymization audit.

### 15. Limitations

{limitations or """- **N = 1 generalizability.** Single-subject results do not generalize to
  population-level claims; this is by design (SCED/N-of-1). Cross-subject
  generalizability requires replication on additional subjects.
- **Subject-internal autocorrelation.** Time-series within a single subject
  exhibit autocorrelation that limits the independence assumption of some
  statistical tests; we use MADCovar variance reduction and the within-subject
  Wilcoxon test as the most appropriate response.
- **Memory carryover.** Although we operate in isolated-mode for primary
  reports, complete elimination of carryover across arms is impossible (this
  is the irreversibility-adaptation problem documented in §3.3 of the paper).
- **Backend-environment differences.** Letta requires a server (in Phase 1
  smoke this was unavailable); arms with environmental dependencies may be
  reported as SKIPPED with documented rationale.
- **Reminder-count regex.** The `had_to_remind_count` metric uses a regex that
  may miss paraphrases. We spot-check 10% of sessions and report agreement.
- **OSS package velocity.** Mem0, Letta, Hindsight, and Cognee are actively
  shipping. We pin versions in `requirements_frozen.txt` and document the
  exact build in §5 above.
"""}
"""
    return md
