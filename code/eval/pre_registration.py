"""Pre-registration document generation + git-commit-based priority lock.

The pre-registration commit hash IS the priority timestamp. This module:
1. Reads the locked experimental_constants
2. Hashes them (SHA-256) — `freeze_constants_hash()`
3. Renders a pre-registration markdown document
4. Writes it to `phd/preregistration/v1.md` with the hash in the frontmatter
5. (Manually) runs `git add ... && git commit -m "PRE-REGISTRATION HASH <hash>"`
   — done OUTSIDE this script for traceability.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Dict, Optional

from .experimental_constants import EXPERIMENTAL_CONSTANTS, freeze_constants_hash


def generate_preregistration(
    constants: Optional[Dict] = None,
    extra_metadata: Optional[Dict] = None,
) -> str:
    """Render the pre-registration markdown text. Pure function."""
    c = constants or EXPERIMENTAL_CONSTANTS
    h = freeze_constants_hash()
    extra = extra_metadata or {}
    md = f"""---
study_id: {c["study_id"]}
hash_sha256: {h}
generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
{("git_commit: " + str(extra["git_commit"])) if extra.get("git_commit") else ""}
{("osf_url: " + str(extra["osf_url"])) if extra.get("osf_url") else ""}
---

# Pre-Registration v1

**Study ID:** `{c["study_id"]}`
**Title:** {c["study_title"]}
**Locked at:** {c["locked_at_utc"]}
**Hash (sha256 of experimental_constants):** `{h}`

> This pre-registration is locked. Any change requires a new pre-registration
> commit with a new hash. The git commit timestamp IS the priority timestamp;
> arXiv pre-print follows submission.

## 1. Subject

- n = {c["subject"]["n"]}
- subject_id: `{c["subject"]["subject_id"]}` (anonymized identifier; consent {c["subject"]["consent"]})

## 2. Hypotheses

**Primary H1:** At least one of {{mem0, letta, hindsight, cognee}} arms produces
a statistically and clinically significant improvement on `task_success_binary`
over the null-arm baseline, at α (corrected) = {c["statistical_procedures"]["alpha_corrected"]:.6f},
under the within-subject Wilcoxon signed-rank test.

**Secondary H2:** Per-deployment decay calibration (PDDC) yields lower out-of-sample
prediction error on memory utility than FSRS-6 default parameters transferred from
flashcard data, on 30% held-out trajectories.

**Secondary H3:** Governed cross-worktree memory propagation (GCMP) with default
policy thresholds yields more useful (`prior_knowledge_recall`) cross-worktree
hits than full inheritance (Letta MemFS default behavior), under multi-judge
labeling with κ ≥ {c["multi_judge"]["kappa_threshold"]}.

## 3. Arms

| Arm | Description |
|---|---|
""" + "\n".join(
        f"| `{arm}` | {c['arm_descriptions'][arm]} |"
        for arm in c["arms"]
    ) + f"""

Number of arms: **{c["n_arms"]}**

## 4. Metrics

**Primary metrics:**
""" + "\n".join(f"- `{m}`" for m in c["metrics"]["primary"]) + f"""

**Secondary metrics:**
""" + "\n".join(f"- `{m}`" for m in c["metrics"]["secondary"]) + f"""

## 5. Statistical procedures

- Pairwise test: **{c["statistical_procedures"]["pairwise_test"]}**
- α (raw): {c["statistical_procedures"]["alpha_raw"]}
- α (Bonferroni-corrected for 15 pairwise comparisons): **{c["statistical_procedures"]["alpha_corrected"]:.6f}**
- Bootstrap: **{c["statistical_procedures"]["bootstrap_B"]}** replicates, **{c["statistical_procedures"]["bootstrap_ci_method"]}** CI
- Effect sizes: {", ".join(c["statistical_procedures"]["effect_sizes"])}
- Variance reduction: **{c["statistical_procedures"]["variance_reduction"]}**

## 6. Multi-judge protocol

