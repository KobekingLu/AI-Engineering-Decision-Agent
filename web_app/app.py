"""Streamlit MVP for single-case decision-agent analysis."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from web_app.decision_adapter import analyze_case_payload, analyze_uploaded_bundle
from web_app.html_report import write_single_case_report
from web_app.intake import build_case_from_freeform_text, slugify
from web_app.ocr_utils import is_ocr_available


OUTPUT_ROOT = REPO_ROOT / "output" / "web_app"
HTML_ROOT = OUTPUT_ROOT / "html"
INPUT_ROOT = OUTPUT_ROOT / "input"


def main() -> None:
    st.set_page_config(
        page_title="Decision Agent MVP",
        page_icon=":material/analytics:",
        layout="wide",
    )

    st.title("Decision Agent MVP")
    st.caption("Single-case intake -> existing decision_agent -> single-case HTML report")
    st.info(
        "This MVP reuses the current decision_agent output. "
        + (
            "Local OCR is enabled for scanned PDF and image files."
            if is_ocr_available()
            else "Local OCR is not enabled, so scanned PDF and image files still need readable text or a sidecar JSON/TXT."
        )
    )

    mode = st.radio(
        "Input mode",
        ("Paste text + optional files", "Upload files only"),
        horizontal=True,
    )

    if mode == "Paste text + optional files":
        render_text_mode()
    else:
        render_upload_mode()


def render_text_mode() -> None:
    with st.form("text_case_form"):
        st.subheader("Freeform Case Input")
        case_id = st.text_input("Optional Case ID")
        st.caption(
            "Paste anything you have in one box, and add helper files if needed. Plain notes are fine. "
            "If you use labels like `Project:`, `Bug ID:`, `Issue Description:`, `Log:`, "
            "`Expected Config:`, the intake will keep them."
        )
        raw_text = st.text_area(
            "Case Notes",
            height=320,
            placeholder="Paste bug title, issue description, logs, comments, mail thread notes, test config, workaround, anything useful...",
        )
        uploaded_files = st.file_uploader(
            "Optional helper files for the same case",
            type=["json", "txt", "pdf", "html", "htm", "png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            help="Useful when one case includes text plus screenshots, scanned logs, HTML exports, or helper files.",
        )

        submitted = st.form_submit_button("Analyze Case", type="primary")

    if not submitted:
        return

    has_text = bool(raw_text.strip())
    has_files = bool(uploaded_files)

    if not has_text and not has_files:
        st.warning("Please paste some case content or upload helper files first.")
        return

    if has_files:
        summary, payload, summary_path, errors = analyze_uploaded_bundle(
            [(uploaded_file.name, uploaded_file.getvalue()) for uploaded_file in uploaded_files],
            output_root=OUTPUT_ROOT,
            case_id=case_id,
            bundle_notes=raw_text,
        )
        if errors:
            for error_message in errors:
                st.warning(error_message)
        if summary is None or summary_path is None or payload is None:
            st.warning("The mixed text-and-file case could not be analyzed.")
            return

        payload_path = INPUT_ROOT / f"{payload['case_id']}.normalized.json"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        html_path = write_single_case_report(
            case_payload=payload,
            summary=summary,
            target_path=HTML_ROOT / f"{slugify(str(summary.get('case_id', 'case_bundle')))}.html",
        )
        render_result(summary, payload, summary_path, html_path)
        return

    payload = build_case_from_freeform_text(case_id, raw_text)
    payload_path = INPUT_ROOT / f"{payload['case_id']}.normalized.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    summary, summary_path = analyze_case_payload(payload, output_root=OUTPUT_ROOT)
    html_path = write_single_case_report(
        case_payload=payload,
        summary=summary,
        target_path=HTML_ROOT / f"{payload['case_id']}.html",
    )
    render_result(summary, payload, summary_path, html_path)


def render_upload_mode() -> None:
    st.subheader("Single-Case Multi-File Upload")
    case_id = st.text_input("Optional Case ID")
    bundle_notes = st.text_area(
        "Case Notes / Overall Context",
        height=160,
        placeholder="Paste any overall notes, mail summary, or manual context that should be merged into this one case.",
    )
    uploaded_files = st.file_uploader(
        "Upload one or more files for the same case",
        type=["json", "txt", "pdf", "html", "htm", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    if st.button("Analyze Uploaded Case", type="primary"):
        if not uploaded_files:
            st.warning("Please upload one or more files first.")
            return

        summary, payload, summary_path, errors = analyze_uploaded_bundle(
            [(uploaded_file.name, uploaded_file.getvalue()) for uploaded_file in uploaded_files],
            output_root=OUTPUT_ROOT,
            case_id=case_id,
            bundle_notes=bundle_notes,
        )
        if errors:
            for error_message in errors:
                st.warning(error_message)
        if summary is None or summary_path is None or payload is None:
            st.warning("The uploaded case bundle could not be analyzed.")
            return

        payload_path = INPUT_ROOT / f"{payload['case_id']}.normalized.json"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        html_path = write_single_case_report(
            case_payload=payload,
            summary=summary,
            target_path=HTML_ROOT / f"{slugify(str(summary.get('case_id', 'case_bundle')))}.html",
        )
        render_result(summary, payload, summary_path, html_path)

def render_result(
    summary: dict[str, object],
    payload: dict[str, object],
    summary_path: Path,
    html_path: Path,
) -> None:
    st.success("Analysis complete.")

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Issue Type", str(summary.get("issue_type", "N/A")))
    metric2.metric("Risk Level", str(summary.get("risk_level", "N/A")))
    metric3.metric("Decision Stage", str(summary.get("decision_stage", "N/A")))
    st.caption(
        "Issue Family/Subtype: "
        f"{summary.get('issue_family', 'N/A')} / {summary.get('issue_subtype', 'N/A')}"
    )
    st.caption(
        f"Action Mode: {summary.get('action_mode', 'N/A')} | "
        f"Resolution: {summary.get('resolution_state', 'N/A')} | "
        f"Confidence: {summary.get('confidence', 'N/A')}"
    )
    lifecycle_flags = [
        label
        for key, label in [
            ("has_root_cause_signal", "root-cause"),
            ("has_solution_signal", "solution/fix"),
            ("has_verification_signal", "verification"),
            ("has_pass_signal", "PASS"),
        ]
        if payload.get(key)
    ]
    if payload.get("status_current") or lifecycle_flags:
        st.caption(
            "Lifecycle Evidence: "
            f"status={payload.get('status_current', payload.get('status', 'N/A'))}"
            + (f" | signals={', '.join(lifecycle_flags)}" if lifecycle_flags else "")
        )
    if summary.get("lifecycle_evidence_summary"):
        st.caption(f"Lifecycle Basis: {summary.get('lifecycle_evidence_summary')}")
        if summary.get("lifecycle_evidence_summary_zh"):
            st.caption(str(summary.get("lifecycle_evidence_summary_zh")))
    if summary.get("status_history_events") or summary.get("lifecycle_signal_items"):
        st.caption(
            "Lifecycle Detail Counts: "
            f"status_events={len(summary.get('status_history_events', []) or [])} | "
            f"signal_items={len(summary.get('lifecycle_signal_items', []) or [])}"
        )

    st.subheader("Decision Summary")
    st.write(summary.get("decision_summary", "N/A"))
    if summary.get("decision_summary_zh"):
        st.caption(str(summary.get("decision_summary_zh")))

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("**Recommended Action**")
        st.write(summary.get("recommended_action", "N/A"))
        if summary.get("recommended_action_zh"):
            st.caption(str(summary.get("recommended_action_zh")))
        st.markdown("**Next Step Focus**")
        st.write(summary.get("next_step_focus", "N/A"))
        if summary.get("next_step_focus_zh"):
            st.caption(str(summary.get("next_step_focus_zh")))
        st.markdown("**Root Cause Hypothesis**")
        st.write(summary.get("root_cause_hypothesis", "N/A"))
        if summary.get("root_cause_hypothesis_zh"):
            st.caption(str(summary.get("root_cause_hypothesis_zh")))
        st.markdown("**Uncertainty Summary**")
        st.write(summary.get("uncertainty_summary", "N/A"))
        if summary.get("uncertainty_summary_zh"):
            st.caption(str(summary.get("uncertainty_summary_zh")))
        st.markdown("**Lifecycle Evidence Summary**")
        st.write(summary.get("lifecycle_evidence_summary", "N/A"))
        if summary.get("lifecycle_evidence_summary_zh"):
            st.caption(str(summary.get("lifecycle_evidence_summary_zh")))
        if summary.get("status_history_events"):
            st.markdown("**Status History Events**")
            st.write(summary.get("status_history_events", []))
        if summary.get("lifecycle_signal_items"):
            st.markdown("**Lifecycle Signal Items**")
            st.write(summary.get("lifecycle_signal_items", []))
        st.markdown("**Missing Information**")
        st.write(summary.get("missing_information", []))
        st.markdown("**Decisive Evidence**")
        st.write(summary.get("decisive_evidence", []))
        st.markdown("**Unresolved Gap**")
        st.write(summary.get("unresolved_gap", []))
        st.markdown("**Knowledge Governance Note**")
        st.write(summary.get("knowledge_governance_note", "N/A"))
        if summary.get("knowledge_governance_note_zh"):
            st.caption(str(summary.get("knowledge_governance_note_zh")))
        st.markdown("**Reasoning Trace**")
        reasoning_trace = summary.get("reasoning_trace", []) or []
        reasoning_trace_zh = summary.get("reasoning_trace_zh", []) or []
        for index, item in enumerate(reasoning_trace):
            st.markdown(f"- {item}")
            if index < len(reasoning_trace_zh) and reasoning_trace_zh[index]:
                st.caption(str(reasoning_trace_zh[index]))

    with right:
        st.markdown("**Matched Historical Cases**")
        matched_details = summary.get("matched_historical_case_details", [])
        if matched_details:
            for item in matched_details:
                st.markdown(
                    f"- `#{item.get('bug_id', '')}` {item.get('subject', 'N/A')}  \n"
                    f"  Project: {item.get('project', 'N/A')} | Status: {item.get('status', 'N/A')}"
                )
        else:
            matched = summary.get("matched_historical_cases", [])
            if matched:
                for item in matched:
                    st.code(str(item))
            else:
                st.write("No historical match.")
        st.markdown("**Output Files**")
        st.write(f"Summary JSON: `{summary_path}`")
        st.write(f"HTML report: `{html_path}`")

    with st.expander("Normalized Input Snapshot"):
        st.json(payload)
    with st.expander("Decision Summary JSON"):
        st.json(summary)

    st.download_button(
        "Download HTML Report",
        data=html_path.read_text(encoding="utf-8"),
        file_name=html_path.name,
        mime="text/html",
    )


if __name__ == "__main__":
    main()
