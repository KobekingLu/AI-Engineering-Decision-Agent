"""Thin importable helpers that reuse the existing decision-agent flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from decision_agent.io_utils import (
    load_bug_rows,
    load_normalized_case,
    load_severity_rules,
    load_summary_template,
    write_json,
)
from decision_agent.models import NormalizedCase
from decision_agent.retriever import retrieve_relevant_bugs
from decision_agent.rule_engine import (
    apply_severity_rules,
    build_recommended_action_with_case,
    build_root_cause_hypothesis,
    classify_decision_stage,
    classify_issue_taxonomy,
    infer_issue_type,
)
from decision_agent.summary_builder import build_decision_summary


def analyze_single_case(
    case_input: Path | NormalizedCase | dict[str, Any],
    *,
    decision_root: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Run the existing decision-agent flow for one case and return the summary."""

    resolved_decision_root = decision_root or Path(__file__).resolve().parent
    case_data = _coerce_case_input(case_input)
    bug_rows = load_bug_rows(
        resolved_decision_root / "knowledge_base" / "redmine_bug_summary_merged.csv"
    )
    severity_rules = load_severity_rules(
        resolved_decision_root / "rules" / "severity_rules.yaml"
    )
    template = load_summary_template(
        resolved_decision_root / "templates" / "decision_summary_schema.json"
    )

    matched_bugs = retrieve_relevant_bugs(case_data, bug_rows, top_n=3)
    issue_type = infer_issue_type(case_data, matched_bugs)
    issue_family, issue_subtype, taxonomy_evidence = classify_issue_taxonomy(case_data, matched_bugs)
    decision_stage, action_mode, resolution_state, stage_evidence, unresolved_gap = classify_decision_stage(
        case_data,
        issue_family,
        issue_subtype,
    )
    risk_level, matched_rules = apply_severity_rules(
        case_data,
        matched_bugs,
        severity_rules,
        issue_family=issue_family,
        issue_subtype=issue_subtype,
        decision_stage=decision_stage,
    )
    root_cause_hypothesis = build_root_cause_hypothesis(
        issue_type,
        case_data,
        matched_bugs,
        issue_subtype=issue_subtype,
    )
    recommended_action = build_recommended_action_with_case(
        issue_type,
        risk_level,
        case_data,
        issue_subtype=issue_subtype,
        decision_stage=decision_stage,
        action_mode=action_mode,
        resolution_state=resolution_state,
    )

    summary = build_decision_summary(
        case_data=case_data,
        matched_bugs=matched_bugs,
        issue_type=issue_type,
        risk_level=risk_level,
        root_cause_hypothesis=root_cause_hypothesis,
        recommended_action=recommended_action,
        applied_rules=matched_rules,
        template=template,
        issue_family=issue_family,
        issue_subtype=issue_subtype,
        decision_stage=decision_stage,
        action_mode=action_mode,
        resolution_state=resolution_state,
        decisive_evidence=taxonomy_evidence + stage_evidence,
        unresolved_gap=unresolved_gap,
    )

    if output_path is not None:
        write_json(output_path, summary)

    return summary


def _coerce_case_input(case_input: Path | NormalizedCase | dict[str, Any]) -> NormalizedCase:
    if isinstance(case_input, NormalizedCase):
        return case_input
    if isinstance(case_input, Path):
        return load_normalized_case(case_input)
    if isinstance(case_input, dict):
        return NormalizedCase.from_dict(case_input)
    raise TypeError(f"Unsupported case_input type: {type(case_input)!r}")
