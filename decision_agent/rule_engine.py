"""Issue taxonomy, lifecycle staging, and risk/action logic."""

from __future__ import annotations

import re

from decision_agent.models import HistoricalBug, NormalizedCase, SeverityRules

SEVERITY_ORDER = ["Critical", "Major", "Minor", "Low", "Unknown"]


def infer_issue_type(case_data: NormalizedCase, matched_bugs: list[HistoricalBug]) -> str:
    issue_family, _, _ = classify_issue_taxonomy(case_data, matched_bugs)
    return issue_family


def classify_issue_taxonomy(
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
) -> tuple[str, str, list[str]]:
    _ = matched_bugs  # classification remains case-first.
    text = _normalize_text(_taxonomy_text(case_data))
    evidence: list[str] = []

    if _has_any(
        text,
        [
            "memory margin",
            "rmt",
            "vref",
            "write_1d_jtag",
            "margin fail",
            "memory training",
            "dimm population",
            "one dimm per channel",
            "1dpc",
            "2dpc",
        ],
    ):
        family = "memory"
        if _has_any(text, ["one dimm per channel", "1dpc", "population", "full population", "2dpc"]):
            evidence.append("Observed pass/fail split by DIMM population pattern.")
            return family, "memory / DIMM population sensitive", evidence
        if _has_any(
            text,
            [
                "bios setup",
                "bios setting",
                "amd cbs",
                "ddr options",
                "memory context restore",
                "data scramble",
                "training setting",
            ],
        ):
            evidence.append("Memory result changes with BIOS or DDR training setting.")
            return family, "memory / BIOS-setting dependent", evidence
        evidence.append("Memory margin or Vref signal is below spec threshold.")
        return family, "memory / margin fail", evidence

    if _has_any(
        text,
        [
            "front panel",
            "reset button",
            "rst bt",
            "rst_bt",
            "rst bt n_fp",
            "button signal",
            "no response after pressing",
        ],
    ):
        return (
            "power-reset",
            "power-reset / front panel button signal issue",
            ["Front-panel reset button signal issue is explicitly described."],
        )

    if _has_any(text, ["pcie", "aer", "acs violation", "link width", "root port", "slot", "riser", "backplane"]):
        family = "PCIe"
        if _is_link_width_downgrade_signal(text):
            evidence.append("Observed PCIe link width downgraded from expected width.")
            return family, "PCIe / link width downgrade", evidence
        if _has_any(
            text,
            [
                "same position",
                "same slot",
                "same location",
                "location-related",
                "slot swap",
                "riser swap",
                "fixed to the same path",
            ],
        ):
            evidence.append("Failure appears tied to one slot/path/location.")
            return family, "PCIe / slot-path-location specific defect", evidence
        if _has_any(text, ["uncorrectable", "acs violation", "fatal", "non-fatal", "bit14"]):
            evidence.append("Uncorrectable AER or ACS violation appears in logs.")
            return family, "PCIe / uncorrectable AER or ACS violation", evidence
        evidence.append("Corrected/correctable AER signature is the dominant fail signal.")
        return family, "PCIe / corrected AER", evidence

    if _has_any(text, ["nvme", "ssd", "e1.s", "e3.s", "u.2", "m.2"]):
        return "storage", "storage / endpoint instability", ["Storage endpoint instability signals are present."]

    if _has_any(text, ["bios", "bmc", "firmware", "vpd"]):
        return "firmware", "firmware / configuration mismatch", ["Firmware/configuration mismatch signals are present."]

    return "other", "other / unclassified", ["No strong subtype signature detected from current evidence."]


