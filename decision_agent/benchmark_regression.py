"""Run benchmark cross-case regression for five decision-agent demo cases."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import fitz

from decision_agent.service import analyze_single_case

BENCHMARK_CASE_IDS = ["133843_v2", "135177_v2", "135322", "141307", "143084_v2"]


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Run benchmark regression analysis for decision-agent.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output_root = Path(args.output).resolve() if args.output else repo_root / "output" / "decision_agent"
    output_root.mkdir(parents=True, exist_ok=True)

    web_output = repo_root / "output" / "web_app"
    rows: list[dict[str, Any]] = []
    mismatch_report: list[dict[str, Any]] = []

    for case_id in BENCHMARK_CASE_IDS:
        input_path = web_output / "input" / f"{case_id}.normalized.json"
        new_summary = analyze_single_case(input_path, decision_root=repo_root / "decision_agent")
        old_summary_text = _read_text(web_output / "json" / f"{case_id}.decision_summary.json")
        pdf_text = _extract_pdf_text(web_output / "uploads" / case_id)
        pdf_signals = _collect_pdf_signals(pdf_text)

        old_issue_type = _extract_old_field(old_summary_text, "issue_type")
        old_recommendation = _extract_old_field(old_summary_text, "recommended_action")
        old_bundle_text = old_summary_text.lower()

        missing_from_old = [
            signal["label"]
            for signal in pdf_signals
            if signal["found"] and not _signal_reflected_in_old(signal["reflect_keywords"], old_bundle_text)
        ]

        distorted_recommendation = []
        if _is_advanced_lifecycle(pdf_text) and _looks_generic_triage_action(old_recommendation):
            distorted_recommendation.append(
                "Recommendation remained generic triage despite lifecycle evidence (fixed/verifying/pass/root cause)."
            )

        expected_family = _expected_family_from_pdf(pdf_text)
        misclassified = []
        if expected_family and old_issue_type and expected_family.lower() not in old_issue_type.lower():
            misclassified.append(
                f"Expected family from PDF signals = {expected_family}, but old HTML decision = {old_issue_type}."
            )

        rows.append(
            {
                "case_id": case_id,
                "predicted_issue_family": new_summary.get("issue_family", new_summary.get("issue_type", "")),
                "predicted_subtype": new_summary.get("issue_subtype", ""),
                "decision_stage": new_summary.get("decision_stage", ""),
                "recommended_action_summary": _shorten(str(new_summary.get("recommended_action", "")), 180),
                "why_this_action_differs": _why_action_differs(new_summary),
            }
        )

        mismatch_report.append(
            {
                "case_id": case_id,
                "pdf_signals_missing_in_old_html": missing_from_old,
                "recommendation_distortion_due_to_lifecycle_gap": distorted_recommendation,
                "misclassification": misclassified,
                "old_issue_type": old_issue_type,
                "old_recommended_action": old_recommendation,
                "new_issue_family": new_summary.get("issue_family", ""),
                "new_issue_subtype": new_summary.get("issue_subtype", ""),
                "new_decision_stage": new_summary.get("decision_stage", ""),
            }
        )

    payload = {
        "benchmark_cases": BENCHMARK_CASE_IDS,
        "cross_case_table": rows,
        "pdf_vs_old_html_gap_analysis": mismatch_report,
    }
    json_path = output_root / "benchmark_regression.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_path = output_root / "benchmark_regression.md"
    md_path.write_text(_to_markdown(rows, mismatch_report), encoding="utf-8")
    print(f"Wrote benchmark regression json to {json_path}")
    print(f"Wrote benchmark regression markdown to {md_path}")
    return md_path


def _to_markdown(rows: list[dict[str, Any]], mismatch_report: list[dict[str, Any]]) -> str:
    lines = [
        "# Benchmark Cross-Case Regression",
        "",
        "| case id | predicted issue family | predicted subtype | decision stage | recommended action summary | why this action differs |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {case_id} | {predicted_issue_family} | {predicted_subtype} | {decision_stage} | {recommended_action_summary} | {why_this_action_differs} |".format(
                **{k: _sanitize_markdown(str(v)) for k, v in row.items()}
            )
        )

    lines.extend(["", "## PDF vs Current HTML Gaps", ""])
    for item in mismatch_report:
        lines.append(f"### {item['case_id']}")
        lines.append("- Signals in PDF but not reflected in old HTML output:")
        if item["pdf_signals_missing_in_old_html"]:
            for signal in item["pdf_signals_missing_in_old_html"]:
                lines.append(f"  - {signal}")
        else:
            lines.append("  - (none)")
        lines.append("- Recommendation distortion due to lifecycle gap:")
        if item["recommendation_distortion_due_to_lifecycle_gap"]:
            for message in item["recommendation_distortion_due_to_lifecycle_gap"]:
                lines.append(f"  - {message}")
        else:
            lines.append("  - (none)")
        lines.append("- Misclassification:")
        if item["misclassification"]:
            for message in item["misclassification"]:
                lines.append(f"  - {message}")
        else:
            lines.append("  - (none)")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _extract_pdf_text(upload_case_dir: Path) -> str:
    pdf_paths = sorted(upload_case_dir.glob("*.pdf"))
    if not pdf_paths:
        return ""
    path = pdf_paths[0]
    doc = fitz.open(path)
    chunks: list[str] = []
    for index in range(min(doc.page_count, 10)):
        text = (doc.load_page(index).get_text("text") or "").strip()
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def _collect_pdf_signals(text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    signal_definitions = [
        ("Status changed signal", ["status changed", "ready for dqa test", "verifying", "fixed", "closed"], ["status", "verifying", "ready for dqa", "fixed", "closed"]),
        ("Root cause / solution signal", ["root cause", "solution(root cause)", "r&d solution"], ["root cause", "solution"]),
        ("PASS / retest pass signal", ["pass", "retest", "verified"], ["pass", "retest", "verified"]),
        ("Replacement / reworked sample signal", ["replacement", "reworked sample", "rework", "board change"], ["rework", "replacement", "board change"]),
        ("BIOS config update signal", ["bios", "amd cbs", "setting"], ["bios", "setting", "config"]),
        ("PCIe corrected AER signal", ["corrected error", "correctable", "bit14"], ["corrected", "bit14"]),
        ("PCIe uncorrectable / ACS signal", ["uncorrectable", "acs violation"], ["uncorrectable", "acs violation"]),
        ("PCIe link width downgrade signal", ["link width", "x2", "downgraded"], ["link width", "x2", "downgrade"]),
        ("Front panel reset button signal", ["front panel", "reset button", "no response"], ["front panel", "reset button", "signal"]),
        ("Memory margin / DIMM / BIOS dependency signal", ["memory margin", "rmt", "vref", "write_1d_jtag", "one dimm per channel", "dimm population"], ["memory margin", "rmt", "vref", "dimm population"]),
    ]
    signals = []
    for label, patterns, reflect_keywords in signal_definitions:
        found = any(pattern in lowered for pattern in patterns)
        signals.append(
            {
                "label": label,
                "found": found,
                "reflect_keywords": reflect_keywords,
            }
        )
    return signals


def _signal_reflected_in_old(keywords: list[str], old_text: str) -> bool:
    return any(keyword in old_text for keyword in keywords)


def _is_advanced_lifecycle(pdf_text: str) -> bool:
    lowered = pdf_text.lower()
    return any(
        phrase in lowered
        for phrase in [
            "ready for dqa test",
            "verifying",
            "fixed",
            "closed",
            "root cause",
            "solution",
            "pass",
            "retest",
            "reworked sample",
        ]
    )


def _looks_generic_triage_action(action: str) -> bool:
    lowered = action.lower()
    generic_patterns = [
        "stop shipment review and ask ae/rd to reproduce, isolate, and fix before proceeding",
        "stop shipment review and ask ae/rd/dqa to isolate",
        "collect more evidence and rerun the decision flow",
    ]
    return any(pattern in lowered for pattern in generic_patterns)


def _expected_family_from_pdf(pdf_text: str) -> str:
    lowered = pdf_text.lower()
    if any(token in lowered for token in ["memory margin", "rmt", "vref", "write_1d_jtag", "one dimm per channel", "dimm population"]):
        return "memory"
    if any(token in lowered for token in ["front panel", "reset button", "rst bt", "no response"]):
        return "power-reset"
    if any(token in lowered for token in ["pcie", "aer", "acs violation", "link width", "riser", "slot"]):
        return "PCIe"
    return ""


def _why_action_differs(summary: dict[str, Any]) -> str:
    stage = str(summary.get("decision_stage", ""))
    subtype = str(summary.get("issue_subtype", ""))
    if stage == "closure":
        return "Fixed/closed lifecycle evidence shifts action to close-out."
    if stage == "verification":
        return "Ready-for-verification signals shift action to retest gating."
    if "link width downgrade" in subtype:
        return "Subtype is link-width degradation, so action targets lane-width verification."
    if "slot-path-location" in subtype:
        return "Subtype is location-specific defect, so action targets slot/path isolation."
    if "uncorrectable AER" in subtype:
        return "Subtype is uncorrectable AER/ACS, so action stays strict on trigger-path validation."
    if "front panel button" in subtype:
        return "Subtype is reset-button signal issue, so action targets board-level signal validation."
    if subtype.startswith("memory /"):
        return "Subtype is memory margin/population/BIOS dependent, so action focuses on memory matrix verification."
    return "Action differs by combined stage + subtype evidence."


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_old_field(text: str, key: str) -> str:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"(.*?)"', text, re.S)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def _shorten(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _sanitize_markdown(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
