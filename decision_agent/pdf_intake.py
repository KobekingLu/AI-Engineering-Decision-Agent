"""Helpers for PDF-backed case inputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from decision_agent.models import NormalizedCase


def load_case_from_pdf(path: Path) -> NormalizedCase:
    """Load a PDF case by resolving a normalized sidecar JSON when available."""

    for candidate in _sidecar_candidates(path):
        if candidate.exists():
            with candidate.open(encoding="utf-8") as handle:
                data = json.load(handle)
            data.setdefault("case_id", path.stem)
            data.setdefault("source_file", str(path))
            data.setdefault("source_format", "pdf_image")
            data.setdefault("source_type", "engineering_issue")
            data.setdefault("extraction_status", "normalized_from_pdf_sidecar")
            return NormalizedCase.from_dict(data)

    metadata_case = _case_from_pdf_metadata(path)
    metadata_case.extraction_status = "metadata_only_requires_manual_normalization"
    return metadata_case


def _sidecar_candidates(path: Path) -> list[Path]:
    return [
        path.with_suffix(".json"),
        path.with_suffix(".normalized.json"),
    ]


def _case_from_pdf_metadata(path: Path) -> NormalizedCase:
    title = ""
    try:
        import fitz

        document = fitz.open(path)
        title = str((document.metadata or {}).get("title", "") or "")
    except Exception:
        title = ""

    bug_id = ""
    subject = title
    match = re.search(r"Bug\s+#(\d+)[_:]?\s*(.*)", title, re.IGNORECASE)
    if match:
        bug_id = match.group(1).strip()
        subject = match.group(2).strip()

    return NormalizedCase(
        case_id=path.stem,
        bug_id=bug_id,
        subject=subject,
        source_type="engineering_issue",
        source_format="pdf_image",
        source_file=str(path),
        known_context="Image-based PDF detected. No OCR engine is installed, so a normalized JSON sidecar is still needed for detailed analysis.",
    )
