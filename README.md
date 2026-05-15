# AI Engineering Decision Agent

[![CI](https://github.com/KobekingLu/AI-Engineering-Decision-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/KobekingLu/AI-Engineering-Decision-Agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

AI Engineering Decision Agent is a demo-grade system for cross-function engineering decision assistance under incomplete information.

It helps AE, PM, RD, and DQA move from scattered evidence to a decision-ready view faster, while keeping uncertainty visible and avoiding overclaiming on incomplete cases.

## What This Repo Is For

This repository is focused on:

- likely issue family and subtype classification
- decision stage awareness
- uncertainty-aware reasoning
- missing-information identification
- case-specific next-step guidance
- retrieval of similar historical patterns
- governed knowledge accumulation

It is not meant to:

- memorize the final answer of closed benchmark cases
- treat closed cases as labels to copy
- replace human engineering judgment

## Repository Layout

- `decision_agent/`
  Core decision logic, retrieval, benchmark regression, and schema/template files.

- `web_app/`
  Local Streamlit demo UI for intake, analysis, and HTML reporting.

- `docs/`
  Architecture notes and supporting documentation.

- `assets/`
  Demo screenshots and example HTML artifacts used in the README.

- `scripts/`
  Utility scripts, including the rebuildable knowledge base builder.

## Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the sample case flow:

```powershell
python -m decision_agent.run_case decision_agent/input/case_002_ae_issue.json
```

Run the default sample set:

```powershell
python -m decision_agent.run_case
```

Run a second sample case:

```powershell
python -m decision_agent.run_case decision_agent/input/case_003_dqa_issue.json
```

Run benchmark regression:

```powershell
python -m decision_agent.benchmark_regression
```

Run the local Streamlit app:

```powershell
python web_app/run_app.py
```

Run the full demo stack with the OpenClaw-style bridge:

```powershell
.\demo.bat
```

Stop the full demo stack:

```powershell
.\stop_demo.bat
```

`python web_app/run_app.py` starts only the human-facing UI. `.\demo.bat` starts the UI plus the bridge and local Gemma wiring used in the demo.

If you need a screen recording or demo walkthrough, see [docs/demo-recording-guide.md](docs/demo-recording-guide.md).

Example outputs are written to:

- `output/decision_agent/`
- `output/web_app/json/`
- `output/web_app/html/`

## OpenClaw Bridge

The repo includes a local HTTP bridge at `decision_agent/openclaw_bridge.py`.

It exposes:

- `http://127.0.0.1:8787/health`
- `http://127.0.0.1:8787/manifest`

The bridge can run in local Gemma 4 mode or deterministic fallback mode, and the Streamlit UI shows its health status at startup.

## Knowledge Base

The repo can rebuild a governed SQLite knowledge base from:

- `decision_agent/knowledge_base/redmine_bug_summary_merged.csv`
- `decision_agent/knowledge_base/BUG Review/`

Run:

```powershell
python scripts/build_knowledge_base_db.py
```

The generated database is written to `.tmp/knowledge_base.generated.sqlite3`. It is a rebuildable artifact, not a human-confirmed source of truth.

## Validation

This repo includes a GitHub Actions workflow that performs a basic maintenance check:

- installs the Python dependencies
- compiles the `decision_agent` and `web_app` packages

That gives us a quick syntax and import-path sanity check on every push and pull request.

## Releases

- [v0.1.0 release notes](docs/releases/v0.1.0.md)

## Decision Assistance Shape

The agent is designed to output:

- likely issue family
- likely issue subtype
- decision stage
- missing information
- likely investigation direction
- next-step recommendation
- uncertainty and confidence
- decision-ready summary

Lifecycle signals such as `clarifying`, `fixing`, `ready for DQA test`, `verifying`, `fixed`, `retest pass`, `solution`, and `root cause` should strongly influence stage inference.

## Governance Notes

- raw new case data may be stored, but it is not automatically confirmed knowledge
- machine-generated summaries are artifacts, not trusted truth sources
- only human-confirmed root cause / solution / verification results belong in high-trust knowledge
- meeting notes should preserve source, speaker, date, and context
- open or unfinished cases should remain low-confidence references
- the generated SQLite knowledge base is a rebuildable artifact and should not be treated as confirmed truth

## Current Boundary

This repo is intentionally practical and inspectable.

It is built to support decision assistance, not to replace final engineering sign-off.
