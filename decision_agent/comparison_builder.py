"""Comparison helpers for multiple decision-agent cases."""

from __future__ import annotations

from typing import Any


def build_case_comparison(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_rows = [
        {
            "case_id": result.get("case_id", ""),
            "issue_family": result.get("issue_family", result.get("issue_type", "")),
            "issue_subtype": result.get("issue_subtype", ""),
            "decision_stage": result.get("decision_stage", ""),
            "action_mode": result.get("action_mode", ""),
            "risk_level": result.get("risk_level", ""),
            "recommended_action_summary": _shorten(str(result.get("recommended_action", "")), 180),
            "why_action_differs": _action_difference_reason(result),
        }
        for result in case_results
    ]

    observations: list[str] = []
    if not comparison_rows:
        observations.append("No case results were available for comparison.")
    else:
        families = {row["issue_family"] for row in comparison_rows}
        stages = {row["decision_stage"] for row in comparison_rows}
        if len(families) == 1:
            observations.append(f"All compared cases share the same issue_family: {next(iter(families))}.")
        else:
            observations.append("Compared cases diverge in issue_family, indicating taxonomy separation is working.")
        if len(stages) == 1:
            observations.append(f"All compared cases currently land on the same decision_stage: {next(iter(stages))}.")
        else:
            observations.append("Compared cases diverge in decision_stage, so lifecycle-aware actions are differentiated.")

    return {
        "case_count": len(case_results),
        "cases": comparison_rows,
        "observations": observations,
        "focus_checks": [
            "issue_family",
            "issue_subtype",
            "decision_stage",
            "action_mode",
            "recommended_action_summary",
            "why_action_differs",
        ],
    }


def _shorten(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _action_difference_reason(result: dict[str, Any]) -> str:
    stage = str(result.get("decision_stage", ""))
    subtype = str(result.get("issue_subtype", ""))
    resolution = str(result.get("resolution_state", ""))

    if stage == "closure":
        return "Case already has fixed/closed lifecycle evidence, so action is closure-oriented."
    if stage == "verification":
        return "Case is in verifying/ready-for-DQA state, so action focuses on retest gating."
    if stage == "root-cause identified":
        return "Root cause is identified, so action focuses on validation scope rather than initial triage."
    if "link width downgrade" in subtype:
        return "Subtype is link-width degradation, so action focuses on lane-width verification."
    if "slot-path-location" in subtype:
        return "Subtype is location-specific path defect, so action focuses on slot/path isolation."
    if "uncorrectable AER" in subtype:
        return "Subtype includes uncorrectable PCIe signal, so action remains strict and trigger-based."
    if "front panel button signal" in subtype:
        return "Subtype is front-panel reset signal issue, so action targets board-level reset path validation."
    if subtype.startswith("memory /"):
        return "Subtype is memory margin/population/BIOS related, so action targets memory matrix verification."
    if resolution:
        return f"Action is adjusted by lifecycle resolution_state = {resolution}."
    return "Action is driven by combined stage + subtype evidence."
