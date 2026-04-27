"""Run the decision-agent flow for one or more normalized case inputs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:  # pragma: no cover - direct script execution support
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from decision_agent.io_utils import (
        load_bug_rows,
        load_normalized_case,
        load_severity_rules,
        load_summary_template,
        write_json,
    )
    from decision_agent.comparison_builder import build_case_comparison
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
except ImportError:  # pragma: no cover - direct script execution fallback
    from io_utils import (
        load_bug_rows,
        load_normalized_case,
        load_severity_rules,
        load_summary_template,
        write_json,
    )
    from comparison_builder import build_case_comparison
    from retriever import retrieve_relevant_bugs
    from rule_engine import (
        apply_severity_rules,
        build_recommended_action_with_case,
        build_root_cause_hypothesis,
        classify_decision_stage,
        classify_issue_taxonomy,
        infer_issue_type,
    )
    from summary_builder import build_decision_summary


def main(argv: list[str] | None = None) -> Path:
    decision_root = Path(__file__).resolve().parent
    repo_root = decision_root.parent
    output_root = repo_root / "output" / "decision_agent"

    parser = argparse.ArgumentParser(description="Run decision-agent analysis for one or more cases.")
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Optional case paths. Supports .json or .pdf within decision_agent/input/.",
    )
    args = parser.parse_args(argv)

    input_paths = resolve_input_paths(decision_root, args.inputs)
    bug_rows = load_bug_rows(
        decision_root / "knowledge_base" / "redmine_bug_summary_merged.csv"
    )
    severity_rules = load_severity_rules(decision_root / "rules" / "severity_rules.yaml")
    template = load_summary_template(
        decision_root / "templates" / "decision_summary_schema.json"
    )

    output_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    last_output_path = output_root / "case_comparison.json"

    for input_path in input_paths:
        case_data = load_normalized_case(input_path)
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
        summaries.append(summary)

        output_path = output_root / f"{input_path.stem}.decision_summary.json"
        write_json(output_path, summary)
        print(f"Wrote decision summary to {output_path}")
        last_output_path = output_path

    comparison = build_case_comparison(summaries)
    comparison_path = output_root / "case_comparison.json"
    write_json(comparison_path, comparison)
    print(f"Wrote case comparison to {comparison_path}")
    return comparison_path if summaries else last_output_path


def resolve_input_paths(decision_root: Path, raw_inputs: list[str]) -> list[Path]:
    if raw_inputs:
        return [resolve_single_input(decision_root, raw_input) for raw_input in raw_inputs]

    input_dir = decision_root / "input"
    pdf_inputs = sorted(input_dir.glob("case_*.pdf"))
    if pdf_inputs:
        return pdf_inputs

    json_inputs = [
        path
        for path in sorted(input_dir.glob("case_*.json"))
        if not path.name.endswith(".normalized.json")
    ]
    return json_inputs


def resolve_single_input(decision_root: Path, raw_input: str) -> Path:
    candidate = Path(raw_input)
    if candidate.exists():
        return candidate
    nested_candidate = decision_root / "input" / raw_input
    if nested_candidate.exists():
        return nested_candidate
    raise FileNotFoundError(f"Could not resolve input path: {raw_input}")


if __name__ == "__main__":
    main()
