"""Tests for the eval harness: metrics, stats, and pre-registration."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.claude_code_jsonl import iter_roomd_sessions, parse_claude_code_session  # noqa: E402
from eval.experimental_constants import EXPERIMENTAL_CONSTANTS, freeze_constants_hash  # noqa: E402
from eval.metrics import (  # noqa: E402
    compute_session_metrics,
    count_reminders,
    count_retries,
    extract_token_spend_usd,
    time_of_day_bucket,
)
from eval.pre_registration import generate_preregistration, write_preregistration  # noqa: E402
from eval.stats import (  # noqa: E402
    bonferroni_correct,
    bootstrap_ci_bca,
    cliff_delta,
    cohens_d,
    mad_covar,
    pairwise_wilcoxon,
)


# ---------------------------------------------------------------------------
# Metrics tests


def test_time_of_day_bucket():
    # 2026-05-25T22:00:00Z = 18:00 ET (evening)
    import datetime
    ts = datetime.datetime(2026, 5, 25, 22, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
    bucket = time_of_day_bucket(ts, tz_offset_hours=-4.0)
    assert bucket == "evening_1800_0000"

    # 10:00 ET = 14:00 UTC → morning
    ts2 = datetime.datetime(2026, 5, 25, 14, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
    assert time_of_day_bucket(ts2, tz_offset_hours=-4.0) == "morning_0600_1200"


def test_metrics_on_real_session():
    samples = list(iter_roomd_sessions())
    if not samples:
        pytest.skip("No roomd sessions available")
    # Pick a medium-sized session
    samples.sort(key=lambda p: p.stat().st_size)
    p = samples[len(samples) // 2]
    session = parse_claude_code_session(p)
    metrics = compute_session_metrics(session, arm="null")
    assert metrics.session_id == session.session_id
    assert metrics.arm == "null"
    assert metrics.cli == "claude_code"
    assert metrics.n_turns >= 0
    # Time-of-day bucket should be one of the pre-registered buckets
    if metrics.time_of_day_bucket and metrics.time_of_day_bucket != "unknown":
        assert metrics.time_of_day_bucket in EXPERIMENTAL_CONSTANTS["design"]["time_of_day_buckets"]


def test_retry_count_and_reminders_run():
    """Just verify these don't crash on real sessions."""
    samples = list(iter_roomd_sessions())
    if not samples:
        pytest.skip("No roomd sessions available")
    samples.sort(key=lambda p: p.stat().st_size)
    p = samples[-1]  # largest
    session = parse_claude_code_session(p)
    r = count_retries(session)
    rem = count_reminders(session)
    assert isinstance(r, int) and r >= 0
    assert isinstance(rem, int) and rem >= 0


def test_token_spend_extraction_returns_finite_or_none():
    samples = list(iter_roomd_sessions())
    if not samples:
        pytest.skip("No roomd sessions available")
    samples.sort(key=lambda p: p.stat().st_size)
    p = samples[-1]
    session = parse_claude_code_session(p)
    spend = extract_token_spend_usd(session)
    assert spend is None or (isinstance(spend, float) and np.isfinite(spend))


# ---------------------------------------------------------------------------
# Stats tests


def test_pairwise_wilcoxon_basic():
    np.random.seed(0)
    data = {
        "null": np.random.normal(0.5, 0.1, 30).tolist(),
        "treat": np.random.normal(0.7, 0.1, 30).tolist(),  # better
        "harm": np.random.normal(0.3, 0.1, 30).tolist(),   # worse
    }
    result = pairwise_wilcoxon(data)
    assert ("null", "treat") in result
    assert ("harm", "null") in result or ("null", "harm") in result
    assert result[("null", "treat")]["n_pairs"] == 30
    # treat > null should produce a significant p-value
    assert result[("null", "treat")]["p_value"] < 0.05


def test_bonferroni_correct():
    p = [0.01, 0.02, 0.03, 0.04, 0.5]
    res = bonferroni_correct(p, alpha=0.05)
    assert len(res["p_corrected"]) == 5
    # alpha corrected = 0.05/5 = 0.01
    assert res["alpha_corrected"] == 0.01
    # First p-value (0.01) corrected to 0.05, which is just above 0.05 (not rejecting)
    # but with strict less-than, 0.05 < 0.05 is False
    assert res["reject_h0"][0] == False  # 0.05 is the boundary
    # 0.5 * 5 = 2.5 → capped at 1.0; certainly not significant
    assert res["reject_h0"][-1] == False


def test_bootstrap_ci_bca_normal():
    np.random.seed(42)
    data = np.random.normal(5.0, 1.0, 100)
    res = bootstrap_ci_bca(data, statistic_fn=np.mean, B=1000, seed=42)
    assert res["point_estimate"] == pytest.approx(float(np.mean(data)), abs=1e-6)
    # CI should contain the true mean (5.0)
    assert res["ci_low"] < 5.0 < res["ci_high"]
    # CI width should be reasonable
    width = res["ci_high"] - res["ci_low"]
    assert 0.05 < width < 1.0


def test_cohens_d_directional():
    a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    b = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    # b > a, so d should be strongly negative when computed as a - b
    d_paired = cohens_d(a, b, paired=True)
    assert d_paired < 0
    # And b vs a (positive)
    d_pos = cohens_d(b, a, paired=True)
    assert d_pos > 0


def test_cliff_delta_extremes():
    # All a > all b → delta = +1
    delta = cliff_delta([10, 11, 12], [1, 2, 3])
    assert delta == pytest.approx(1.0, abs=1e-6)
    # All a < all b → delta = -1
    delta = cliff_delta([1, 2, 3], [10, 11, 12])
    assert delta == pytest.approx(-1.0, abs=1e-6)


def test_mad_covar_reduces_variance_when_correlated():
    np.random.seed(0)
    x = np.random.uniform(0, 10, 100)
    y = 2.0 * x + np.random.normal(0, 0.5, 100)  # strongly correlated
    res = mad_covar(y, x)
    assert res["variance_reduction_pct"] > 0.0


# ---------------------------------------------------------------------------
# Pre-registration tests


def test_freeze_constants_hash_stable():
    h1 = freeze_constants_hash()
    h2 = freeze_constants_hash()
    assert h1 == h2  # deterministic
    assert len(h1) == 64  # SHA-256 hex


def test_generate_preregistration_includes_hash():
    text = generate_preregistration()
    h = freeze_constants_hash()
    assert h in text
    assert EXPERIMENTAL_CONSTANTS["study_id"] in text
    # All six arms must be mentioned
    for arm in EXPERIMENTAL_CONSTANTS["arms"]:
        assert arm in text


def test_write_preregistration(tmp_path):
    out = tmp_path / "v1.md"
    res = write_preregistration(output_path=out)
    assert res["path"] == str(out)
    assert out.exists()
    assert out.read_text().startswith("---")
    assert res["hash_sha256"] == freeze_constants_hash()