def classify_decision_stage(
    case_data: NormalizedCase,
    issue_family: str,
    issue_subtype: str,
) -> tuple[str, str, str, list[str], list[str]]:
    raw_text = _case_text(case_data)
    text = _normalize_text(raw_text)
    lifecycle_status = _choose_lifecycle_status(
        explicit_status=case_data.status_current or case_data.status,
        status_history=case_data.status_history or [],
        raw_text=raw_text,
    )

    has_root_cause = case_data.has_root_cause_signal or _has_root_cause_signal(text)
    has_fix_artifact = case_data.has_solution_signal or _has_fix_artifact_signal(text)
    has_pass = case_data.has_pass_signal or _has_pass_signal(text)
    has_verification_request = case_data.has_verification_signal or _has_verification_request_signal(text)
    has_compare_signal = _has_any(
        text,
        [
            "swap",
            "compare",
            "a/b",
            "same location",
            "same path",
            "1dpc",
            "2dpc",
            "retest",
            "cross check",
        ],
    )

    decisive_evidence: list[str] = []
    if lifecycle_status:
        decisive_evidence.append(f"Normalized lifecycle status = {lifecycle_status}.")
    if case_data.status_history:
        decisive_evidence.append("Status history is available in normalized lifecycle evidence.")
    if case_data.has_root_cause_signal:
        decisive_evidence.append("Normalized lifecycle signal includes root-cause evidence.")
    if case_data.has_solution_signal:
        decisive_evidence.append("Normalized lifecycle signal includes solution or fix evidence.")
    if case_data.has_pass_signal:
        decisive_evidence.append("Normalized lifecycle signal includes PASS or retest-pass evidence.")

    if lifecycle_status in {"closed", "resolved"} and (has_pass or has_root_cause or has_fix_artifact):
        stage = "closure"
        action_mode = "close"
        resolution_state = "closed"
        decisive_evidence.append("Lifecycle status shows the case is already closed/resolved.")
    elif lifecycle_status == "fixed":
        if has_pass:
            stage = "closure"
            action_mode = "close"
            resolution_state = "fixed_verified"
            decisive_evidence.append("Fixed status is backed by explicit PASS or retest evidence.")
        elif has_root_cause or has_fix_artifact:
            stage = "verification"
            action_mode = "verify"
            resolution_state = "fixed_pending_verification"
            decisive_evidence.append("Fixed status is present, but closure still depends on verification evidence.")
        else:
            stage = "verification"
            action_mode = "verify"
            resolution_state = "fixed_pending_verification"
            decisive_evidence.append("Fixed status exists, but the supporting verification package is still thin.")
    elif lifecycle_status in {"verifying", "ready for dqa test"} or has_verification_request:
        stage = "verification"
        action_mode = "verify"
        resolution_state = "ready_for_verification"
        decisive_evidence.append("Lifecycle signal indicates verification or retest stage.")
    elif lifecycle_status in {"support & hw rework", "fixing"}:
        if has_root_cause or has_fix_artifact:
            stage = "root-cause identified"
            action_mode = "verify"
            resolution_state = "fix_in_progress"
            decisive_evidence.append("Lifecycle status and text both point to a defined fix path.")
        else:
            stage = "investigation"
            action_mode = "investigate"
            resolution_state = "investigating"
            decisive_evidence.append("Case is in active fix handling, but root-cause evidence is still incomplete.")
    elif lifecycle_status in {"clarifying", "in progress"}:
        stage = "investigation"
        action_mode = "investigate"
        resolution_state = "investigating"
        decisive_evidence.append("Lifecycle status indicates active investigation.")
    elif lifecycle_status in {"new", "open"}:
        if has_root_cause or has_fix_artifact:
            stage = "root-cause identified"
            action_mode = "verify"
            resolution_state = "fix_defined"
            decisive_evidence.append("Even though status is early, the text already contains root-cause or fix evidence.")
        elif has_compare_signal:
            stage = "triage"
            action_mode = "triage"
            resolution_state = "open"
            decisive_evidence.append("Case is still open/new; existing compare clues are treated as supporting triage context.")
        else:
            stage = "triage"
            action_mode = "triage"
            resolution_state = "open"
            decisive_evidence.append("Lifecycle status is still new/open without a confirmed fix path.")
    elif has_pass and (has_root_cause or has_fix_artifact):
        stage = "verification"
        action_mode = "verify"
        resolution_state = "verification_in_progress"
        decisive_evidence.append("Pass evidence exists together with a likely fix or root-cause statement.")
    elif has_root_cause or has_fix_artifact:
        stage = "root-cause identified"
        action_mode = "verify"
        resolution_state = "root_cause_identified"
        decisive_evidence.append("Root-cause or fix direction is explicitly described in the case text.")
    elif has_compare_signal:
        stage = "investigation"
        action_mode = "investigate"
        resolution_state = "investigating"
        decisive_evidence.append("The case already includes branch-separating compare signals.")
    else:
        stage = "triage"
        action_mode = "triage"
        resolution_state = "open"
        decisive_evidence.append("No strong lifecycle evidence beyond initial issue intake.")

    if has_root_cause:
        decisive_evidence.append("Text includes an explicit root-cause statement or equivalent wording.")
    if has_fix_artifact:
        decisive_evidence.append("Text includes a fix artifact such as rework, board change, or BIOS/config update.")
    if has_pass:
        decisive_evidence.append("Text includes PASS or retest-pass evidence.")

    unresolved_gap = _stage_specific_gaps(
        case_data=case_data,
        issue_family=issue_family,
        issue_subtype=issue_subtype,
        decision_stage=stage,
        has_root_cause=has_root_cause,
        has_fix_artifact=has_fix_artifact,
        has_pass=has_pass,
    )

    return stage, action_mode, resolution_state, _dedupe(decisive_evidence), _dedupe(unresolved_gap)


