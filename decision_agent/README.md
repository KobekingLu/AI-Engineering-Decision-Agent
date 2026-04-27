# Decision Agent Core

This folder contains the reusable decision core for the `AI Engineering Decision Agent` demo.

Its job is simple:

- read one or more engineering issue cases
- normalize available evidence
- retrieve similar historical bugs
- infer issue type
- evaluate risk level
- explain the basis of the decision
- produce structured summary output

## What This Module Does

The current flow is designed for **engineering issue triage and decision support**, not full autonomous decision making.

It turns raw or normalized issue evidence into decision-ready output that can be reviewed by AE, PM, RD, and DQA.

## Input Expectations

The core flow works best with normalized case input, but it can also support PDF intake through the current sidecar / extraction path.

Typical useful fields include:

- `case_id`
- `subject`
- `issue_description`
- `log_snippet`
- `comments`
- `reporter_role`
- `component`
- `test_context`
- `fail_rate`
- `evidence`

When input is incomplete, the agent should surface that gap through `missing_information` instead of pretending certainty.

## Output Shape

The decision summary is built around these fields:

- `issue_type`
- `risk_level`
- `root_cause_hypothesis`
- `recommended_action`
- `missing_information`
- `decision_summary`
- `reasoning_trace`
- `matched_historical_cases`

## Current Flow

1. Load normalized case input
2. Retrieve similar historical bug records from the local knowledge base
3. Infer issue type from case evidence and matched patterns
4. Apply severity and risk rules
5. Build a structured decision summary
6. Optionally compare multiple cases

## Main Entry Points

- `run_case.py`: CLI entry point for one or more cases
- `service.py`: thin importable interface for app integration

## Key Files

- `models.py`: data models for case input, bug rows, rules, and output
- `io_utils.py`: loading and JSON writing helpers
- `retriever.py`: historical bug retrieval
- `rule_engine.py`: issue typing, risk evaluation, and recommended action logic
- `summary_builder.py`: final structured summary assembly
- `comparison_builder.py`: cross-case comparison output
- `pdf_intake.py`: PDF intake and sidecar support

## Knowledge Base and Rules

- `knowledge_base/redmine_bug_summary_merged.csv`: historical bug summary data
- `rules/severity_rules.yaml`: starter severity and risk rules
- `rules/required_bug_fields.yaml`: required-field guidance
- `templates/decision_summary_schema.json`: output schema template

## Run from Repo Root

Analyze default sample inputs:

```powershell
python decision_agent/run_case.py
```

Analyze a specific case:

```powershell
python decision_agent/run_case.py decision_agent/input/case_001_normalized.json
```

## Design Intent

This module is intentionally:

- readable
- easy to modify
- explainable
- light on framework complexity

It is a practical decision-support core for demo and iteration, not a production-grade orchestration system.
