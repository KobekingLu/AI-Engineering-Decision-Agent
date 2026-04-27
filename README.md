# AI Engineering Decision Agent

AI agent for cross-function engineering decision assistance under incomplete information.

This repository is not aimed at reproducing the final answer from closed bugs. Its purpose is to help AE, PM, RD, and DQA turn scattered evidence into a clearer, decision-ready view, so the next engineering decision can happen faster and with better context.

## Project Positioning

The core strengthening target of this project is:

`improve decision assistance quality under incomplete information`

That means the agent should get better at:

- identifying the most likely issue family and subtype
- surfacing the most valuable evidence instead of being distracted by background noise
- expressing uncertainty clearly
- proposing engineer-like next steps that actually move the case forward
- recognizing the current decision stage
- helping the team form a decision-ready view faster

The goal is not:

- memorizing the final answer of benchmark cases
- treating closed cases as labels to imitate
- replacing AE/RD/DQA final judgment

Closed or historical cases are still useful, but in a specific way: the agent should not memorize their final answers as labels to copy. At the same time, if the current case already contains lifecycle evidence such as `clarifying`, `fixing`, `ready for DQA test`, `verifying`, `fixed`, `retest pass`, `solution`, or `root cause`, that evidence should strongly influence stage-aware decision assistance.

## What Benchmark Cases Are For

The benchmark cases in this repo are used as teaching material, not answer keys.

They help us learn:

- how to classify issue family and subtype more accurately
- how to spot decisive evidence early
- how to identify missing information by decision need
- how to separate `triage`, `investigation`, `verification`, and `closure`
- how to recommend different investigation paths for different case shapes
- how to improve engineering decision assistance before the final answer exists

## Current Agent Role

This agent is a decision-assistance system, not a final-decision system.

Given a current case plus retrieved reference patterns, it should produce:

- likely issue family
- likely issue subtype
- decision stage
- missing information
- likely investigation direction
- next-step recommendation
- uncertainty / confidence
- decision summary

The output is intended to support engineering discussion, not to declare definitive root cause.

## Stage-Aware Behavior

In this repo, `decision stage` is not just a presentation label. It is meant to shape the recommended next action.

- `triage`
  The agent should identify the likely issue direction, highlight the most important missing evidence, and suggest the first branch-separating step.

- `investigation`
  The agent should focus on narrowing competing hypotheses and recommend the most efficient compare or isolation step.

- `verification`
  The agent should assume a likely fix or root-cause path already exists, and focus on whether the original fail condition has been re-tested and cleared.

- `closure`
  The agent should focus on closure-grade evidence: final PASS result, fix scope, verification package, and traceable status history.

This is also where lifecycle evidence matters most: even when the agent keeps an uncertainty-aware, decision-assistance tone, it should not push a case back to an artificially early stage if the case already contains `clarifying`, `fixing`, `ready for DQA test`, `verifying`, `fixed`, `retest pass`, `solution`, or `root cause` signals.

## Current Capabilities

- single-case intake from freeform text or multi-file bundle
- local OCR for scanned PDF and image evidence
- case normalization into a reusable decision input
- retrieval of similar historical issue patterns
- issue family / subtype classification
- decision stage awareness
- uncertainty-aware reasoning fields
- case-specific next-step guidance
- single-case JSON summary output
- single-case HTML report output
- benchmark cross-case regression output

## Current Architecture

The current MVP already reflects the future direction in a small form:

1. `Data intake`
   Freeform text, PDF, HTML, images, logs, and manual notes can be ingested as one case bundle.

2. `Knowledge normalization`
   Uploaded evidence is normalized into a shared case structure before analysis.

3. `Retrieval`
   Similar historical cases are retrieved as reference patterns, not as answer labels.

4. `Decision assistance`
   The agent produces likely classification, uncertainty, missing information, and next-step guidance.

5. `Report output`
   The result is rendered into JSON and HTML for demo review.

See [docs/architecture-note.md](docs/architecture-note.md) for the longer-term architecture direction.

## Knowledge Accumulation With Governance

This project is intended to become a governed engineering knowledge loop over time.

Future knowledge sources may include:

- Redmine bug / task / note / status / attachment
- quarterly bug review or issue review meeting notes
- DQA / RD / AE / PM discussion records
- human-confirmed root cause / solution / verification result
- uploaded case files, PDFs, logs, and HTML reports

But governance matters:

- raw new case data may be stored, but it is not automatically confirmed knowledge
- machine-generated summary is an artifact, not a trusted truth source
- only human-confirmed root cause / solution / verification result should enter a high-trust knowledge base
- meeting notes must preserve source, speaker, date, and context
- open or unfinished cases should remain low-confidence reference material

## Benchmark-Driven Improvement Direction

When we use benchmark cases, the priority is to improve:

- issue family / subtype classification
- decision stage awareness
- evidence prioritization
- uncertainty-aware reasoning
- missing-information identification
- case-specific recommended action
- retrieval quality based on trigger, symptom, and recovery pattern

The priority is not to hard-code benchmark outputs.

## Repo Structure

- `decision_agent/`
  Core decision logic, retrieval, benchmark regression, and schema/template files.

- `web_app/`
  Local Streamlit app for intake, analysis, and HTML reporting.

- `docs/`
  Architecture notes and future design guidance.

- `output/`
  Local generated summaries and reports.

## Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the decision-agent CLI with one example input:

```powershell
python -m decision_agent.run_case decision_agent/input/case_002_ae_issue.json
```

Run benchmark regression:

```powershell
python -m decision_agent.benchmark_regression
```

Run the local web app:

```powershell
python web_app/run_app.py
```

Notes:

- The web launcher will pick the first free port from `8501` to `8505`, so the actual URL may differ if one of those ports is already in use.
- On Windows, if a summary JSON or HTML file is already open in a browser or editor, the CLI may fail to overwrite that same output filename. Closing the opened file or using a fresh case ID avoids that lock.

## Current Boundaries

- reasoning is still primarily rule-based plus retrieval-assisted
- the knowledge base is still a demo-scale local dataset
- trust-level governance is only partially represented in the current code
- retrieved cases are still references, not validated answers
- final engineering decision remains with human owners

## Why This Repo Exists

This repo exists to make the engineering decision-assistance layer independently demoable.

The project story is now:

- this repo: case intake, evidence normalization, retrieval, decision assistance, governed knowledge direction
- separate pre-shipment repo: shipment review workbook flow and pre-shipment risk review