def apply_severity_rules(
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
    severity_rules: SeverityRules,
    *,
    issue_family: str = "",
    issue_subtype: str = "",
    decision_stage: str = "",
) -> tuple[str, list[str]]:
    case_text = _normalize_text(_case_text(case_data))
    historical_text = _normalize_text(" ".join(bug.combined_text() for bug in matched_bugs))
    matched_rule_texts: list[str] = []
    matched_levels: list[str] = []

    fail_ratio = _parse_fail_ratio(case_data.fail_rate or case_text)
    has_fatal_signal = _has_any(
        case_text,
        ["fatal hardware error", "machine check exception", "fatal error", "uncorrectable", "critical interrupt", "mce"],
    )
    has_device_missing = _mentions_device_missing(case_text)
    has_correctable_signal = _has_any(case_text, ["corrected error", "correctable", "aer"])
    has_workaround = _has_any(case_text, ["workaround", "customer accepts", "accept", "containment"])

    if fail_ratio is not None:
        if fail_ratio > 0.5:
            matched_levels.append("Critical")
            matched_rule_texts.append(f"Observed fail rate {_format_ratio(case_data.fail_rate or case_text)} (>50%).")
        elif fail_ratio >= 0.03:
            matched_levels.append("Major")
            matched_rule_texts.append(f"Observed fail rate {_format_ratio(case_data.fail_rate or case_text)} (3%~50%).")
        elif fail_ratio > 0:
            matched_levels.append("Minor")
            matched_rule_texts.append(f"Observed fail rate {_format_ratio(case_data.fail_rate or case_text)} (<=3%).")

    if has_fatal_signal:
        matched_levels.append("Critical")
        matched_rule_texts.append("Fatal or uncorrectable hardware signal appears in current evidence.")

    if has_device_missing:
        if has_workaround and fail_ratio is None and not has_fatal_signal:
            matched_levels.append("Major")
            matched_rule_texts.append("Device missing signal exists, but workaround path is also documented.")
        else:
            matched_levels.append("Critical")
            matched_rule_texts.append("Required device or slot is reported as not detected.")

    if has_correctable_signal and not has_fatal_signal:
        matched_levels.append("Minor")
        matched_rule_texts.append("Corrected or correctable AER signal appears without fatal symptom.")

    for level, rule_texts in severity_rules.severity_levels.items():
        for rule_text in rule_texts:
            if _rule_matches(case_text, rule_text):
                matched_levels.append(level)
                matched_rule_texts.append(rule_text)

    if not matched_levels and historical_text:
        for level, rule_texts in severity_rules.severity_levels.items():
            for rule_text in rule_texts:
                if _rule_matches(historical_text, rule_text):
                    matched_levels.append(_cap_historical_level(level))
                    matched_rule_texts.append(f"Historical support only: {rule_text}")

    if not matched_levels:
        matched_levels.append("Unknown")

    risk_level = max(matched_levels, key=_severity_rank)
    risk_level = _adjust_risk_by_subtype_and_stage(
        risk_level=risk_level,
        issue_family=issue_family,
        issue_subtype=issue_subtype,
        decision_stage=decision_stage,
        case_text=case_text,
    )
    return risk_level, _dedupe(matched_rule_texts)


