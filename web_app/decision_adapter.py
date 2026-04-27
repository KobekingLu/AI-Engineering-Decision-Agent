"""Thin bridge between the web app and the existing decision-agent flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from decision_agent.service import analyze_single_case
from web_app.intake import (
    build_bundle_payload,
    extract_case_payload_from_path,
    save_uploaded_file,
    slugify,
)


def analyze_case_payload(
    payload: dict[str, Any],
    *,
    output_root: Path,
) -> tuple[dict[str, Any], Path]:
    case_id = slugify(str(payload.get("case_id") or payload.get("subject") or "manual_case"))
    payload = dict(payload)
    payload["case_id"] = case_id
    summary_path = output_root / "json" / f"{case_id}.decision_summary.json"
    summary = analyze_single_case(payload, output_path=summary_path)
    return summary, summary_path


def analyze_uploaded_path(
    source_name: str,
    content: bytes,
    *,
    output_root: Path,
    sidecar_name: str | None = None,
    sidecar_content: bytes | None = None,
) -> tuple[dict[str, Any] | None, Path | None, str | None]:
    uploads_root = output_root / "uploads"
    upload_path = save_uploaded_file(uploads_root / source_name, content)
    case_input: Path | dict[str, Any]

    if sidecar_name and sidecar_content:
        case_input, sidecar_error = _load_sidecar_case_input(
            upload_path,
            sidecar_name,
            sidecar_content,
        )
        if sidecar_error:
            return None, None, sidecar_error
    else:
        case_input, single_error = extract_case_payload_from_path(upload_path)
        if single_error:
            return None, None, single_error
        if case_input is None:
            return None, None, "The uploaded case could not be normalized."

    try:
        summary_path = output_root / "json" / f"{upload_path.stem}.decision_summary.json"
        summary = analyze_single_case(case_input, output_path=summary_path)
        return summary, summary_path, None
    except Exception as exc:
        return None, None, f"Unable to analyze the uploaded file: {exc}"


def analyze_uploaded_bundle(
    files: list[tuple[str, bytes]],
    *,
    output_root: Path,
    case_id: str = "",
    bundle_notes: str = "",
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, Path | None, list[str]]:
    bundle_id = slugify(case_id or "case_bundle")
    bundle_root = output_root / "uploads" / bundle_id
    uploaded_paths: list[Path] = []
    for source_name, content in files:
        uploaded_paths.append(save_uploaded_file(bundle_root / source_name, content))

    payload, errors = build_bundle_payload(
        case_id=bundle_id,
        uploaded_paths=uploaded_paths,
        bundle_notes=bundle_notes,
    )
    if payload is None:
        return None, None, None, errors or ["No readable evidence was extracted from the uploaded files."]

    try:
        summary_path = output_root / "json" / f"{payload['case_id']}.decision_summary.json"
        summary = analyze_single_case(payload, output_path=summary_path)
        return summary, payload, summary_path, errors
    except Exception as exc:
        errors.append(f"Unable to analyze the merged case bundle: {exc}")
        return None, payload, None, errors


def _load_sidecar_case_input(
    upload_path: Path,
    sidecar_name: str,
    sidecar_content: bytes,
) -> tuple[Path | dict[str, Any] | None, str | None]:
    sidecar_suffix = Path(sidecar_name).suffix.lower()
    if sidecar_suffix == ".json":
        save_uploaded_file(upload_path.with_suffix(".json"), sidecar_content)
        case_input, error = extract_case_payload_from_path(upload_path.with_suffix(".json"))
        if error:
            return None, error
        if case_input is None:
            return None, "Unable to read sidecar JSON."
        case_input.setdefault("source_file", upload_path.name)
        return case_input, None

    if sidecar_suffix == ".txt":
        save_uploaded_file(upload_path.with_suffix(".txt"), sidecar_content)
        case_input, error = extract_case_payload_from_path(upload_path.with_suffix(".txt"))
        if error:
            return None, error
        if case_input is None:
            return None, "Unable to read sidecar TXT."
        case_input["case_id"] = slugify(upload_path.stem)
        case_input["source_file"] = upload_path.name
        case_input["source_format"] = upload_path.suffix.lower().lstrip(".") + "_with_txt_sidecar"
        return case_input, None

    return None, "Sidecar must be JSON or TXT in this MVP."
