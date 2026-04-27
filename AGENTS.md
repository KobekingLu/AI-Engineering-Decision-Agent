# AGENTS.md

## Project Name

AI Engineering Decision Agent

## Long-Term Direction

This repository exists to improve engineering decision assistance quality under incomplete information.

The agent is not meant to memorize final answers from closed cases, and it is not meant to replace AE, PM, RD, or DQA final judgment.

Its job is to help the team move faster from scattered evidence to a decision-ready view.

## Benchmark Principle

Benchmark cases are teaching material, not answer labels.

They should be used to learn:

- how to classify issue family and subtype more accurately
- how to recognize decisive evidence earlier
- how to identify missing information based on the current decision need
- how to distinguish decision stages
- how to propose better next-step investigation guidance
- how to express uncertainty instead of overclaiming

Do not optimize this repo for reproducing the final answer of closed benchmark cases.
Do not hard-code benchmark outputs.
Do not memorize final answers from closed cases, but do not ignore lifecycle evidence already present in the current case.

## Agent Role Boundary

This agent should help with:

- likely issue family
- likely issue subtype
- decision stage
- likely investigation direction
- missing information
- next-step recommendation
- uncertainty / confidence
- decision-ready summary

This agent should not:

- pretend to know the final root cause when evidence is incomplete
- treat retrieved historical cases as definitive answers
- replace human engineering sign-off

## Preferred Optimization Priorities

When improving this repo, prefer work that strengthens:

- issue family / subtype classification
- decision stage awareness
- uncertainty-aware reasoning
- evidence prioritization
- missing-information identification based on decision needs
- case-specific next-step guidance
- retrieval quality using symptom, trigger condition, fail signal, and recovery pattern
- governed knowledge accumulation

Do not prioritize cosmetic wording changes over these decision-quality improvements.

## Architecture Direction

Future work in this repo should move toward five layers:

1. Data ingestion layer
   Sources may include Redmine, meeting notes, uploaded case files, HTML reports, logs, and manual summaries.

2. Knowledge normalization layer
   Different source types should be normalized into a governed schema with metadata, symptoms, evidence, root-cause fields, solution fields, verification fields, and provenance.

3. Retrieval layer
   New cases should retrieve reference patterns by issue family, subtype, trigger condition, symptom, root-cause pattern, and fix/verification pattern.

4. Decision assistance layer
   The system should generate likely direction, missing information, uncertainty, and the most valuable next step.

5. Knowledge feedback layer
   New case outcomes should be written back in governed form with trust levels, not blindly auto-learned.

## Knowledge Governance Rules

Follow these rules whenever knowledge handling is involved:

- raw new case data may be stored, but it is not confirmed knowledge
- machine-generated summary is an artifact, not a trusted source of truth
- only human-confirmed root cause / solution / verification result belongs in a high-trust knowledge base
- open or unfinished cases must remain low-confidence references
- meeting notes must preserve source, speaker, date, and context
- provenance should be preserved whenever data is normalized or merged

## Decision Assistance Rules

When producing case analysis:

- prefer `likely` language over definitive language when evidence is incomplete
- explicitly state uncertainty and confidence
- explain what is missing and why it matters
- recommend the smallest, highest-value next step that best separates competing hypotheses
- adapt recommendation shape to the issue subtype and decision stage
- distinguish between triage, investigation, verification, and closure

Lifecycle signals must be treated as high-priority evidence for stage inference. In particular, signals such as:

- `clarifying`
- `fixing`
- `ready for DQA test`
- `verifying`
- `fixed`
- `retest pass`
- explicit `solution`
- explicit `root cause`

should strongly influence the inferred `decision_stage`, `action_mode`, and `resolution_state`.

This means:

- a case may still use decision-assistance language without pretending the final answer is certain
- but it must not be pushed back to an artificially early stage if the case already contains real lifecycle evidence
- stage inference should reflect the best current lifecycle state present in the case, not only the most conservative wording

## Anti-Patterns

Avoid these failure modes:

- generic recommendation templates reused across unrelated case shapes
- retrieval driven only by keyword overlap
- ignoring lifecycle signals such as fixed / verifying / retest pass
- over-correcting toward caution so aggressively that a case with clear fix or verification evidence is still treated like early triage
- treating benchmark closed cases as ground-truth labels to copy
- promoting unreviewed machine output into trusted knowledge
- collapsing all uncertainty into a single confidence label without explanation

## Practical Working Style

Keep work incremental, demo-friendly, and inspectable.

When unsure:

1. favor a clearer decision-assistance artifact over a more complicated architecture
2. preserve provenance and uncertainty
3. keep retrieved knowledge framed as reference support
4. avoid overfitting to one benchmark case
5. make the next engineering action more useful, not just more polished