def build_root_cause_hypothesis(
    issue_type: str,
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
    issue_subtype: str = "",
) -> str:
    text = _normalize_text(" ".join([_case_text(case_data)] + [bug.combined_text() for bug in matched_bugs]))
    component_hint = _component_hint(case_data)

    if issue_subtype == "PCIe / corrected AER":
        return "Likely corrected AER noise or signal-integrity issue on a specific PCIe path or riser."
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        if component_hint:
            return (
                f"Likely PCIe routing or compatibility instability on the {component_hint} path under the original trigger "
                "condition, not yet narrowed to endpoint versus root-port side."
            )
        return "Likely PCIe routing or compatibility instability under the original trigger condition."
    if issue_subtype == "PCIe / link width downgrade":
        if component_hint:
            return f"Likely lane-training or signal-integrity weakness on a specific {component_hint} path, causing x4 to degrade to x2."
        return "Likely PCIe lane-training integrity issue causing endpoint link width downgrade."
    if issue_subtype == "PCIe / slot-path-location specific defect":
        return "Likely a fixed slot, riser, or backplane path defect rather than an endpoint-only defect."
    if issue_subtype == "power-reset / front panel button signal issue":
        return "Likely a front-panel reset signal level or board-path defect instead of a software-only sequence issue."
    if issue_subtype == "memory / margin fail":
        return "Likely memory margin weakness where the tested Vref or training result is too close to the spec boundary."
    if issue_subtype == "memory / DIMM population sensitive":
        return "Likely memory behavior that changes with DIMM population topology rather than a random one-off failure."
    if issue_subtype == "memory / BIOS-setting dependent":
        return "Likely memory stability that depends on BIOS or DDR training settings rather than a single fixed hardware fault."

    if issue_type == "PCIe":
        if _has_any(text, ["nvme", "ssd", "e3.s"]):
            return "Possible PCIe endpoint path instability on the NVMe or SSD route under the reported trigger."
        return "Possible PCIe link training or enumeration instability under the reported trigger."
    if issue_type == "memory":
        return "Likely memory margin or training related instability."
    if issue_type == "power-reset":
        return "Possible power or reset path timing issue."
    return "Most likely still an incomplete issue pattern; more branch-separating evidence is needed."


def build_recommended_action(issue_type: str, risk_level: str) -> str:
    return build_recommended_action_with_case(issue_type, risk_level, None)