- N_judges: {c["multi_judge"]["n_judges"]}
- Judges: {", ".join(c["multi_judge"]["judges"])}
- κ threshold: {c["multi_judge"]["kappa_threshold"]}
- Permutation averaging: {c["multi_judge"]["permutation_averaging"]}
  (N permutations: {c["multi_judge"]["permutation_N"]})

## 7. Design

- Type: **{c["design"]["type"]}**
- Irreversibility adaptation: **{c["design"]["irreversibility_adaptation"]}**
- Randomization seed source: `{c["design"]["randomization_seed_source"]}`
- N target sessions: **{c["design"]["n_target_sessions_total"]}** ({c["design"]["n_min_sessions_per_arm_cell"]} min per arm cell)
- Task unit: {c["design"]["task_unit_definition"]}
- Stratification: {", ".join(c["design"]["stratification"])}
- Time-of-day buckets: {", ".join(c["design"]["time_of_day_buckets"])}
- Switchback design: {c["design"]["switchback_design"]}

## 8. Decontamination

- {c["decontamination"]["policy"]}
- PDDC calibration split: {c["decontamination"]["PDDC_calibration_split"]}

## 9. LLM backbones in use

{", ".join(f"`{m}`" for m in c["llm_backbones_in_use"])}

## 10. Embeddings + vector stores

- Initial embedding: `{c["embeddings_locked"]["initial"]}`
- Phase 2 target embedding: `{c["embeddings_locked"]["phase_2_target"]}`
- Initial vector store: `{c["vector_stores_locked"]["initial"]}`
- Comparison vector store: `{c["vector_stores_locked"]["comparison"]}`

## 11. Spend caps (pre-registered)

- Phase 1 cap: ${c["spend_caps"]["phase_1_cap_usd"]}
- Phase 2 cap: ${c["spend_caps"]["phase_2_cap_usd"]}
- Session cap: ${c["spend_caps"]["session_cap_usd"]}

## 12. Reproducibility commitments

- System license: {c["reproducibility"]["license_system"]}
- Corpus license: {c["reproducibility"]["license_corpus"]}
- Datasheet: `{c["reproducibility"]["datasheet"]}`
- Frozen requirements: `{c["reproducibility"]["frozen_requirements"]}`
- Pre-registration path: `{c["reproducibility"]["preregistration_path"]}`
- HONEST-Mem methods: `{c["reproducibility"]["honest_mem_methods_path"]}`

## 13. Locked constants

The complete locked constants are serialized in
`eval/experimental_constants.py`. The SHA-256 hash above is computed over
the canonical JSON serialization of this dict.

## 14. Procedural commitments

1. **No data analysis (post-Phase-2) without first locking this pre-registration via git commit.**
2. **No metric definitions change after the commit.** If a defect is discovered,
   the eval is re-run from scratch with the new (re-registered) constants.
3. **All results are reported.** Null and disconfirming findings are reported
   with the same rigor as confirming findings.
4. **The corpus is released** under {c["reproducibility"]["license_corpus"]} on
   acceptance of the paper at the target venue, with the datasheet and full
   reproduction package.

---

*This pre-registration was generated by `eval/pre_registration.py` from the
locked `eval/experimental_constants.py`. To verify integrity, recompute the
hash via:*

```bash
python3 -c "from eval.experimental_constants import freeze_constants_hash; print(freeze_constants_hash())"
# expected: {h}
```
"""
    return md


def write_preregistration(
    output_path: str | Path = "/Users/aiSandbox/github/claude_can_do_anything/distillation/phd/preregistration/v1.md",
    extra_metadata: Optional[Dict] = None,
) -> Dict:
    """Render and write the pre-registration markdown. Returns a summary dict."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = generate_preregistration(extra_metadata=extra_metadata)
    p.write_text(text)
    h = freeze_constants_hash()
    return {
        "path": str(p),
        "hash_sha256": h,
        "bytes_written": len(text.encode("utf-8")),
    }


if __name__ == "__main__":
    res = write_preregistration()
    print(json.dumps(res, indent=2))
