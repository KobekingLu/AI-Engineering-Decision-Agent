# AI Engineering Decision Agent NotebookLM Source Pack

> 這份文件是給 NotebookLM 用的專案資料包。目標不是背答案，而是幫簡報產生更清楚的結構、語句與圖像提示。

## 1. Project Identity

- **Project name**: AI Engineering Decision Agent
- **One-line summary**: turn scattered engineering evidence into a decision-ready view
- **Core audience**: AE / PM / RD / DQA
- **What it is**: an engineering decision-assistance Agent
- **What it is not**: a generic chatbot, a final root-cause oracle, or a benchmark answer memorizer

### Names to fill before final submission

- **Project Owner**: `[fill with real name]`
- **Business Users**: `[fill with real names and regions]`
- **AI Builder**: `[fill with real name(s)]`

## 2. Project Goal

The project improves decision assistance quality under incomplete information.

It helps the team move faster from:

- fragmented evidence
- uncertain lifecycle state
- open questions
- repeated context switching

to:

- a decision-ready summary
- a clear next-step recommendation
- a reviewable HTML artifact

## 3. Problem Statement

Engineering case data is usually scattered across many places:

- issue descriptions
- comments and discussion threads
- logs
- PDF / HTML reports
- screenshots
- test results
- status history
- meeting notes
- known issue references

The real bottleneck is not only reading the data.

The bottleneck is aligning:

- evidence
- lifecycle state
- uncertainty
- missing information
- next action

## 4. Decision Boundary

This repo follows a strict boundary:

- do not pretend to know the final root cause when evidence is incomplete
- do not treat retrieved historical cases as definitive answer labels
- do not promote raw machine summaries into trusted knowledge
- do not ignore lifecycle evidence such as `clarifying`, `fixing`, `ready for DQA test`, `verifying`, `fixed`, `retest pass`, `root cause`, `solution`

The output should be uncertainty-aware and decision-ready, not overconfident.

The generated SQLite knowledge base should also be treated as a rebuildable artifact, not a trusted final answer source.

## 5. Input Sources

Recommended sources for this project:

- Redmine bug / task / note / attachment
- `decision_agent/knowledge_base/redmine_bug_summary_merged.csv`
- `decision_agent/knowledge_base/BUG Review/`
- logs
- PDF and HTML reports
- screenshots
- OCR output for scanned evidence
- comments and review notes
- meeting notes
- manual engineer summaries

Each source should preserve provenance:

- source type
- source path or link
- author or speaker when available
- timestamp
- extraction status

## 6. Agent Workflow

The agent workflow should be understood as a sequence of focused steps:

1. **Intake**
   - collect case text, logs, PDFs, screenshots, and notes

2. **Normalize**
   - turn scattered evidence into a consistent case record

3. **Extract lifecycle signals**
   - identify `clarifying`, `fixing`, `verifying`, `fixed`, `retest pass`, `solution`, `root cause`

4. **Retrieve**
   - find similar cases, known issues, and verification patterns

5. **Infer**
   - issue family
   - issue subtype
   - decision stage
   - confidence
   - uncertainty

6. **Recommend**
   - missing information
   - decisive evidence
   - next-step focus
   - smallest useful follow-up action

7. **Report**
   - generate a shareable HTML decision artifact

## 7. Output Schema

The final decision artifact should include:

- issue family
- issue subtype
- decision stage
- action mode
- resolution state
- confidence
- decisive evidence
- unresolved gap
- missing information
- likely root-cause hypothesis
- recommended action
- next-step focus
- lifecycle evidence summary

The key is to make the output useful for review, not to claim final certainty.

## 8. Knowledge Governance

The project uses a governed knowledge loop.

Recommended trust levels:

- **low**
  - raw case data
  - open discussion
  - machine-only summary

- **medium**
  - reviewed summary
  - strong but not fully confirmed evidence

- **high**
  - human-confirmed root cause
  - human-confirmed solution
  - human-confirmed verification result

Recommended write-back objects:

- `CaseRecord`
- `EvidenceRecord`
- `KnowledgeRecord`
- `DecisionArtifact`

The repository should keep raw data, machine artifacts, and human-confirmed knowledge separate.

## 9. Current Implementation Status

The current project already supports a working prototype style demo.

Current demo elements include:

- Streamlit-style UI
- case text input
- file upload support
- local OCR for scanned evidence
- local Gemma 4 mode
- deterministic fallback when the model is unavailable
- HTML decision report output
- multi-case review artifacts

