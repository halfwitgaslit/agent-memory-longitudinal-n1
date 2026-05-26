# Reproducibility container for the PhD Phase 1 build.
#
# Usage:
#   docker build -t phd-phase1 -f Dockerfile .
#   docker run --rm phd-phase1 make smoke
#
# Targets supported inside the container:
#   - make smoke
#   - make preregister
#   - make paper        (renders v0.1 PDF)
#
# NOT supported inside the container (require external services / a real
# user's corpus):
#   - make eval_corpus  (requires ~/.claude/projects/*roomd* and ~/.codex/sessions/*.jsonl)
#   - Live Letta server queries
#
# Memory backends inside the container default to the same gracefully-degraded
# smoke paths used in CI: Letta is SKIPPED-UNHEALTHY (no server), Cognee can
# add but not search without LLM credentials, etc.

FROM python:3.13-slim-bookworm

# System deps for weasyprint + scientific Python + pg0 embedded postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libxml2 \
    libxslt1.1 \
    fonts-dejavu \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /phd

# Copy the entire phd/ tree
COPY . /phd/code/
WORKDIR /phd/code

# Install deps from the frozen file
RUN python -m venv /phd/code/.venv && \
    /phd/code/.venv/bin/pip install --upgrade pip && \
    /phd/code/.venv/bin/pip install -r requirements_frozen.txt

# Smoke test on container build
RUN /phd/code/.venv/bin/python -m pytest tests/test_adapters.py tests/test_calibration.py tests/test_governance.py tests/test_eval.py -v --tb=short -x

CMD ["/bin/bash"]