def build_recommended_action_with_case(
    issue_type: str,
    risk_level: str,
    case_data: NormalizedCase | None,
    *,
    issue_subtype: str = "",
    decision_stage: str = "",
    action_mode: str = "",
    resolution_state: str = "",
) -> str:
    _ = issue_type
    _ = resolution_state
    mode = action_mode or _default_action_mode(decision_stage or "triage")
    component_hint = _component_hint(case_data) if case_data else ""

    if mode == "close":
        if issue_subtype == "PCIe / link width downgrade":
            return "Close only after the final package includes x4 PASS logs for the original node and slot, plus before/after evidence for any tray, riser, or board change."
        if issue_subtype == "power-reset / front panel button signal issue":
            return "Close only after the reworked board passes the original reset-button test and the closure note records the reset-signal root cause and board change."
        if issue_subtype.startswith("memory /"):
            return "Close only after the final package includes the chosen BIOS or DIMM matrix, repeated PASS evidence under the original fail condition, and a clear closure note."
        return "Close only after the final package includes fix scope, PASS evidence, and status traceability."

    if mode == "verify":
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return (
                "First rerun the original AC restore or runtime trigger, confirm the uncorrectable AER or ACS signal is gone in full-cycle logs, "
                "and keep closure pending until DQA retest pass is attached."
            )
        if issue_subtype == "PCIe / corrected AER":
            return "First rerun the same stress phase and confirm corrected-AER counts stay within expectation on the original port or path before closure."
        if issue_subtype == "PCIe / slot-path-location specific defect":
            return "First verify the fix with the original slot or riser matrix and confirm the symptom no longer stays with the same path before closing the case."
        if issue_subtype == "PCIe / link width downgrade":
            return "First verify that the affected node or slot keeps x4 after reboot or power cycle, and attach before/after scan-compare logs for the same path."
        if issue_subtype == "power-reset / front panel button signal issue":
            return "First rerun the original front-panel reset test on the reworked sample, confirm stable reboot PASS, and keep the case open until signal evidence and PASS logs are attached."
        if issue_subtype.startswith("memory /"):
            return "First rerun the original memory margin case on the final BIOS and DIMM topology, and attach PASS evidence that proves the failing matrix is now stable."
        return "First run verification under the original fail condition and attach explicit PASS evidence before closure."

    if mode == "investigate":
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "First rerun under the original AC restore or runtime trigger, capture the raw AER log, and separate endpoint, slot-path, and root-port factors before widening the investigation."
        if issue_subtype == "PCIe / corrected AER":
            return "First capture corrected-AER logs with port and device mapping under the failing stress phase, then compare the same endpoint on a known-good path."
        if issue_subtype == "PCIe / slot-path-location specific defect":
            return "First do a slot or riser A/B swap to confirm whether the symptom stays with one physical path before moving to broader reproduction."
        if issue_subtype == "power-reset / front panel button signal issue":
            return "First measure the reset-button signal on the failing board path and confirm whether the symptom only appears with the current front-panel board configuration."
        if issue_subtype == "memory / DIMM population sensitive":
            return "First compare the failing DIMM population against 1-DIMM-per-channel on the same BIOS settings and record which topology flips PASS or FAIL."
        if issue_subtype == "memory / BIOS-setting dependent":
            return "First rerun the same memory population with the current BIOS training settings and one known-good setting to confirm whether the failure is setting-dependent."
        if issue_subtype == "memory / margin fail":
            return "First rerun the failing margin or Vref item under the same setup and record the exact delta against the spec boundary."
        return "First isolate the highest-value branch with one compare experiment before widening the investigation scope."

    if issue_subtype == "PCIe / link width downgrade":
        target = component_hint or "affected node or slot"
        return f"First swap the {target} against a known-good location and confirm whether x2 stays with the same path; keep the original link-status and scan-compare logs."
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return "First rerun the original trigger and capture the raw AER or ACS signature before deciding whether to branch into endpoint, slot-path, or root-port investigation."
    if issue_subtype == "power-reset / front panel button signal issue":
        return "First confirm the reset-button symptom on the original setup and measure the reset signal level before deciding whether to move into hardware rework."
    if issue_subtype == "memory / DIMM population sensitive":
        return "First compare the original failing DIMM population against 1-DIMM-per-channel on the same BIOS settings and keep the margin result side by side."
    if issue_subtype == "memory / BIOS-setting dependent":
        return "First confirm whether the failure disappears only after a BIOS or training-setting change, and preserve both the failing and passing setting sets."
    if issue_subtype == "memory / margin fail":
        return "First rerun the failing margin item and capture the raw Vref or margin value that crosses the spec threshold."

    if risk_level == "Critical":
        return "Pause shipment review, capture one decisive fail signature, and use that evidence to choose the next investigation branch."
    return "Collect the missing trigger, fail signature, and scope evidence before moving beyond triage."


