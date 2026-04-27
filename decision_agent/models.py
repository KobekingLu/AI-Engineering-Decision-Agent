"""Small data models for the standalone decision-agent flow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class NormalizedCase:
    """Normalized case input used by the first decision-agent prototype."""

    case_id: str = ""
    project: str = ""
    source_type: str = ""
    source_format: str = ""
    source_file: str = ""
    extraction_status: str = ""
    bug_id: str = ""
    reporter_role: str = ""
    subject: str = ""
    status: str = ""
    status_current: str = ""
    status_history: list[str] | None = None
    status_history_events: list[dict[str, Any]] | None = None
    decision_stage_candidate: str = ""
    resolution_state_candidate: str = ""
    has_root_cause_signal: bool = False
    has_solution_signal: bool = False
    has_verification_signal: bool = False
    has_pass_signal: bool = False
    lifecycle_signal_items: list[dict[str, Any]] | None = None
    priority: str = ""
    severity: str = ""
    component: str = ""
    hw_version: str = ""
    fw_version: str = ""
    assignee: str = ""
    customer: str = ""
    issue_description: str = ""
    log_snippet: str = ""
    comments: str = ""
    current_config: str = ""
    expected_config: str = ""
    known_context: str = ""
    reproduction: str = ""
    fail_rate: str = ""
    test_case: str = ""
    test_procedure: str = ""
    workaround: str = ""
    attachments: list[str] | None = None
    evidence: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "NormalizedCase":
        return cls(
            case_id=str(data.get("case_id", "") or ""),
            project=str(data.get("project", "") or ""),
            source_type=str(data.get("source_type", "") or ""),
            source_format=str(data.get("source_format", "") or ""),
            source_file=str(data.get("source_file", "") or ""),
            extraction_status=str(data.get("extraction_status", "") or ""),
            bug_id=str(data.get("bug_id", "") or ""),
            reporter_role=str(data.get("reporter_role", "") or ""),
            subject=str(data.get("subject", "") or ""),
            status=str(data.get("status", "") or ""),
            status_current=str(data.get("status_current", "") or ""),
            status_history=_coerce_str_list(data.get("status_history")),
            status_history_events=_coerce_dict_list(data.get("status_history_events")),
            decision_stage_candidate=str(data.get("decision_stage_candidate", "") or ""),
            resolution_state_candidate=str(data.get("resolution_state_candidate", "") or ""),
            has_root_cause_signal=_coerce_bool(data.get("has_root_cause_signal")),
            has_solution_signal=_coerce_bool(data.get("has_solution_signal")),
            has_verification_signal=_coerce_bool(data.get("has_verification_signal")),
            has_pass_signal=_coerce_bool(data.get("has_pass_signal")),
            lifecycle_signal_items=_coerce_dict_list(data.get("lifecycle_signal_items")),
            priority=str(data.get("priority", "") or ""),
            severity=str(data.get("severity", "") or ""),
            component=str(data.get("component", "") or ""),
            hw_version=str(data.get("hw_version", "") or ""),
            fw_version=str(data.get("fw_version", "") or ""),
            assignee=str(data.get("assignee", "") or ""),
            customer=str(data.get("customer", "") or ""),
            issue_description=str(data.get("issue_description", "") or ""),
            log_snippet=str(data.get("log_snippet", "") or ""),
            comments=str(data.get("comments", "") or ""),
            current_config=str(data.get("current_config", "") or ""),
            expected_config=str(data.get("expected_config", "") or ""),
            known_context=str(data.get("known_context", "") or ""),
            reproduction=str(data.get("reproduction", "") or ""),
            fail_rate=str(data.get("fail_rate", "") or ""),
            test_case=str(data.get("test_case", "") or ""),
            test_procedure=str(data.get("test_procedure", "") or ""),
            workaround=str(data.get("workaround", "") or ""),
            attachments=_coerce_str_list(data.get("attachments")),
            evidence=_coerce_str_list(data.get("evidence")),
        )

    def combined_text(self) -> str:
        return " ".join(
            part
            for part in [
                self.case_id,
                self.project,
                self.source_type,
                self.source_format,
                self.source_file,
                self.extraction_status,
                self.bug_id,
                self.reporter_role,
                self.subject,
                self.status,
                self.status_current,
                " ".join(self.status_history or []),
                " ".join(str(item) for item in (self.status_history_events or [])),
                self.decision_stage_candidate,
                self.resolution_state_candidate,
                " ".join(str(item) for item in (self.lifecycle_signal_items or [])),
                self.priority,
                self.severity,
                self.component,
                self.hw_version,
                self.fw_version,
                self.assignee,
                self.customer,
                self.issue_description,
                self.log_snippet,
                self.comments,
                self.current_config,
                self.expected_config,
                self.known_context,
                self.reproduction,
                self.fail_rate,
                self.test_case,
                self.test_procedure,
                self.workaround,
                " ".join(self.attachments or []),
                " ".join(self.evidence or []),
            ]
            if part
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HistoricalBug:
    """One searchable row from the historical bug summary CSV."""

    bug_id: str
    project: str
    component: str
    status: str
    subject: str
    description: str
    quarter: str
    source_sheet: str
    score: float = 0.0
    matched_terms: list[str] | None = None
    matched_fields: dict[str, list[str]] | None = None
    match_reasons: list[str] | None = None

    def combined_text(self) -> str:
        return " ".join(
            part
            for part in [
                self.bug_id,
                self.project,
                self.component,
                self.status,
                self.subject,
                self.description,
                self.quarter,
                self.source_sheet,
            ]
            if part
        )


@dataclass
class SeverityRules:
    """Parsed severity rules from the starter YAML file."""

    severity_levels: dict[str, list[str]]
    general_rule: str = ""


@dataclass
class DecisionSummary:
    """Structured JSON output for the decision-agent flow."""

    case_id: str
    source_file: str
    reporter_role: str
    evidence_quality: str
    issue_type: str
    matched_historical_cases: list[str]
    root_cause_hypothesis: str
    risk_level: str
    recommended_action: str
    decision_summary: str
    missing_information: list[str]
    reasoning_trace: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _coerce_str_list(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return None


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _coerce_dict_list(value: object) -> list[dict[str, Any]] | None:
    if value is None:
        return None
    if isinstance(value, list):
        result: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                result.append({str(key): item[key] for key in item})
        return result or None
    return None
