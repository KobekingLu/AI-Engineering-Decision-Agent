"""Input normalization helpers for the decision-agent MVP web app."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import fitz

from web_app.ocr_utils import is_ocr_available, ocr_image_path, ocr_pdf_path


NORMALIZED_KEYS = {
    "case_id",
    "project",
    "source_type",
    "source_format",
    "source_file",
    "extraction_status",
    "bug_id",
    "reporter_role",
    "subject",
    "status",
    "status_current",
    "status_history",
    "status_history_events",
    "decision_stage_candidate",
    "resolution_state_candidate",
    "has_root_cause_signal",
    "has_solution_signal",
    "has_verification_signal",
    "has_pass_signal",
    "lifecycle_signal_items",
    "priority",
    "severity",
    "component",
    "hw_version",
    "fw_version",
    "assignee",
    "customer",
    "issue_description",
    "log_snippet",
    "comments",
    "current_config",
    "expected_config",
    "known_context",
    "reproduction",
    "fail_rate",
    "test_case",
    "test_procedure",
    "workaround",
    "attachments",
    "evidence",
}


def build_case_from_text_fields(fields: dict[str, str]) -> dict[str, Any]:
    case_id = slugify(fields.get("case_id") or fields.get("subject") or "manual_case")
    payload = {
        "case_id": case_id,
        "project": fields.get("project", "").strip(),
        "source_type": "interactive_input",
        "source_format": "text_form",
        "source_file": "",
        "extraction_status": "web_manual_input",
        "bug_id": fields.get("bug_id", "").strip(),
        "reporter_role": fields.get("reporter_role", "").strip(),
        "subject": fields.get("subject", "").strip(),
        "issue_description": fields.get("issue_description", "").strip(),
        "log_snippet": fields.get("log_snippet", "").strip(),
        "comments": fields.get("comments", "").strip(),
        "current_config": fields.get("current_config", "").strip(),
        "expected_config": fields.get("expected_config", "").strip(),
        "known_context": fields.get("known_context", "").strip(),
        "fail_rate": fields.get("fail_rate", "").strip(),
        "test_case": fields.get("test_case", "").strip(),
        "test_procedure": fields.get("test_procedure", "").strip(),
        "workaround": fields.get("workaround", "").strip(),
    }
    _finalize_payload(payload)
    return payload


def build_case_from_freeform_text(case_id: str, raw_text: str) -> dict[str, Any]:
    fields = parse_labeled_text(raw_text)
    inferred_bug_id = _find_bug_id(raw_text)
    inferred_subject = fields.get("subject") or _infer_subject(raw_text)
    inferred_fail_rate = fields.get("fail_rate") or _infer_fail_rate(raw_text)
    normalized_case_id = slugify(case_id or fields.get("case_id") or inferred_subject or "manual_case")
    payload = {
        "case_id": normalized_case_id,
        "project": fields.get("project", "") or _infer_project(raw_text),
        "source_type": "interactive_input",
        "source_format": "freeform_text",
        "source_file": "",
        "extraction_status": "web_freeform_input",
        "bug_id": fields.get("bug_id", "") or inferred_bug_id,
        "reporter_role": fields.get("reporter_role", "") or _infer_reporter_role(raw_text),
        "subject": inferred_subject or normalized_case_id,
        "status": fields.get("status", ""),
        "severity": fields.get("severity", ""),
        "component": fields.get("component", ""),
        "hw_version": fields.get("hw_version", ""),
        "fw_version": fields.get("fw_version", ""),
        "assignee": fields.get("assignee", ""),
        "customer": fields.get("customer", ""),
        "issue_description": fields.get("issue_description", raw_text.strip()),
        "log_snippet": fields.get("log_snippet", ""),
        "comments": fields.get("comments", ""),
        "current_config": fields.get("current_config", ""),
        "expected_config": fields.get("expected_config", ""),
        "known_context": fields.get("known_context", "Imported from freeform pasted text."),
        "fail_rate": inferred_fail_rate,
        "test_case": fields.get("test_case", ""),
        "test_procedure": fields.get("test_procedure", ""),
        "workaround": fields.get("workaround", ""),
    }
    _finalize_payload(payload)
    return payload


def build_case_from_txt_content(file_name: str, raw_text: str) -> dict[str, Any]:
    fields = parse_labeled_text(raw_text)
    case_id = slugify(Path(file_name).stem or fields.get("subject") or "txt_case")
    payload = {
        "case_id": case_id,
        "project": fields.get("project", ""),
        "source_type": "uploaded_file",
        "source_format": "txt",
        "source_file": file_name,
        "extraction_status": "web_txt_import",
        "bug_id": fields.get("bug_id", ""),
        "reporter_role": fields.get("reporter_role", ""),
        "subject": fields.get("subject", Path(file_name).stem),
        "issue_description": fields.get("issue_description", raw_text.strip()),
        "log_snippet": fields.get("log_snippet", ""),
        "comments": fields.get("comments", ""),
        "current_config": fields.get("current_config", ""),
        "expected_config": fields.get("expected_config", ""),
        "known_context": fields.get("known_context", "Imported from uploaded txt file."),
        "fail_rate": fields.get("fail_rate", ""),
        "test_case": fields.get("test_case", ""),
        "test_procedure": fields.get("test_procedure", ""),
        "workaround": fields.get("workaround", ""),
    }
    _finalize_payload(payload)
    return payload


def build_case_from_html_content(file_name: str, raw_text: str) -> dict[str, Any]:
    parser = _SimpleHtmlTextExtractor()
    parser.feed(raw_text)
    body_text = parser.text()
    title = parser.title_text.strip() or Path(file_name).stem
    case_id = slugify(title or Path(file_name).stem or "html_case")
    payload = {
        "case_id": case_id,
        "project": "",
        "source_type": "uploaded_file",
        "source_format": "html",
        "source_file": file_name,
        "extraction_status": "web_html_import",
        "bug_id": "",
        "reporter_role": "",
        "subject": title,
        "issue_description": body_text[:6000].strip(),
        "log_snippet": "",
        "comments": "",
        "current_config": "",
        "expected_config": "",
        "known_context": "Imported from uploaded HTML file.",
        "fail_rate": "",
        "test_case": "",
        "test_procedure": "",
        "workaround": "",
    }
    _finalize_payload(payload)
    return payload


def merge_case_payloads(
    base_payload: dict[str, Any] | None,
    incoming_payload: dict[str, Any],
    *,
    evidence_label: str,
) -> dict[str, Any]:
    if base_payload is None:
        payload = dict(incoming_payload)
        payload.setdefault("attachments", [])
        payload.setdefault("evidence", [])
        payload["attachments"] = list(payload.get("attachments") or [])
        payload["evidence"] = list(payload.get("evidence") or [])
        if evidence_label and evidence_label not in payload["attachments"]:
            payload["attachments"].append(evidence_label)
        return payload

    payload = dict(base_payload)
    payload.setdefault("attachments", [])
    payload.setdefault("evidence", [])
    payload["attachments"] = list(payload.get("attachments") or [])
    payload["evidence"] = list(payload.get("evidence") or [])
    if evidence_label and evidence_label not in payload["attachments"]:
        payload["attachments"].append(evidence_label)
    incoming_priority = evidence_label == "bundle_notes" or incoming_payload.get("source_format") == "bundle_notes"
    override_keys = {"bug_id", "subject", "project", "reporter_role", "component", "fail_rate"}

    for key, value in incoming_payload.items():
        if key in {"attachments", "evidence"}:
            continue
        if not value:
            continue
        if incoming_priority and key in override_keys:
            if key == "subject":
                if not _looks_generic_subject(str(value)) or _looks_generic_subject(str(payload.get(key, ""))):
                    payload[key] = value
                    continue
            else:
                payload[key] = value
                continue
        if key not in payload or not payload.get(key):
            payload[key] = value
        elif key in {"issue_description", "log_snippet", "comments", "known_context", "test_procedure"}:
            merged = "\n\n".join(part for part in [str(payload.get(key, "")).strip(), str(value).strip()] if part)
            payload[key] = merged

    for item in incoming_payload.get("evidence", []) or []:
        if item not in payload["evidence"]:
            payload["evidence"].append(item)
    for item in incoming_payload.get("attachments", []) or []:
        if item not in payload["attachments"]:
            payload["attachments"].append(item)
    return payload


def extract_case_payload_from_path(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_uploaded_json(path.read_bytes(), path.name), None
    if suffix == ".txt":
        try:
            raw_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None, "TXT upload must be UTF-8 encoded in this MVP."
        return build_case_from_txt_content(path.name, raw_text), None
    if suffix in {".html", ".htm"}:
        try:
            raw_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None, "HTML upload must be UTF-8 encoded in this MVP."
        return build_case_from_html_content(path.name, raw_text), None
    if suffix == ".pdf":
        return _extract_case_payload_from_pdf(path)
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return _extract_case_payload_from_image(path)
    return None, f"Unsupported file type: {path.suffix}"


def build_bundle_payload(
    *,
    case_id: str,
    uploaded_paths: list[Path],
    bundle_notes: str = "",
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    payload: dict[str, Any] | None = None
    extracted_texts: list[str] = []

    for path in uploaded_paths:
        extracted_payload, error = extract_case_payload_from_path(path)
        if error:
            errors.append(f"{path.name}: {error}")
            continue
        if extracted_payload is None:
            continue
        payload = merge_case_payloads(payload, extracted_payload, evidence_label=path.name)
        text_bits = [
            extracted_payload.get("subject", ""),
            extracted_payload.get("issue_description", ""),
            extracted_payload.get("log_snippet", ""),
            extracted_payload.get("comments", ""),
            extracted_payload.get("known_context", ""),
        ]
        combined = "\n".join(bit for bit in text_bits if bit).strip()
        if combined:
            extracted_texts.append(f"File: {path.name}\n{combined}")

    if bundle_notes.strip():
        notes_payload = build_case_from_freeform_text(case_id, bundle_notes.strip())
        notes_payload["source_type"] = "interactive_input"
        notes_payload["source_format"] = "bundle_notes"
        notes_payload["source_file"] = "bundle_notes"
        notes_payload["extraction_status"] = "web_bundle_notes"
        payload = merge_case_payloads(payload, notes_payload, evidence_label="bundle_notes")

    if bundle_notes.strip():
        extracted_texts.append(f"Bundle Notes:\n{bundle_notes.strip()}")

    if payload is None and extracted_texts:
        payload = build_case_from_freeform_text(case_id, "\n\n".join(extracted_texts))
    elif payload is not None:
        payload["case_id"] = slugify(case_id or str(payload.get("case_id") or payload.get("subject") or "case_bundle"))
        payload["source_type"] = "uploaded_bundle"
        payload["source_format"] = "multi_file_bundle"
        payload["source_file"] = ", ".join(path.name for path in uploaded_paths)
        payload["extraction_status"] = "web_multi_file_bundle"
        if extracted_texts:
            payload["known_context"] = _summarize_bundle_context(
                payload=payload,
                uploaded_paths=uploaded_paths,
                extracted_texts=extracted_texts,
            )

        _finalize_payload(payload)

    return payload, errors


def parse_uploaded_json(content: bytes, file_name: str) -> dict[str, Any]:
    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Uploaded JSON must be a single object for one normalized case.")

    if not (NORMALIZED_KEYS & set(data)):
        raise ValueError("Uploaded JSON does not look like a normalized single-case input.")

    data.setdefault("case_id", slugify(Path(file_name).stem))
    data.setdefault("source_type", "uploaded_file")
    data.setdefault("source_format", "json")
    data.setdefault("source_file", file_name)
    data.setdefault("extraction_status", "web_json_import")
    _finalize_payload(data)
    return data


def parse_labeled_text(raw_text: str) -> dict[str, str]:
    lines = [line.rstrip() for line in raw_text.splitlines()]
    mapping: dict[str, list[str]] = {}
    current_key = "issue_description"
    mapping[current_key] = []
    pending_key: str | None = None

    aliases = {
        "case id": "case_id",
        "bug id": "bug_id",
        "project": "project",
        "reporter": "reporter_role",
        "reporter role": "reporter_role",
        "issue finder": "reporter_role",
        "subject": "subject",
        "title": "subject",
        "issue": "issue_description",
        "issue description": "issue_description",
        "description": "issue_description",
        "log": "log_snippet",
        "log snippet": "log_snippet",
        "comment": "comments",
        "comments": "comments",
        "current config": "current_config",
        "expected config": "expected_config",
        "context": "known_context",
        "known context": "known_context",
        "fail rate": "fail_rate",
        "test case": "test_case",
        "test procedure": "test_procedure",
        "workaround": "workaround",
        "status": "status",
        "severity": "severity",
        "component": "component",
        "hw version": "hw_version",
        "fw version": "fw_version",
        "assignee": "assignee",
        "customer": "customer",
    }
    section_aliases = {
        "test case": "test_case",
        "expectation": "expected_config",
        "issue description": "issue_description",
        "additional information": "comments",
        "fail rate": "fail_rate",
        "test procedure": "test_procedure",
        "test configuration": "current_config",
    }

    for line in lines:
        if not line.strip():
            if pending_key:
                pending_key = None
                current_key = "issue_description"
            if mapping.get(current_key):
                mapping[current_key].append("")
            continue

        section_match = re.match(r"^\s*\[([A-Za-z0-9 _/-]+)\]\s*$", line)
        if section_match:
            raw_section = section_match.group(1).strip().lower()
            normalized_section = section_aliases.get(raw_section)
            if normalized_section:
                current_key = normalized_section
                mapping.setdefault(current_key, [])
                pending_key = None
                continue

        label_only_match = re.match(r"^\s*([A-Za-z0-9 _/-]+)\s*:\s*$", line)
        if label_only_match:
            raw_key = label_only_match.group(1).strip().lower()
            normalized_key = aliases.get(raw_key)
            if normalized_key:
                pending_key = normalized_key
                mapping.setdefault(normalized_key, [])
                continue

        if pending_key:
            mapping.setdefault(pending_key, []).append(line.strip())
            pending_key = None
            current_key = "issue_description"
            continue

        match = re.match(r"^\s*([A-Za-z0-9 _/-]+)\s*:\s*(.*)$", line)
        if match:
            raw_key = match.group(1).strip().lower()
            normalized_key = aliases.get(raw_key)
            if normalized_key:
                current_key = normalized_key
                mapping.setdefault(current_key, [])
                if match.group(2).strip():
                    mapping[current_key].append(match.group(2).strip())
                continue

        mapping.setdefault(current_key, []).append(line.strip())

    return {
        key: "\n".join(value).strip()
        for key, value in mapping.items()
        if "\n".join(value).strip()
    }


def save_uploaded_file(target_path: Path, content: bytes) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(content)
    return target_path


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_").lower()
    return slug or "case"


def _find_bug_id(raw_text: str) -> str:
    match = re.search(r"Bug\s*#\s*(\d+)", raw_text, re.IGNORECASE)
    return match.group(1) if match else ""


def _infer_subject(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    for index, line in enumerate(lines[:12]):
        if re.match(r"Bug\s*#\s*\d+", line, re.IGNORECASE):
            following = []
            for candidate in lines[index + 1 : index + 4]:
                lowered = candidate.lower()
                if lowered.startswith(("added by", "updated by", "status", "priority", "assignee")):
                    break
                if len(candidate) < 4:
                    continue
                following.append(candidate)
            if following:
                return re.sub(r"\s+", " ", " ".join([line] + following[:2])).strip()
            return re.sub(r"\s+", " ", line).strip()
        if "acs violation" in line.lower() or "uncorrectable error" in line.lower():
            return re.sub(r"\s+", " ", line).strip()
        if "nvme" in line.lower() and len(line) > 12:
            if index + 2 < len(lines) and lines[index + 1].upper() in {"OPEN", "NEW", "CLOSED"}:
                return lines[index + 2]
            if index + 1 < len(lines):
                return lines[index + 1]
        if len(line) > 12 and not line.endswith(":"):
            return line
    return ""


def _infer_project(raw_text: str) -> str:
    match = re.search(r"\b([A-Z]{2,5}-\d{3,5}[A-Z]?\d?)\b", raw_text)
    return match.group(1) if match else ""


def _infer_reporter_role(raw_text: str) -> str:
    match = re.search(r"\b(AE|DQA|RD|PM)\b", raw_text)
    return match.group(1) if match else ""


def _infer_fail_rate(raw_text: str) -> str:
    labeled_match = re.search(r"fail rate[^0-9]*(\d+\s*/\s*\d+)", raw_text, re.IGNORECASE | re.DOTALL)
    if labeled_match:
        return labeled_match.group(1).replace(" ", "")
    all_ratios = re.findall(r"\b(\d+\s*/\s*\d+)\b", raw_text)
    if all_ratios:
        return all_ratios[-1].replace(" ", "")
    return ""


def _finalize_payload(payload: dict[str, Any]) -> None:
    combined_text = " ".join(
        str(payload.get(key, "") or "")
        for key in [
            "subject",
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

    if not payload.get("bug_id"):
        payload["bug_id"] = _find_bug_id(combined_text)
    if not payload.get("project"):
        payload["project"] = _infer_project(combined_text)
    if not payload.get("reporter_role"):
        payload["reporter_role"] = _infer_reporter_role(combined_text)
    elif str(payload.get("reporter_role", "")).upper() not in {"AE", "DQA", "RD", "PM"}:
        payload["reporter_role"] = _infer_reporter_role(combined_text)
    if not payload.get("fail_rate"):
        ratio_match = re.search(r"\b\d+\s*/\s*\d+\b", combined_text)
        if ratio_match:
            payload["fail_rate"] = ratio_match.group(0)

    focus_text = " ".join(
        str(payload.get(key, "") or "")
        for key in ["subject", "issue_description", "comments", "test_case", "known_context"]
    )
    inferred_component = _infer_component_label(focus_text or combined_text)
    if inferred_component and not payload.get("component"):
        payload["component"] = inferred_component

    inferred_status = _infer_status_label(
        str(payload.get("status", "") or ""),
        focus_text=focus_text or combined_text,
    )
    if inferred_status:
        payload["status"] = inferred_status

    if _looks_generic_subject(str(payload.get("subject", "") or "")):
        better_subject = _infer_subject(combined_text)
        if better_subject:
            payload["subject"] = better_subject

    payload["issue_description"] = _clean_issue_description(
        str(payload.get("issue_description", "") or ""),
        fallback_text=combined_text,
    )
    payload["current_config"] = _clean_current_config(
        str(payload.get("current_config", "") or ""),
        fallback_text=combined_text,
    )
    payload["expected_config"] = _clean_expected_config(
        str(payload.get("expected_config", "") or ""),
        fallback_text=combined_text,
    )
    payload["comments"] = _clean_generic_block(str(payload.get("comments", "") or ""))

    if not payload.get("log_snippet"):
        payload["log_snippet"] = _extract_log_snippet(combined_text)

    if not payload.get("comments") and payload.get("attachments"):
        payload["comments"] = "Attachments included: " + ", ".join(payload.get("attachments") or [])

    lifecycle_sources = _iter_lifecycle_source_texts(payload)
    status_history_events = _extract_status_history_events(lifecycle_sources)
    status_history = [item.get("to", "") for item in status_history_events if item.get("to")]
    status_current = _resolve_status_current(payload.get("status", ""), status_history)
    if status_current:
        payload["status_current"] = status_current
        payload["status"] = status_current
    elif payload.get("status"):
        payload["status_current"] = str(payload.get("status", ""))
    if status_history:
        payload["status_history"] = status_history
    if status_history_events:
        payload["status_history_events"] = status_history_events

    lifecycle_signals = _infer_lifecycle_signals(lifecycle_sources)
    payload["has_root_cause_signal"] = lifecycle_signals["has_root_cause_signal"]
    payload["has_solution_signal"] = lifecycle_signals["has_solution_signal"]
    payload["has_verification_signal"] = lifecycle_signals["has_verification_signal"]
    payload["has_pass_signal"] = lifecycle_signals["has_pass_signal"]
    payload["lifecycle_signal_items"] = _extract_lifecycle_signal_items(lifecycle_sources)
    stage_candidate, resolution_candidate = _build_lifecycle_candidates(
        status_current=str(payload.get("status_current", "") or payload.get("status", "") or ""),
        has_root_cause_signal=payload["has_root_cause_signal"],
        has_solution_signal=payload["has_solution_signal"],
        has_verification_signal=payload["has_verification_signal"],
        has_pass_signal=payload["has_pass_signal"],
    )
    if stage_candidate:
        payload["decision_stage_candidate"] = stage_candidate
    if resolution_candidate:
        payload["resolution_state_candidate"] = resolution_candidate


def _summarize_bundle_context(
    *,
    payload: dict[str, Any],
    uploaded_paths: list[Path],
    extracted_texts: list[str],
) -> str:
    combined_text = "\n".join(extracted_texts)
    detected_signals: list[str] = []
    for label, pattern in [
        ("PCIe AER / ACS violation", r"\baer\b|\bacs violation\b"),
        ("Uncorrectable error", r"\buncorrectable\b"),
        ("Corrected error", r"\bcorrected error\b"),
        ("NVMe / SSD path", r"\bnvme\b|\bssd\b"),
        ("Power-cycle or runtime phase", r"runtime phase|initial phase|power cycle|reboot"),
        ("Fail-rate evidence", r"\b\d+\s*/\s*\d+\b|fail rate"),
    ]:
        if re.search(pattern, combined_text, re.IGNORECASE):
            detected_signals.append(label)

    summary_lines = [
        "Bundle summary:",
        f"- Attachments: {', '.join(path.name for path in uploaded_paths)}",
    ]

    if payload.get("bug_id"):
        summary_lines.append(f"- Bug ID: {payload['bug_id']}")
    if payload.get("project"):
        summary_lines.append(f"- Project: {payload['project']}")
    if payload.get("component"):
        summary_lines.append(f"- Component: {payload['component']}")
    if payload.get("fail_rate"):
        summary_lines.append(f"- Fail rate: {payload['fail_rate']}")
    if detected_signals:
        summary_lines.append(f"- Detected signals: {', '.join(detected_signals)}")

    summary_lines.append("")
    summary_lines.append("Raw evidence was merged from uploaded files and optional notes.")
    return "\n".join(summary_lines).strip()


def _clean_issue_description(text: str, *, fallback_text: str) -> str:
    source = _extract_section(
        text or fallback_text,
        ["issue description", "[issue description]"],
        [
            "additional information",
            "[additional information]",
            "fail rate",
            "[fail rate]",
            "test procedure",
            "[test procedure]",
            "test configuration",
            "[test configuration]",
            "files",
            "attachments",
            "notes",
            "history",
            "updated by",
            "related issues",
            "subtasks",
        ],
    )
    if not source:
        source = _extract_section(
            text or fallback_text,
            ["description"],
            [
                "steps to reproduce",
                "actual result",
                "expected result",
                "current config",
                "test configuration",
                "[test configuration]",
                "files",
                "attachments",
                "notes",
                "history",
                "updated by",
                "related issues",
                "subtasks",
            ],
        )
    if not source:
        source = text.strip() or fallback_text
    cleaned = _clean_generic_block(source)
    cleaned = _drop_meta_lines(cleaned)
    cleaned = _collapse_block(cleaned)
    return _limit_lines(cleaned, 14)


def _clean_current_config(text: str, *, fallback_text: str) -> str:
    source = text.strip() or _extract_section(
        fallback_text,
        ["test configuration", "[test configuration]", "current config", "system information", "[system information]"],
        [
            "expected config",
            "expectation",
            "description",
            "files",
            "attachments",
            "notes",
            "history",
            "updated by",
            "related issues",
            "subtasks",
        ],
    )
    cleaned = _clean_generic_block(source)
    cleaned = _drop_meta_lines(cleaned)
    filtered_lines = []
    for line in cleaned.splitlines():
        lowered = line.lower()
        if lowered.startswith(("files", "subtasks", "related issues", "spent time", "fix_reject_counts")):
            break
        if any(token in lowered for token in ["added by", "updated by", "start date", "due date", "assigned to", "priority", "category"]):
            continue
        filtered_lines.append(line)
    cleaned = _collapse_block("\n".join(filtered_lines))
    return _limit_lines(cleaned, 12)


def _clean_expected_config(text: str, *, fallback_text: str) -> str:
    source = text.strip() or _extract_section(
        fallback_text,
        ["expected config", "expectation", "[expectation]"],
        [
            "description",
            "actual result",
            "files",
            "attachments",
            "notes",
            "history",
            "updated by",
        ],
    )
    cleaned = _collapse_block(_drop_meta_lines(_clean_generic_block(source)))
    return _limit_lines(cleaned, 10)


def _extract_section(text: str, starters: list[str], stoppers: list[str]) -> str:
    if not text.strip():
        return ""
    lines = [line.rstrip() for line in text.splitlines()]
    started = False
    bucket: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        lowered = line.lower().strip(":-[] ")
        if not started:
            if any(lowered == marker or lowered.startswith(marker) for marker in starters):
                started = True
            continue
        if any(lowered == marker or lowered.startswith(marker) for marker in stoppers):
            break
        bucket.append(raw_line)
    return "\n".join(bucket).strip()


def _drop_meta_lines(text: str) -> str:
    if not text.strip():
        return ""
    meta_prefixes = (
        "added by",
        "updated by",
        "start date",
        "due date",
        "assigned to",
        "priority",
        "category",
        "status",
        "target version",
        "estimated time",
        "spent time",
        "fix_reject_counts",
    )
    kept = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if kept and kept[-1] != "":
                kept.append("")
            continue
        lowered = line.lower()
        if lowered in {"open", "new", "closed", "-", "n/a"}:
            continue
        if lowered.startswith(meta_prefixes):
            continue
        if re.fullmatch(r"[A-Z_]+:", line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _clean_generic_block(text: str) -> str:
    cleaned = text.replace("\u00a0", " ").replace("\t", " ")
    cleaned = cleaned.replace("бў", "->").replace("→", "->")
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
    cleaned = re.sub(r"(?i)^description\s*:?\s*", "", cleaned.strip())
    return cleaned.strip()


def _collapse_block(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" -")
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if lines and line == lines[-1]:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _limit_lines(text: str, max_lines: int) -> str:
    if not text:
        return ""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + "\n..."


def _iter_lifecycle_source_texts(payload: dict[str, Any]) -> list[tuple[str, str]]:
    source_fields = [
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
    for field in source_fields:
        text = str(payload.get(field, "") or "").strip()
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
            from_status = _infer_status_label("", focus_text=match.group(1))
            to_status = _infer_status_label("", focus_text=match.group(2))
            if not to_status:
                continue
            matched_text = match.group(0).strip()
            event = {
                "from": from_status,
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


def _resolve_status_current(current_status: object, status_history: list[str]) -> str:
    current = _infer_status_label(str(current_status or ""), focus_text="")
    if not status_history:
        return current
    latest = status_history[-1]
    if not current:
        return latest
    current_rank = _status_rank(current)
    latest_rank = _status_rank(latest)
    if latest_rank > current_rank:
        return latest
    return current


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


def _infer_lifecycle_signals(source: str | list[tuple[str, str]]) -> dict[str, bool]:
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


def _infer_component_label(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["memory margin", "rmt", "vref", "dimm"]):
        return "Memory subsystem"
    if any(token in lowered for token in ["front panel", "reset button", "rst bt", "no response"]):
        return "Front panel reset"
    if any(token in lowered for token in ["link width", "downgraded", "x2", "x1"]):
        return "PCIe slot path"
    if any(token in lowered for token in ["corrected error", "uncorrectable", "acs violation", "aer"]):
        return "PCIe path"
    if any(token in lowered for token in ["nvme", "ssd", "u.2", "m.2"]):
        return "NVMe SSD"
    if any(token in lowered for token in ["gpu", "l40s"]):
        return "GPU"
    if any(token in lowered for token in ["x710", "cx-7", "nic", "ethernet", "lan"]):
        return "NIC"
    if any(token in lowered for token in ["pcie"]):
        return "PCIe device"
    return ""


def _infer_status_label(current_status: str, *, focus_text: str) -> str:
    lowered_status = current_status.strip().lower()
    known = {
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
    if lowered_status in known:
        return known[lowered_status]

    lowered = focus_text.lower()
    status_changes = re.findall(r"status changed from .*? to ([a-z &]+)", lowered)
    if status_changes:
        candidate = status_changes[-1].strip()
        if candidate in known:
            return known[candidate]

    for key in [
        "closed",
        "fixed",
        "verifying",
        "ready for dqa test",
        "support & hw rework",
        "fixing",
        "clarifying",
        "open",
        "new",
    ]:
        if key in lowered:
            return known.get(key, key.title())
    return ""


def _looks_generic_subject(subject: str) -> bool:
    lowered = subject.strip().lower()
    return lowered in {"", "error description", "case_bundle", "bundle_notes"}


def _extract_log_snippet(text: str, *, max_lines: int = 6) -> str:
    useful_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if any(
            token in lowered
            for token in [
                "aer",
                "acs violation",
                "uncorrectable",
                "corrected error",
                "rasdaemon",
                "dmesg",
                "device_id",
                "vendor_id",
                "root complex",
            ]
        ):
            useful_lines.append(line)
        if len(useful_lines) >= max_lines:
            break
    return "\n".join(useful_lines)


class _SimpleHtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._title_chunks: list[str] = []
        self._in_title = False
        self._ignore_depth = 0

    @property
    def title_text(self) -> str:
        return " ".join(self._title_chunks)

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = True
        if lowered in {"script", "style"}:
            self._ignore_depth += 1

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = False
        if lowered in {"script", "style"} and self._ignore_depth > 0:
            self._ignore_depth -= 1
        if lowered in {"p", "div", "section", "article", "br", "li", "tr", "h1", "h2", "h3"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignore_depth:
            return
        cleaned = data.strip()
        if not cleaned:
            return
        self._chunks.append(cleaned)
        if self._in_title:
            self._title_chunks.append(cleaned)

    def text(self) -> str:
        text = " ".join(self._chunks)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n\s+", "\n", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


def _extract_case_payload_from_pdf(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    text = _extract_pdf_text(path)
    if not text and not is_ocr_available():
        return None, "This PDF needs OCR, but OCR is not available in the current environment."
    if not text:
        text = ocr_pdf_path(path)
    if not text:
        return None, "No readable text was extracted from this PDF."

    payload = build_case_from_freeform_text(path.stem, text)
    payload["source_file"] = path.name
    payload["source_format"] = "pdf"
    payload["extraction_status"] = "web_pdf_import"
    payload.setdefault("attachments", []).append(path.name)
    return payload, None


def _extract_case_payload_from_image(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not is_ocr_available():
        return None, "This image needs OCR, but OCR is not available in the current environment."
    text = ocr_image_path(path)
    if not text:
        return None, "No readable text was extracted from this image."
    payload = build_case_from_freeform_text(path.stem, text)
    payload["source_file"] = path.name
    payload["source_format"] = "image_ocr"
    payload["extraction_status"] = "web_image_ocr_import"
    payload.setdefault("attachments", []).append(path.name)
    return payload, None


def _extract_pdf_text(path: Path, *, max_pages: int = 8) -> str:
    doc = fitz.open(path)
    chunks: list[str] = []
    for index in range(min(doc.page_count, max_pages)):
        text = (doc.load_page(index).get_text("text") or "").strip()
        if text:
            chunks.append(text)
    return "\n\n".join(chunks).strip()
