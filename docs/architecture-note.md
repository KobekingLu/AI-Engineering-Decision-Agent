# Architecture Note

## Purpose

This note describes the intended architecture direction for `decision-agent-demo`.

The target is not a one-off analyzer. The target is a governed AI engineering decision agent that improves decision assistance quality under incomplete information.

## Design Goal

The agent should become better at:

- finding the right similar cases
- identifying decisive evidence
- describing uncertainty clearly
- proposing the most valuable next engineering step
- helping the team form a decision-ready view earlier

It should not be optimized as a closed-case answer reproducer.

## Proposed Layers

### 1. Data Ingestion Layer

Supported inputs should gradually include:

- Redmine bug / task / note / status / attachment
- meeting notes and review notes
- uploaded files such as PDF, HTML, text logs, screenshots
- manual engineer summaries

The ingestion layer should preserve provenance:

- source type
- source link or file path
- author / speaker when available
- timestamp
- extraction status

### 2. Knowledge Normalization Layer

Different sources should be mapped into a unified, governed schema.

Recommended logical entities:

- `CaseRecord`
  Current-case view assembled from raw evidence

- `EvidenceRecord`
  One extracted piece of evidence with provenance and trust metadata

- `KnowledgeRecord`
  Normalized historical knowledge entry used for retrieval

- `DecisionArtifact`
  Machine-generated output for one current case

Suggested normalized fields:

- case metadata
- issue family / subtype
- symptom
- trigger condition
- key evidence
- reproduction condition
- root cause
- solution
- verification result
- confidence / trust level
- source type / source link / timestamp

### Lifecycle Evidence Extraction

Lifecycle evidence should be treated as a first-class normalized signal, not as incidental wording inside long case text.

Examples of lifecycle evidence include:

- status values such as `clarifying`, `fixing`, `ready for DQA test`, `verifying`, `fixed`
- explicit `status changed from ... to ...` history
- comments or notes that state `root cause`, `solution`, `retest pass`, or equivalent confirmation
- replacement board, reworked sample, BIOS config update, or other fix-candidate signals

This matters because the repo is not trying to memorize final answers from closed cases, but it also should not ignore lifecycle evidence already present in the current case.

Recommended normalized lifecycle fields:

- `status_current`
- `status_history`
- `decision_stage_candidate`
- `resolution_state_candidate`
- `has_root_cause_signal`
- `has_solution_signal`
- `has_verification_signal`
- `has_pass_signal`

These fields should later influence:

- decision-stage inference
- action-mode inference
- missing-information generation for the current stage
- retrieval of similar recovery and verification patterns

### 3. Retrieval Layer

Retrieval should move beyond keyword overlap.

Preferred retrieval sequence:

1. filter by likely issue family / subtype
2. filter by trigger condition and fail signal
3. rank by symptom similarity
4. rank by recovery or verification pattern
5. apply trust-aware weighting

This means:

- high-trust confirmed cases should rank differently from open-note references
- meeting notes can support retrieval, but should carry lower trust unless confirmed

### 4. Decision Assistance Layer

The output should help a human make the next engineering decision.

Core output fields should include:

- likely issue family
- likely issue subtype
- decision stage
- confidence
- uncertainty summary
- decisive evidence
- unresolved gap
- missing information
- next-step focus
- recommended action
- knowledge governance note

This layer should avoid presenting retrieved patterns as final truth.

### 5. Knowledge Feedback Layer

New case information should not automatically become trusted knowledge.

Recommended write-back levels:

- raw case record
- machine-generated summary
- human-confirmed root cause
- human-confirmed solution
- human-confirmed verification result

Recommended trust levels:

- `low`
  Open case, ongoing discussion, machine-only summary

- `medium`
  Reviewed summary or strong but not fully confirmed evidence

- `high`
  Human-confirmed root cause / solution / verification result

## Current Gaps

The current repo already has:

- single-case ingestion
- normalization
- retrieval
- decision assistance
- benchmark regression

But it still lacks:

- first-class trust-level modeling
- separated `CaseRecord` / `KnowledgeRecord` data model
- governed write-back flow
- meeting-note ingestion and provenance tracking
- trust-aware ranking across mixed knowledge sources

## Near-Term Priorities

The next practical improvements should focus on:

1. stronger normalized schema for evidence and trust level
2. better lifecycle / decision-stage extraction from Redmine and notes
3. retrieval ranking that separates symptom similarity from fix-pattern similarity
4. output fields that guide the next investigation step under uncertainty
5. governance-aware storage for machine artifacts vs confirmed knowledge