### Runtime, Bridge, and Knowledge Base

- The Streamlit UI is the human-facing entry point for the demo.
- The local OpenClaw-style bridge exposes health and tool endpoints on `http://127.0.0.1:8787`.
- The bridge can serve `analyze_single_case` as a local tool layer for agent-style workflows.
- `demo.bat`, `start_demo.bat`, `start_demo.ps1`, `stop_demo.bat`, and `stop_demo.ps1` control the demo stack.
- The bridge can run in local Gemma 4 mode or deterministic fallback mode.
- `scripts/build_knowledge_base_db.py` can rebuild a SQLite knowledge base from the raw Redmine summary and `decision_agent/knowledge_base/BUG Review/` materials.
- The generated SQLite knowledge base lives as a rebuildable artifact under `.tmp/knowledge_base.generated.sqlite3` and should not be treated as a trusted final answer source.

The project should be described as a prototype that is already useful, not as a fully deployed enterprise platform.

## 10. Quantified Benefit

Use conservative numbers and phrase them carefully.

The current story should say:

- a first-pass manual review can be reduced from tens of minutes to a much shorter initial decision view
- context switching is reduced
- stage inference becomes more consistent
- follow-up becomes faster

If a number is still an estimate, say so explicitly.

## 11. Future Integration Alignment

The project should be framed as future-compatible with the company AI ecosystem.

### OpenClaw

Likely role:

- workflow orchestration
- intake
- tool gateway / local bridge
- retrieval
- report generation

### NemoClaw

Likely role:

- governed engineering knowledge
- issue history
- known issue patterns
- retrieval memory
- rebuildable knowledge base

### Hermes Agent

Likely role:

- action and system integration
- Redmine
- log repository
- test report
- follow-up actions

Important boundary:

- do not say these are already fully integrated
- the current code already has a local bridge and a governed knowledge base rebuild, but the broader OpenClaw / NemoClaw / Hermes story should still be presented as alignment and scaling direction
- present them as future alignment directions

## 12. Recommended Slide Narrative

If NotebookLM is asked to draft a contest deck, the slide story should be:

### Slide 1

- title
- domain
- team
- date

### Slide 2

- table of contents

### Slide 3

- what the official template expects
- why the project should be documented clearly

### Slide 4

- one-page executive summary

### Slide 5

- concrete example summary structure

### Slide 6

- reference-only note

### Slide 7

- business scenario and pain point

### Slide 8

- agent workflow

### Slide 9

- technical architecture

### Slide 10

- OpenClaw bridge / local tool gateway

### Slide 11

- governed knowledge base and provenance

### Slide 12

- OpenClaw / NemoClaw / Hermes alignment

### Slide 13

- current progress

### Slide 14

- demo scene or prototype showcase

### Slide 15

- quantified benefit

### Slide 16

- feasibility and scaling plan

### Slide 17

- executive summary supplement

### Slide 18

- appendix

### Slide 19

- more one-page summary examples

## 13. Visual Direction

For the final deck, the visual style should be:

- Chinese-first
- one slide, one message
- image-driven
- fewer paragraphs, more diagrams
- readable from a distance

Good visual types:

- evidence bridge diagram
- bridge health / manifest panel
- workflow pipeline
- architecture layers
- knowledge base rebuild flow
- decision dashboard mockup
- governance loop
- stage matrix

Avoid:

- huge text blocks
- unreadable full-page screenshots
- generic abstract images without context

## 14. Suggested Source Files to Upload into NotebookLM

Recommended upload set:

1. `docs/contest_template_requirements.md`
2. `docs/notebooklm/ai_engineering_decision_agent_notebooklm_master.md`
3. `docs/notebooklm/09_current_progress_snapshot.md`
4. `docs/openclaw-bridge-demo-script.md`
5. `docs/demo-recording-guide_v2.md`
6. representative case example notes
7. current screenshots, bridge health capture, or demo notes

## 15. NotebookLM Output Targets

Ask NotebookLM to produce:

- a 19-slide slide-by-slide outline
- a one-page executive summary in markdown
- a short deck narrative in Chinese
- a list of image / diagram suggestions per slide
- a conservative list of quantified benefits
- a section on what not to claim
- a clear current implementation vs future alignment distinction

## 16. Short Summary

This project is an engineering decision-assistance Agent.

It turns scattered evidence into a decision-ready view, keeps uncertainty visible, and supports better next-step action under incomplete information.