def estimate_confidence(
    *,
    case_data: NormalizedCase,
    issue_subtype: str,
    decision_stage: str,
    decisive_evidence: list[str],
    unresolved_gap: list[str],
) -> str:
    score = 0
    if issue_subtype and "unclassified" not in issue_subtype:
        score += 1
    if decision_stage != "triage":
        score += 1
    if _parse_fail_ratio(case_data.fail_rate or _case_text(case_data)) is not None:
        score += 1
    if len(decisive_evidence) >= 2:
        score += 1
    if len(unresolved_gap) <= 1:
        score += 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _default_action_mode(stage: str) -> str:
    if stage == "closure":
        return "close"
    if stage in {"verification", "root-cause identified"}:
        return "verify"
    if stage == "investigation":
        return "investigate"
    return "triage"


def _adjust_risk_by_subtype_and_stage(
    *,
    risk_level: str,
    issue_family: str,
    issue_subtype: str,
    decision_stage: str,
    case_text: str,
) -> str:
    adjusted = risk_level

    if issue_subtype == "PCIe / corrected AER" and not _mentions_device_missing(case_text):
        adjusted = _cap_level(adjusted, "Major")
    if issue_subtype == "PCIe / link width downgrade":
        adjusted = _cap_level(adjusted, "Major")
    if issue_subtype == "power-reset / front panel button signal issue":
        adjusted = _cap_level(adjusted, "Major")
    if issue_family == "memory":
        adjusted = _cap_level(adjusted, "Major")

    if decision_stage == "verification":
        adjusted = _cap_level(adjusted, "Major")
    if decision_stage == "closure":
        if _has_pass_signal(case_text):
            adjusted = _cap_level(adjusted, "Minor")
        else:
            adjusted = _cap_level(adjusted, "Major")
    return adjusted


def _stage_specific_gaps(
    *,
    case_data: NormalizedCase,
    issue_family: str,
    issue_subtype: str,
    decision_stage: str,
    has_root_cause: bool,
    has_fix_artifact: bool,
    has_pass: bool,
) -> list[str]:
    gaps: list[str] = []
    text = _normalize_text(_case_text(case_data))

    if decision_stage == "triage":
        if not (case_data.log_snippet or _has_any(text, ["aer", "width x2", "vref", "button signal", "no response"])):
            gaps.append("raw fail signature under the original trigger")
        if not (case_data.test_case or case_data.test_procedure or case_data.expected_config):
            gaps.append("original test condition or expected behavior")
        if not _contains_fail_rate(case_data.fail_rate or _case_text(case_data)):
            gaps.append("reproduction scope or fail rate")
    elif decision_stage == "investigation":
        gaps.append(_investigation_gap_for_subtype(issue_subtype))
        if not (case_data.current_config or case_data.component):
            gaps.append("failing configuration or affected component mapping")
    elif decision_stage == "root-cause identified":
        if not has_fix_artifact:
            gaps.append("fix candidate or corrective-action record")
        if not has_root_cause:
            gaps.append("explicit root-cause statement")
        gaps.append(_verification_gap_for_subtype(issue_subtype))
    elif decision_stage == "verification":
        if not has_pass:
            gaps.append("PASS or retest result under the original fail condition")
        gaps.append(_verification_gap_for_subtype(issue_subtype))
    elif decision_stage == "closure":
        if not has_pass:
            gaps.append("closure-grade PASS evidence under the original fail condition")
        if not (has_root_cause or has_fix_artifact):
            gaps.append("final closure note describing the fix scope")

    return _dedupe(gaps)


