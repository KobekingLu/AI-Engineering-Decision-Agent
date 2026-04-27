"""Historical bug retriever with issue-profile-aware filtering and ranking."""

from __future__ import annotations

import re

from decision_agent.models import HistoricalBug, NormalizedCase

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "during",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "issue",
    "only",
    "sky",
}

SIGNAL_WEIGHTS = {
    "pcie": 3.0,
    "aer": 3.0,
    "acs": 3.0,
    "uncorrectable": 3.0,
    "corrected": 2.0,
    "slot": 2.0,
    "riser": 2.0,
    "link": 1.5,
    "width": 1.5,
    "x2": 2.0,
    "x4": 1.0,
    "nvme": 1.5,
    "ssd": 1.5,
    "reset": 2.0,
    "button": 2.0,
    "memory": 2.5,
    "dimm": 2.5,
    "rmt": 2.5,
    "vref": 2.5,
    "bios": 1.5,
    "retest": 1.0,
    "pass": 1.0,
    "rework": 1.0,
}


def retrieve_relevant_bugs(
    case_data: NormalizedCase,
    bug_rows: list[HistoricalBug],
    top_n: int = 3,
) -> list[HistoricalBug]:
    query_text = _normalize_text(_case_focus_text(case_data))
    query_tokens = set(_tokenize(query_text))
    case_profile = _build_profile(query_text)
    project_key = _normalize_project(case_data.project)

    scored_rows: list[HistoricalBug] = []
    for row in bug_rows:
        row_text = _normalize_text(row.combined_text())
        row_tokens = set(_tokenize(row_text))
        overlap = query_tokens & row_tokens

        row_profile = _build_profile(row_text)
        match_reasons: list[str] = []
        score = 0.0

        if case_profile["family"] and case_profile["family"] == row_profile["family"]:
            score += 5.0
            match_reasons.append("same issue family")
        elif case_profile["family"] and row_profile["family"] and case_profile["family"] != row_profile["family"]:
            if len(overlap) < 3:
                continue

        if case_profile["subtype"] and case_profile["subtype"] == row_profile["subtype"]:
            score += 4.0
            match_reasons.append("same issue subtype")

        trigger_overlap = sorted(case_profile["trigger"] & row_profile["trigger"])
        if trigger_overlap:
            score += 2.0 + 0.5 * len(trigger_overlap)
            match_reasons.append("same trigger condition")

        signal_overlap = sorted(case_profile["fail_signal"] & row_profile["fail_signal"])
        if signal_overlap:
            score += 2.0 + 0.5 * len(signal_overlap)
            match_reasons.append("same fail signal")

        recovery_overlap = sorted(case_profile["recovery"] & row_profile["recovery"])
        if recovery_overlap:
            score += 1.5
            match_reasons.append("same recovery pattern")

        test_case_tokens = set(_tokenize(case_data.test_case))
        if test_case_tokens and (test_case_tokens & row_tokens):
            score += 1.0
            match_reasons.append("same test context")

        if overlap:
            score += sum(_signal_weight(token) for token in overlap)

        if project_key and project_key == _normalize_project(row.project):
            score += 3.0

        if row.status.strip().lower() in {"fixed", "closed", "resolved", "support & hw rework", "ready for dqa test"}:
            score += 0.75

        if score < 2.5:
            continue

        matched_fields = _collect_matched_fields(query_tokens, row)
        matched_terms = sorted(overlap)
        scored_rows.append(
            HistoricalBug(
                bug_id=row.bug_id,
                project=row.project,
                component=row.component,
                status=row.status,
                subject=row.subject,
                description=row.description,
                quarter=row.quarter,
                source_sheet=row.source_sheet,
                score=score,
                matched_terms=matched_terms,
                matched_fields=matched_fields,
                match_reasons=sorted(set(match_reasons)),
            )
        )

    scored_rows.sort(key=lambda item: (-item.score, item.bug_id))
    return scored_rows[:top_n]


def _collect_matched_fields(
    query_tokens: set[str],
    row: HistoricalBug,
) -> dict[str, list[str]]:
    fields = {
        "project": set(_tokenize(row.project)),
        "component": set(_tokenize(row.component)),
        "subject": set(_tokenize(row.subject)),
        "description": set(_tokenize(row.description)),
        "status": set(_tokenize(row.status)),
    }
    return {
        key: sorted(tokens & query_tokens)
        for key, tokens in fields.items()
        if tokens & query_tokens
    }


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in re.findall(r"[a-z0-9]+", text.lower()):
        if raw in STOP_WORDS:
            continue
        token = _normalize_token(raw)
        if token and token not in STOP_WORDS and len(token) >= 2:
            tokens.append(token)
    return tokens


