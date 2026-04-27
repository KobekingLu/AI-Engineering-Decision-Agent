"""File loading helpers for the minimal decision-agent flow."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
import re

from decision_agent.models import HistoricalBug, NormalizedCase, SeverityRules
from decision_agent.pdf_intake import load_case_from_pdf


def load_normalized_case(path: Path) -> NormalizedCase:
    if path.suffix.lower() == ".pdf":
        return load_case_from_pdf(path)
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data.setdefault("case_id", path.stem)
        data.setdefault("source_file", str(path))
        data.setdefault("source_format", data.get("source_format") or "json")
        data.setdefault("extraction_status", data.get("extraction_status") or "provided_json")
        _fill_lifecycle_defaults(data)
    return NormalizedCase.from_dict(data)


def load_bug_rows(path: Path) -> list[HistoricalBug]:
    rows: list[HistoricalBug] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                HistoricalBug(
                    bug_id=str(row.get("bug_id", "") or ""),
                    project=str(row.get("project", "") or ""),
                    component=str(row.get("component", "") or ""),
                    status=str(row.get("status", "") or ""),
                    subject=str(row.get("subject", "") or ""),
                    description=str(row.get("description", "") or ""),
                    quarter=str(row.get("quarter", "") or ""),
                    source_sheet=str(row.get("source_sheet", "") or ""),
                )
            )
    return rows


def load_severity_rules(path: Path) -> SeverityRules:
    severity_levels: dict[str, list[str]] = {}
    general_rule = ""
    current_level = ""

    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line == "severity_levels:":
                continue
            if line.startswith("general_rule:"):
                general_rule = line.split(":", 1)[1].strip()
                continue
            if line.endswith(":") and not line.startswith("- "):
                current_level = line[:-1].strip()
                severity_levels.setdefault(current_level, [])
                continue
            if line.startswith("- ") and current_level:
                severity_levels[current_level].append(line[2:].strip())

    return SeverityRules(severity_levels=severity_levels, general_rule=general_rule)


def load_summary_template(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _fill_lifecycle_defaults(data: dict[str, Any]) -> None:
    source_texts = _iter_lifecycle_source_texts(data)
    combined_text = " ".join(
        str(data.get(key, "") or "")
        for key in [
            "subject",
            "status",
            "issue_description",
            "log_snippet",
            "comments",
            "known_context",
            "current_config",
            "expected_config",
            "test_case",
            "test_procedure",
            "workaround",
        ]
    )
    status_history_events = data.get("status_history_events") or _extract_status_history_events(source_texts)
    if status_history_events:
        data["status_history_events"] = status_history_events
    status_history = data.get("status_history") or [item.get("to", "") for item in status_history_events if item.get("to")]
    if status_history:
        data["status_history"] = status_history

    status_current = str(data.get("status_current", "") or "")
    if not status_current:
        status_current = _resolve_status_current(str(data.get("status", "") or ""), status_history or [], combined_text)
    if status_current:
        data["status_current"] = status_current
        data["status"] = status_current

    flags = _infer_lifecycle_flags(source_texts)
    for key, value in flags.items():
        data.setdefault(key, value)
    data.setdefault("lifecycle_signal_items", _extract_lifecycle_signal_items(source_texts))

    stage_candidate, resolution_candidate = _build_lifecycle_candidates(
        status_current=str(data.get("status_current", "") or data.get("status", "") or ""),
        has_root_cause_signal=bool(data.get("has_root_cause_signal")),
        has_solution_signal=bool(data.get("has_solution_signal")),
        has_verification_signal=bool(data.get("has_verification_signal")),
        has_pass_signal=bool(data.get("has_pass_signal")),
    )
    data.setdefault("decision_stage_candidate", stage_candidate)
    data.setdefault("resolution_state_candidate", resolution_candidate)


def _iter_lifecycle_source_texts(data: dict[str, Any]) -> list[tuple[str, str]]:
    fields = [
        "status_current",
        "status",
        "subject",
        "comments",
        "known_context",
        "test_procedure",
        "workaround",
        "issue_description",
        "log_snippet",
        "current_config",
        "expected_config",
    ]
    items: list[tuple[str, str]] = []
    for field in fields:
        text = str(data.get(field, "") or "").strip()
        if text:
            items.append((field, text))
    return items


def _coerce_source_texts(source: str | list[tuple[str, str]]) -> list[tuple[str, str]]:
    if isinstance(source, str):
        return [("combined_text", source)] if source.strip() else []
    return [(field, text) for field, text in source if str(text).strip()]


def _extract_status_history_events(source: str | list[tuple[str, str]]) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for source_field, text in _coerce_source_texts(source):
        matches = re.finditer(r"status changed from ([a-z0-9 &/_-]+?) to ([a-z0-9 &/_-]+)", text.lower())
        for match in matches:
            to_status = _normalize_status_label(match.group(2))
            if not to_status:
                continue
            matched_text = match.group(0).strip()
            event = {
                "from": _normalize_status_label(match.group(1)),
                "to": to_status,
                "source_field": source_field,
                "matched_text": matched_text,
                "matched_excerpt": _build_excerpt(text, matched_text),
            }
            key = (event["from"], event["to"], event["source_field"], event["matched_text"])
            if key in seen:
                continue
            seen.add(key)
            events.append(event)
    return events


def _resolve_status_current(current_status: str, status_history: list[str], combined_text: str) -> str:
    current = _normalize_status_label(current_status or "")
    if not current:
        current = _infer_status_from_text(combined_text)
    if not status_history:
        return current
    latest = status_history[-1]
    if not current:
        return latest
    if _status_rank(latest) > _status_rank(current):
        return latest
    return current


def _infer_status_from_text(text: str) -> str:
    lowered = text.lower()
    for label in [
        "closed",
        "resolved",
        "fixed",
        "verifying",
        "ready for dqa test",
        "support & hw rework",
        "fixing",
        "clarifying",
        "open",
        "new",
    ]:
        if label in lowered:
            return _normalize_status_label(label)
    return ""


def _normalize_status_label(value: str) -> str:
    lowered = str(value or "").strip().lower()
    mapping = {
        "new": "New",
        "open": "Open",
        "clarifying": "Clarifying",
        "fixing": "Fixing",
        "support & hw rework": "Support & HW Rework",
        "ready for dqa test": "Ready for DQA test",
        "verifying": "Verifying",
        "fixed": "Fixed",
        "closed": "Closed",
        "resolved": "Resolved",
    }
    return mapping.get(lowered, "")


def _status_rank(status: str) -> int:
    order = {
        "New": 1,
        "Open": 1,
        "Clarifying": 2,
        "Fixing": 3,
        "Support & HW Rework": 3,
        "Ready for DQA test": 4,
        "Verifying": 4,
        "Fixed": 5,
        "Resolved": 6,
        "Closed": 6,
    }
    return order.get(status, 0)


def _infer_lifecycle_flags(source: str | list[tuple[str, str]]) -> dict[str, bool]:
    signal_items = _extract_lifecycle_signal_items(source)
    signal_types = {item.get("signal_type", "") for item in signal_items}
    return {
        "has_root_cause_signal": "root-cause signal" in signal_types,
        "has_solution_signal": "solution/fix signal" in signal_types,
        "has_verification_signal": "verification signal" in signal_types,
        "has_pass_signal": "PASS signal" in signal_types,
    }


def _extract_lifecycle_signal_items(source: str | list[tuple[str, str]]) -> list[dict[str, str]]:
    signal_patterns = [
        ("root-cause signal", ["root cause", "this issue cause by", "cause by"]),
        (
            "solution/fix signal",
            [
                "solution",
                "to fix this issue",
                "fixed by",
                "reworked sample",
                "replacement board",
                "board change",
                "bios config update",
                "config update",
                "0 ohm",
            ],
        ),
        ("verification signal", ["ready for dqa test", "verifying", "verification", "retest", "verify"]),
        ("PASS signal", ["retest pass", "stable pass", "test result is pass", "verified", "pass"]),
    ]
    items: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for source_field, text in _coerce_source_texts(source):
        lowered = text.lower()
        for signal_type, tokens in signal_patterns:
            for token in tokens:
                if token in lowered:
                    key = (signal_type, token, source_field)
                    if key in seen:
                        break
                    seen.add(key)
                    items.append(
                        {
                            "signal_type": signal_type,
                            "source_field": source_field,
                            "matched_text": token,
                            "matched_excerpt": _build_excerpt(text, token),
                        }
                    )
                    break
    return items


def _build_excerpt(text: str, token: str, max_chars: int = 140) -> str:
    lowered = text.lower()
    token_lower = token.lower()
    index = lowered.find(token_lower)
    if index < 0:
        compact = " ".join(text.split())
        return compact[:max_chars] + ("..." if len(compact) > max_chars else "")
    start = max(0, index - 45)
    end = min(len(text), index + len(token) + 65)
    excerpt = " ".join(text[start:end].split())
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."
    return excerpt


def _build_lifecycle_candidates(
    *,
    status_current: str,
    has_root_cause_signal: bool,
    has_solution_signal: bool,
    has_verification_signal: bool,
    has_pass_signal: bool,
) -> tuple[str, str]:
    status = status_current.strip().lower()
    if status in {"closed", "resolved"} or (status == "fixed" and has_pass_signal):
        return "closure", "closed" if status in {"closed", "resolved"} else "fixed_verified"
    if status in {"ready for dqa test", "verifying"} or has_verification_signal or status == "fixed":
        return "verification", "fixed_pending_verification" if status == "fixed" else "ready_for_verification"
    if status in {"fixing", "support & hw rework"} or has_root_cause_signal or has_solution_signal:
        return "root-cause identified", "fix_defined"
    if status in {"clarifying", "in progress"}:
        return "investigation", "investigating"
    return "triage", "open"