def _investigation_gap_for_subtype(issue_subtype: str) -> str:
    if issue_subtype == "PCIe / link width downgrade":
        return "slot/node/tray A-B compare result showing whether x2 follows the path or the endpoint"
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return "raw AER log under the original trigger with endpoint, slot-path, and root-port mapping"
    if issue_subtype == "PCIe / slot-path-location specific defect":
        return "swap result confirming the symptom stays with one slot, riser, or backplane path"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "reset-signal measurement or board-path evidence on the failing front-panel path"
    if issue_subtype.startswith("memory /"):
        return "BIOS-setting and DIMM-population compare matrix that separates the failing branch"
    return "branch-separating compare evidence"


def _verification_gap_for_subtype(issue_subtype: str) -> str:
    if issue_subtype.startswith("PCIe /"):
        return "before/after verification logs on the original node, slot, or path"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "reworked-sample PASS record on the original reset-button case"
    if issue_subtype.startswith("memory /"):
        return "final BIOS or DIMM matrix plus PASS result on the original fail case"
    return "verification package for the original fail case"


def _cap_level(level: str, cap: str) -> str:
    if _severity_rank(level) > _severity_rank(cap):
        return cap
    return level


def _rule_matches(search_text: str, rule_text: str) -> bool:
    normalized_rule = _normalize_text(rule_text)
    if normalized_rule and normalized_rule in search_text:
        return True

    rule_tokens = [token for token in re.findall(r"[a-z0-9]+", normalized_rule) if len(token) >= 3]
    if not rule_tokens:
        return False

    matched_count = sum(1 for token in rule_tokens if token in search_text)
    if len(rule_tokens) <= 3:
        required_count = len(rule_tokens)
    else:
        required_count = max(2, (len(rule_tokens) + 1) // 2)
    return matched_count >= required_count


def _severity_rank(level: str) -> int:
    try:
        return len(SEVERITY_ORDER) - SEVERITY_ORDER.index(level)
    except ValueError:
        return 0


def _normalize_text(value: str) -> str:
    text = value.lower()
    replacements = {
        "detected": "detect",
        "detection": "detect",
        "detectable": "detect",
        "pciee": "pcie",
        "sr-iov": "sriov",
        "–": "-",
        "—": "-",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _case_text(case_data: NormalizedCase) -> str:
    return "\n".join(
        part
        for part in [
            case_data.subject,
            case_data.status,
            case_data.issue_description,
            case_data.log_snippet,
            case_data.comments,
            case_data.current_config,
            case_data.expected_config,
            case_data.known_context,
            case_data.test_case,
            case_data.test_procedure,
            case_data.workaround,
        ]
        if part
    )


def _taxonomy_text(case_data: NormalizedCase) -> str:
    return "\n".join(
        part
        for part in [
            case_data.subject,
            case_data.component,
            case_data.issue_description,
            case_data.log_snippet,
            case_data.comments,
            case_data.known_context,
            case_data.test_case,
        ]
        if part
    )


def _mentions_device_missing(search_text: str) -> bool:
    missing_patterns = [
        "cannot be detect",
        "could not be detect",
        "not detect",
        "device disappear",
        "cannot detect",
        "missing device",
    ]
    if any(pattern in search_text for pattern in missing_patterns):
        return True
    return "detect" in search_text and any(token in search_text for token in ["cannot", "not", "missing", "fail"])


def _parse_fail_ratio(text: str) -> float | None:
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if not match:
        return None
    numerator = int(match.group(1))
    denominator = int(match.group(2))
    if denominator == 0:
        return None
    return numerator / denominator


def _format_ratio(text: str) -> str:
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return text


def _cap_historical_level(level: str) -> str:
    if level == "Critical":
        return "Major"
    return level


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def _is_link_width_downgrade_signal(text: str) -> bool:
    patterns = [
        r"link width",
        r"downgrad",
        r"instead of x4",
        r"detect with x2",
        r"width x2",
        r"lnksta.*x2",
        r"x4.*x2",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _infer_lifecycle_status(raw_text: str, explicit_status: str) -> str:
    lowered_status = _normalize_text(explicit_status or "").strip()
    known = [
        "closed",
        "resolved",
        "fixed",
        "verifying",
        "ready for dqa test",
        "support & hw rework",
        "fixing",
        "clarifying",
        "in progress",
        "open",
        "new",
    ]
    for key in known:
        if lowered_status == key or lowered_status.startswith(key):
            return key

    lowered = _normalize_text(raw_text)
    changed = re.findall(r"status changed from .*? to ([a-z0-9 &/_-]+)", lowered)
    if changed:
        candidate = changed[-1].strip()
        for key in known:
            if key in candidate:
                return key

    for line in lowered.splitlines():
        compact = line.strip()
        if not compact.startswith("status"):
            continue
        for key in known:
            if key in compact:
                return key
    return ""


def _choose_lifecycle_status(*, explicit_status: str, status_history: list[str], raw_text: str) -> str:
    explicit = _infer_lifecycle_status(raw_text, explicit_status)
    if not status_history:
        return explicit
    latest_history = _normalize_status_label(status_history[-1])
    if not explicit:
        return latest_history
    if _status_rank(latest_history) > _status_rank(explicit):
        return latest_history
    return explicit


def _normalize_status_label(value: str) -> str:
    normalized = _normalize_text(value or "").strip()
    aliases = {
        "new": "new",
        "open": "open",
        "clarifying": "clarifying",
        "fixing": "fixing",
        "support & hw rework": "support & hw rework",
        "ready for dqa test": "ready for dqa test",
        "verifying": "verifying",
        "fixed": "fixed",
        "resolved": "resolved",
        "closed": "closed",
    }
    return aliases.get(normalized, normalized)


def _status_rank(status: str) -> int:
    order = {
        "new": 1,
        "open": 1,
        "clarifying": 2,
        "fixing": 3,
        "support & hw rework": 3,
        "ready for dqa test": 4,
        "verifying": 4,
        "fixed": 5,
        "resolved": 6,
        "closed": 6,
    }
    return order.get(status, 0)


def _contains_fail_rate(text: str) -> bool:
    return bool(text and re.search(r"\d+\s*/\s*\d+", text))


def _has_root_cause_signal(text: str) -> bool:
    patterns = [
        "root cause",
        "solution(root cause)",
        "cause by",
        "this issue cause by",
        "r&d solution for fix",
        "due to",
        "root-cause",
    ]
    return _has_any(text, patterns)


def _has_fix_artifact_signal(text: str) -> bool:
    patterns = [
        "to fix this issue",
        "fixed by",
        "replacement board",
        "reworked sample",
        "rework",
        "board change",
        "change r",
        "0 ohm",
        "bios config update",
        "bios setting",
        "config update",
        "workaround",
    ]
    return _has_any(text, patterns)


def _has_pass_signal(text: str) -> bool:
    return bool(
        re.search(
            r"\b(pass|passed|verified|stable pass|retest pass|verification pass)\b",
            text,
        )
    )


def _has_verification_request_signal(text: str) -> bool:
    return _has_any(
        text,
        [
            "ready for dqa test",
            "verifying",
            "verify",
            "verification",
            "retest",
        ],
    )


def _component_hint(case_data: NormalizedCase | None) -> str:
    if case_data is None:
        return ""
    text = _normalize_text(
        "\n".join(
            part
            for part in [
                case_data.component,
                case_data.subject,
                case_data.issue_description,
                case_data.comments,
                case_data.current_config,
                case_data.known_context,
            ]
            if part
        )
    )
    if _has_any(text, ["e3.s", "e1.s", "nvme", "ssd", "kioxia", "solidigm"]):
        return "NVMe SSD"
    if _has_any(text, ["riser", "backplane"]):
        return "riser/backplane"
    if "slot" in text:
        return "slot/path"
    if _has_any(text, ["front panel", "reset button", "rst bt"]):
        return "front-panel reset"
    if "dimm" in text:
        return "DIMM population"
    return ""