def _normalize_token(token: str) -> str:
    aliases = {
        "detected": "detect",
        "detection": "detect",
        "errors": "error",
        "reboot": "boot",
        "cycles": "cycle",
        "slots": "slot",
        "correctable": "corrected",
    }
    if token in aliases:
        return aliases[token]
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > 4 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def _normalize_project(value: str) -> str:
    return "".join(character for character in value.upper() if character.isalnum())


def _signal_weight(token: str) -> float:
    return SIGNAL_WEIGHTS.get(token, 1.0)


def _normalize_text(text: str) -> str:
    cleaned = text.lower()
    cleaned = cleaned.replace("–", "-").replace("—", "-")
    return cleaned


def _build_profile(text: str) -> dict[str, object]:
    family = ""
    subtype = ""

    if _has_any(text, ["memory margin", "rmt", "vref", "write_1d_jtag", "dimm population", "one dimm per channel"]):
        family = "memory"
        if _has_any(text, ["one dimm per channel", "population", "2dpc"]):
            subtype = "memory / DIMM population sensitive"
        elif _has_any(text, ["bios setup", "amd cbs", "bios setting", "ddr options"]):
            subtype = "memory / BIOS-setting dependent"
        else:
            subtype = "memory / margin fail"
    elif _has_any(text, ["front panel", "reset button", "rst bt", "no response"]):
        family = "power-reset"
        subtype = "power-reset / front panel button signal issue"
    elif _has_any(text, ["pcie", "aer", "acs violation", "link width", "slot", "riser"]):
        family = "PCIe"
        if _is_link_width_downgrade_signal(text):
            subtype = "PCIe / link width downgrade"
        elif _has_any(text, ["same position", "location-related", "slot swap", "riser"]):
            subtype = "PCIe / slot-path-location specific defect"
        elif _has_any(text, ["uncorrectable", "acs violation", "fatal"]):
            subtype = "PCIe / uncorrectable AER or ACS violation"
        else:
            subtype = "PCIe / corrected AER"

    return {
        "family": family,
        "subtype": subtype,
        "trigger": _extract_trigger_tokens(text),
        "fail_signal": _extract_fail_signal_tokens(text),
        "recovery": _extract_recovery_tokens(text),
    }


def _extract_trigger_tokens(text: str) -> set[str]:
    mapping = [
        ("ac_cycle", r"ac power|ac cycle|g3"),
        ("runtime_phase", r"runtime phase|initial phase"),
        ("reboot", r"reboot|power cycle"),
        ("front_panel", r"front panel|reset button"),
        ("rmt", r"\brmt\b|margin"),
    ]
    return {name for name, pattern in mapping if re.search(pattern, text)}


def _extract_fail_signal_tokens(text: str) -> set[str]:
    mapping = [
        ("corrected_aer", r"corrected error|correctable|bit14"),
        ("uncorrectable_aer", r"uncorrectable|acs violation"),
        ("link_width", r"link width|x2|x1|downgrad"),
        ("slot_location", r"same position|location-related|slot"),
        ("button_no_response", r"no response|reset button|rst"),
        ("memory_margin", r"vref|margin|write_1d_jtag"),
    ]
    return {name for name, pattern in mapping if re.search(pattern, text)}


def _extract_recovery_tokens(text: str) -> set[str]:
    mapping = [
        ("reworked_sample", r"reworked sample|rework|board change|replacement"),
        ("bios_update", r"bios config update|bios setting"),
        ("pass", r"\bpass\b|retest|verified"),
        ("ready_for_dqa", r"ready for dqa test|verifying"),
    ]
    return {name for name, pattern in mapping if re.search(pattern, text)}


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _is_link_width_downgrade_signal(text: str) -> bool:
    patterns = [
        r"link width",
        r"downgrad",
        r"instead of x4",
        r"detected with x2",
        r"pcie width x2",
        r"width x2",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _case_focus_text(case_data: NormalizedCase) -> str:
    return "\n".join(
        part
        for part in [
            case_data.subject,
            case_data.issue_description,
            case_data.log_snippet,
            case_data.comments,
            case_data.known_context,
            case_data.test_case,
        ]
        if part
    )
