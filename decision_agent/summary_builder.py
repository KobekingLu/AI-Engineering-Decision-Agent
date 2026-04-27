"""Build structured JSON outputs for decision-agent analysis."""

from __future__ import annotations

from typing import Any

from decision_agent.models import DecisionSummary, HistoricalBug, NormalizedCase


def build_decision_summary(
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
    issue_type: str,
    risk_level: str,
    root_cause_hypothesis: str,
    recommended_action: str,
    applied_rules: list[str],
    template: dict[str, Any],
    *,
    issue_family: str | None = None,
    issue_subtype: str = "",
    decision_stage: str = "triage",
    action_mode: str = "triage",
    resolution_state: str = "open",
    decisive_evidence: list[str] | None = None,
    unresolved_gap: list[str] | None = None,
    confidence: str = "",
) -> dict[str, Any]:
    family = issue_family or issue_type or "other"
    subtype = issue_subtype or f"{family} / unclassified"
    missing_information = collect_missing_information(
        case_data,
        matched_bugs,
        stage=decision_stage,
        issue_subtype=subtype,
    )
    evidence_quality = assess_evidence_quality(case_data, missing_information)
    decisive = _dedupe(decisive_evidence or [])
    unresolved = _dedupe((unresolved_gap or []) + _stage_gap_from_missing(missing_information, decision_stage))
    final_confidence = confidence or estimate_confidence(
        evidence_quality=evidence_quality,
        stage=decision_stage,
        decisive_count=len(decisive),
        unresolved_count=len(unresolved),
    )

    summary = DecisionSummary(
        case_id=case_data.case_id or case_data.bug_id or "unknown_case",
        source_file=case_data.source_file,
        reporter_role=case_data.reporter_role,
        evidence_quality=evidence_quality,
        issue_type=family,
        matched_historical_cases=[bug.bug_id for bug in matched_bugs],
        root_cause_hypothesis=root_cause_hypothesis,
        risk_level=risk_level,
        recommended_action=recommended_action,
        decision_summary=build_decision_text(
            case_data=case_data,
            issue_family=family,
            issue_subtype=subtype,
            decision_stage=decision_stage,
            risk_level=risk_level,
            evidence_quality=evidence_quality,
            confidence=final_confidence,
        ),
        missing_information=missing_information,
        reasoning_trace=build_reasoning_trace(
            case_data=case_data,
            matched_bugs=matched_bugs,
            issue_family=family,
            issue_subtype=subtype,
            decision_stage=decision_stage,
            action_mode=action_mode,
            resolution_state=resolution_state,
            risk_level=risk_level,
            applied_rules=applied_rules,
            missing_information=missing_information,
            decisive_evidence=decisive,
            unresolved_gap=unresolved,
            confidence=final_confidence,
        ),
    )

    result = summary.to_dict()
    result["issue_family"] = family
    result["issue_subtype"] = subtype
    result["decision_stage"] = decision_stage
    result["action_mode"] = action_mode
    result["resolution_state"] = resolution_state
    result["lifecycle_status"] = case_data.status_current or case_data.status
    result["lifecycle_status_history"] = case_data.status_history or []
    result["lifecycle_signals"] = collect_lifecycle_signals(case_data)
    result["status_history_events"] = case_data.status_history_events or []
    result["lifecycle_signal_items"] = case_data.lifecycle_signal_items or []
    result["lifecycle_evidence_summary"] = build_lifecycle_evidence_summary(case_data)
    result["lifecycle_evidence_summary_zh"] = build_lifecycle_evidence_summary_zh(case_data)
    result["confidence"] = final_confidence
    result["decisive_evidence"] = decisive
    result["unresolved_gap"] = unresolved
    result["root_cause_hypothesis_zh"] = build_root_cause_hypothesis_zh(
        issue_subtype=subtype,
        case_data=case_data,
    )
    result["recommended_action_zh"] = build_recommended_action_zh(
        action_mode=action_mode,
        issue_subtype=subtype,
        resolution_state=resolution_state,
        case_data=case_data,
    )
    result["decision_summary_zh"] = build_decision_text_zh(
        case_data=case_data,
        issue_subtype=subtype,
        decision_stage=decision_stage,
        risk_level=risk_level,
        confidence=final_confidence,
    )
    result["uncertainty_summary"] = build_uncertainty_summary(
        decision_stage=decision_stage,
        confidence=final_confidence,
        missing_information=missing_information,
        unresolved_gap=unresolved,
    )
    result["uncertainty_summary_zh"] = build_uncertainty_summary_zh(
        decision_stage=decision_stage,
        confidence=final_confidence,
        missing_information=missing_information,
        unresolved_gap=unresolved,
    )
    result["next_step_focus"] = build_next_step_focus(
        action_mode=action_mode,
        issue_subtype=subtype,
        decision_stage=decision_stage,
        resolution_state=resolution_state,
        case_data=case_data,
    )
    result["next_step_focus_zh"] = build_next_step_focus_zh(
        action_mode=action_mode,
        issue_subtype=subtype,
        decision_stage=decision_stage,
        resolution_state=resolution_state,
        case_data=case_data,
    )
    result["knowledge_governance_note"] = (
        "Retrieved historical cases are reference patterns only. "
        "They should not be treated as definitive answers unless a human later confirms the root cause, solution, or verification result."
    )
    result["knowledge_governance_note_zh"] = (
        "歷史案例只作為參考模式，不代表最終答案。只有後續經人工確認的 root cause、solution 或 verification result，"
        "才應被視為高信任度知識。"
    )
    result["reasoning_trace_zh"] = build_reasoning_trace_zh(
        case_data=case_data,
        matched_bugs=matched_bugs,
        issue_family=family,
        issue_subtype=subtype,
        decision_stage=decision_stage,
        action_mode=action_mode,
        resolution_state=resolution_state,
        risk_level=risk_level,
        applied_rules=applied_rules,
        missing_information=missing_information,
        decisive_evidence=decisive,
        unresolved_gap=unresolved,
        confidence=final_confidence,
    )
    result["matched_historical_case_details"] = [
        {
            "bug_id": bug.bug_id,
            "project": bug.project,
            "component": bug.component,
            "status": bug.status,
            "subject": bug.subject,
            "description_excerpt": _excerpt(bug.description, 180),
            "match_reasons": bug.match_reasons or _fallback_match_reasons(bug),
        }
        for bug in matched_bugs[:3]
    ]

    ordered_result: dict[str, Any] = {}
    for key in template:
        ordered_result[key] = result.get(key, template[key])
    for key, value in result.items():
        if key not in ordered_result:
            ordered_result[key] = value
    return ordered_result


def collect_missing_information(
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
    *,
    stage: str = "triage",
    issue_subtype: str = "",
) -> list[str]:
    missing: list[str] = []

    if stage == "triage":
        if not (case_data.log_snippet or _has_any(case_data.combined_text(), ["aer", "width x2", "vref", "button signal", "no response"])):
            missing.append("raw fail signature under the original trigger")
        if not (case_data.test_case or case_data.expected_config or case_data.test_procedure):
            missing.append("original test condition or expected behavior")
        if not _contains_fail_rate(case_data.fail_rate or case_data.combined_text()):
            missing.append("reproduction rate or fail scope")
    elif stage == "investigation":
        if not (case_data.current_config or case_data.component):
            missing.append("failing configuration or affected component mapping")
        missing.append(_investigation_need(issue_subtype))
    elif stage == "root-cause identified":
        missing.append("verification plan under the original fail condition")
        if not (case_data.comments or case_data.known_context):
            missing.append("supporting note that explains why the proposed root cause is likely")
    elif stage == "verification":
        missing.append("PASS or retest result under the original fail condition")
        missing.append(_verification_need(issue_subtype))
    elif stage == "closure":
        missing.append("closure package: final PASS evidence, fix scope, and traceable status note")

    if not case_data.reporter_role:
        missing.append("reporter role / issue finder")
    if not matched_bugs:
        missing.append("relevant historical reference pattern")

    return _dedupe([item for item in missing if item and not _already_present(item, case_data, stage, issue_subtype)])


def build_decision_text(
    *,
    case_data: NormalizedCase,
    issue_family: str,
    issue_subtype: str,
    decision_stage: str,
    risk_level: str,
    evidence_quality: str,
    confidence: str,
) -> str:
    role = case_data.reporter_role.upper() if case_data.reporter_role else "UNKNOWN"
    return (
        f"{role} case is currently treated as {decision_stage} stage. "
        f"Likely issue family/subtype = {issue_family} / {issue_subtype}. "
        f"Current risk = {risk_level}, evidence quality = {evidence_quality}, confidence = {confidence}. "
        "This output is meant to support the next engineering decision under incomplete information, not to claim a final answer."
    )


def build_decision_text_zh(
    *,
    case_data: NormalizedCase,
    issue_subtype: str,
    decision_stage: str,
    risk_level: str,
    confidence: str,
) -> str:
    role = case_data.reporter_role.upper() if case_data.reporter_role else "未知角色"
    return (
        f"目前將這個 {role} case 視為「{_stage_zh(decision_stage)}」。"
        f"較可能屬於「{issue_subtype}」，目前風險評估為 {risk_level}，信心為{_confidence_zh(confidence)}。"
        "這份輸出是用來協助 AE / PM / RD / DQA 在資訊尚未完整時更快形成 decision-ready view，"
        "不是直接宣稱已找到最終答案。"
    )


def build_uncertainty_summary(
    *,
    decision_stage: str,
    confidence: str,
    missing_information: list[str],
    unresolved_gap: list[str],
) -> str:
    if confidence == "high" and not unresolved_gap:
        return (
            f"Uncertainty is limited for the current {decision_stage} view, "
            "but the output should still be treated as decision assistance rather than a definitive answer."
        )
    parts = [f"Current confidence is {confidence} at {decision_stage} stage."]
    if missing_information:
        parts.append("The most useful missing information is: " + ", ".join(missing_information[:3]) + ".")
    if unresolved_gap:
        parts.append("The current stage still depends on: " + ", ".join(unresolved_gap[:3]) + ".")
    return " ".join(parts)


def collect_lifecycle_signals(case_data: NormalizedCase) -> list[str]:
    signals: list[str] = []
    if case_data.has_root_cause_signal:
        signals.append("root-cause signal")
    if case_data.has_solution_signal:
        signals.append("solution/fix signal")
    if case_data.has_verification_signal:
        signals.append("verification signal")
    if case_data.has_pass_signal:
        signals.append("PASS signal")
    return signals


def build_lifecycle_evidence_summary(case_data: NormalizedCase) -> str:
    status = case_data.status_current or case_data.status or "N/A"
    history = ", ".join(case_data.status_history or [])
    signals = ", ".join(collect_lifecycle_signals(case_data))
    parts = [f"Normalized lifecycle status = {status}."]
    if history:
        parts.append(f"Status history = {history}.")
    if signals:
        parts.append(f"Lifecycle signals = {signals}.")
    if case_data.status_history_events:
        parts.append(f"Status history events = {len(case_data.status_history_events)}.")
    if case_data.lifecycle_signal_items:
        parts.append(f"Lifecycle signal items = {len(case_data.lifecycle_signal_items)}.")
    return " ".join(parts)


def build_lifecycle_evidence_summary_zh(case_data: NormalizedCase) -> str:
    status = case_data.status_current or case_data.status or "N/A"
    history = "、".join(case_data.status_history or [])
    signals = "、".join(_lifecycle_signal_zh(item) for item in collect_lifecycle_signals(case_data))
    parts = [f"正規化後的 lifecycle status = {status}。"]
    if history:
        parts.append(f"狀態歷程 = {history}。")
    if signals:
        parts.append(f"已抽取到的 lifecycle 訊號 = {signals}。")
    if case_data.status_history_events:
        parts.append(f"狀態事件數 = {len(case_data.status_history_events)}。")
    if case_data.lifecycle_signal_items:
        parts.append(f"lifecycle 訊號項目數 = {len(case_data.lifecycle_signal_items)}。")
    return "".join(parts)


def build_uncertainty_summary_zh(
    *,
    decision_stage: str,
    confidence: str,
    missing_information: list[str],
    unresolved_gap: list[str],
) -> str:
    if confidence == "high" and not unresolved_gap:
        return (
            f"目前對「{_stage_zh(decision_stage)}」的判讀已相對穩定，但仍應視為工程決策輔助，"
            "不是最終定論。"
        )
    parts = [f"目前在「{_stage_zh(decision_stage)}」階段的判斷信心為{_confidence_zh(confidence)}。"]
    if missing_information:
        parts.append("最值得優先補齊的資訊包括：" + "、".join(missing_information[:3]) + "。")
    if unresolved_gap:
        parts.append("現階段仍卡住的關鍵缺口是：" + "、".join(unresolved_gap[:3]) + "。")
    return "".join(parts)


def build_next_step_focus(
    *,
    action_mode: str,
    issue_subtype: str,
    decision_stage: str,
    resolution_state: str,
    case_data: NormalizedCase,
) -> str:
    if action_mode == "close":
        if issue_subtype.startswith("memory /"):
            return "Prioritize assembling the closure package: final BIOS or DIMM matrix, PASS evidence on the original fail case, and a traceable closure note."
        if issue_subtype == "PCIe / link width downgrade":
            return "Prioritize closure-grade PASS evidence on the original node and slot, not another broad repro sweep."
        return "Prioritize the closure package: final PASS evidence, fix scope, and traceable status history."

    if action_mode == "verify":
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "Prioritize verifying the original AC restore or runtime trigger and confirming the failing AER signature is gone."
        if issue_subtype == "PCIe / link width downgrade":
            return "Prioritize confirming x4 stays on the same node and slot after reboot or power cycle, before running broader stress."
        if issue_subtype == "power-reset / front panel button signal issue":
            return "Prioritize confirming the reworked sample passes the original reset-button case before discussing closure."
        if issue_subtype.startswith("memory /"):
            return "Prioritize proving the final BIOS or DIMM setup passes the original failing matrix before any closure discussion."
        return "Prioritize verification under the original fail condition before any closure decision."

    if action_mode == "investigate":
        if issue_subtype == "PCIe / slot-path-location specific defect":
            return "Prioritize confirming whether the symptom stays with the same slot, riser, or path rather than broad reproduction."
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "Prioritize the raw trigger-condition log that can separate endpoint, slot-path, and root-port branches."
        if issue_subtype.startswith("memory /"):
            return "Prioritize the smallest BIOS and DIMM matrix that can separate population, setting, and margin branches."
        return "Prioritize the one compare step that can eliminate the most likely wrong branches."

    if issue_subtype == "PCIe / link width downgrade":
        return "Prioritize confirming whether x2 is fixed to the same node, slot, or tray before running wider stress or reboot loops."
    if issue_subtype == "power-reset / front panel button signal issue":
        return "Prioritize confirming the reset-button symptom on the original setup and capturing one decisive signal trace."
    if issue_subtype.startswith("memory /"):
        return "Prioritize preserving the exact fail topology and BIOS setting before the next comparison step."
    return "Prioritize the first branch-separating evidence instead of a broad rerun."


def build_next_step_focus_zh(
    *,
    action_mode: str,
    issue_subtype: str,
    decision_stage: str,
    resolution_state: str,
    case_data: NormalizedCase,
) -> str:
    _ = decision_stage
    _ = resolution_state
    _ = case_data
    if action_mode == "close":
        if issue_subtype.startswith("memory /"):
            return "優先整理可支撐 closure 的 PASS 證據、最終 BIOS／DIMM matrix，以及可追溯的 closure note。"
        if issue_subtype == "PCIe / link width downgrade":
            return "優先補齊原 fail node/slot 的 x4 PASS 證據，而不是再做一輪沒有聚焦的重跑。"
        return "優先把 PASS 證據、fix 範圍與 status trace 整理成 closure package。"

    if action_mode == "verify":
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "優先確認原本 AC restore／runtime trigger 下的 AER symptom 是否已消失，再決定能否往 closure 推進。"
        if issue_subtype == "PCIe / link width downgrade":
            return "優先確認原 fail 的 node／slot 在 reboot 或 power cycle 後都維持 x4，而不是先全面重跑。"
        if issue_subtype == "power-reset / front panel button signal issue":
            return "優先確認 reworked sample 是否已在原 Reset Button case 下完成穩定 PASS。"
        if issue_subtype.startswith("memory /"):
            return "優先確認最終 BIOS／DIMM 組態是否已在原 fail matrix 下完成複驗 PASS。"
        return "優先在原 fail 條件下完成複驗，再決定是否能往 closure 前進。"

    if action_mode == "investigate":
        if issue_subtype == "PCIe / slot-path-location specific defect":
            return "優先確認問題是否固定跟隨同一個 slot／riser／path，而不是先全面重跑。"
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "優先補抓原始 trigger 條件下的 AER log，先把 endpoint、slot path、root port 三個分支切開。"
        if issue_subtype.startswith("memory /"):
            return "優先用最小的 BIOS／DIMM 對照矩陣，把 population、setting、margin 三個方向切開。"
        return "優先做一個最能切分分支的對照動作，而不是先擴大測試範圍。"

    if issue_subtype == "PCIe / link width downgrade":
        return "優先確認 x2 是否固定在同一個 node／slot／tray，而不是先全面重跑。"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "優先確認原 setup 下的 reset 症狀是否可穩定重現，並先補一組決定性的訊號量測。"
    if issue_subtype.startswith("memory /"):
        return "優先保留原始 fail 的 DIMM 組態與 BIOS 設定，再做下一步對照。"
    return "優先補一個能切分主要分支的證據，不要先做沒有聚焦的重跑。"


def build_recommended_action_zh(
    *,
    action_mode: str,
    issue_subtype: str,
    resolution_state: str,
    case_data: NormalizedCase,
) -> str:
    _ = resolution_state
    if action_mode == "close":
        if issue_subtype == "PCIe / link width downgrade":
            return "先整理原 fail node／slot 的 x4 PASS log，以及 tray／riser／板件變更前後的對照證據，再考慮結案。"
        if issue_subtype == "power-reset / front panel button signal issue":
            return "先確認 reworked sample 已在原 front panel reset 測試下穩定 PASS，並把 reset 訊號根因與板件修改記錄整理進 closure note。"
        if issue_subtype.startswith("memory /"):
            return "先確認最終採用的 BIOS training／DIMM 組態已在原 fail matrix 下 PASS，再把 RMT 結果、設定值與 closure note 整理完整。"
        return "先把最終 PASS 證據、fix 範圍與可追溯 status 記錄整理齊全，再結案。"

    if action_mode == "verify":
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "先在原本 AC restore／runtime 條件下複驗，確認 uncorrectable AER／ACS violation 已消失，並保留完整 cycle log，通過後再考慮結案。"
        if issue_subtype == "PCIe / corrected AER":
            return "先在原 stress phase 下複驗 corrected AER 是否已降到可接受範圍，並保留同一路徑的 before/after log。"
        if issue_subtype == "PCIe / slot-path-location specific defect":
            return "先用原 slot／riser 對照矩陣驗證修正是否有效，確認症狀不再固定跟隨同一路徑後，再往 closure 推進。"
        if issue_subtype == "PCIe / link width downgrade":
            return "先在原 fail 的 node／slot 上做 reboot／power cycle 複驗，確認每次都維持 x4，並附上 before/after scan compare log。"
        if issue_subtype == "power-reset / front panel button signal issue":
            return "先用原 fail 條件重做 front panel reset 測試，確認 reworked board 已可穩定 reboot；再補上 reset 訊號與 PASS 紀錄。"
        if issue_subtype == "memory / DIMM population sensitive":
            return "先用原 fail 的 DIMM population 與最終 BIOS 設定做複驗，確認不是只有 1DPC 才 PASS，之後再決定是否能結案。"
        if issue_subtype == "memory / BIOS-setting dependent":
            return "先用最終 BIOS setting 在原 fail matrix 下複驗，確認 PASS 並保留設定值，再評估是否可結案。"
        if issue_subtype == "memory / margin fail":
            return "先用原 fail case 重新跑 margin／RMT，確認修正後已回到規格範圍，再考慮結案。"
        return "先在原 fail 條件下完成複驗 PASS，再決定是否能往 closure 前進。"

    if action_mode == "investigate":
        if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
            return "先在原始 trigger 條件下重抓 AER log，確認錯誤是固定跟隨 endpoint、slot path 還是 root port，再決定後續調查分支。"
        if issue_subtype == "PCIe / corrected AER":
            return "先把 corrected AER 的 port／device mapping 補齊，並比較同一 endpoint 在不同路徑下的差異。"
        if issue_subtype == "PCIe / slot-path-location specific defect":
            return "先做 slot／riser 對調比對，確認問題是否固定跟隨位置，而不是先擴大重跑範圍。"
        if issue_subtype == "power-reset / front panel button signal issue":
            return "先量測 front panel reset 訊號在按鍵時的電位與波形，確認是否只有特定板上路徑或 FB board 組態會失效。"
        if issue_subtype == "memory / DIMM population sensitive":
            return "先以單支 DIMM／每 channel 1 DIMM 和原 fail population 做對照，確認是否屬於 population-sensitive 問題。"
        if issue_subtype == "memory / BIOS-setting dependent":
            return "先在相同 DIMM 組態下比較目前 BIOS setting 與已知可 PASS 的 setting，確認失效是否由 training 條件造成。"
        if issue_subtype == "memory / margin fail":
            return "先在原 setup 下重跑 margin item，記錄實際 Vref／margin 偏移量，確認是否真的是貼近規格邊界。"
        return "先做一個能切分主要原因分支的對照動作，再決定後續調查方向。"

    if issue_subtype == "PCIe / link width downgrade":
        return "先做 Node／slot／tray 對調比對，確認 x2 是否固定跟隨同一路徑，並保留原始 link status 與 scan compare log。"
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return "先補抓原始 trigger 條件下的 AER／ACS violation log，再決定要往 endpoint、slot path 還是 root port 分支調查。"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "先確認原始 reset button 測試是否可穩定重現，並補一組 reset 訊號量測，再決定是否進入硬體 rework。"
    if issue_subtype == "memory / DIMM population sensitive":
        return "先以 1DPC 與原 fail DIMM population 做對照，確認是否只有特定插滿方式才會 fail。"
    if issue_subtype == "memory / BIOS-setting dependent":
        return "先比較 fail 與 pass 的 BIOS training 設定，確認問題是否確實受 BIOS 條件影響。"
    if issue_subtype == "memory / margin fail":
        return "先重跑原 fail margin item，確認實際數值是否仍跨過規格邊界。"
    return "先補齊能切分主要原因分支的證據，再進入下一階段。"


def build_root_cause_hypothesis_zh(*, issue_subtype: str, case_data: NormalizedCase) -> str:
    _ = case_data
    if issue_subtype == "PCIe / corrected AER":
        return "較可能是特定 PCIe 路徑上的 corrected AER 雜訊或訊號完整性問題，而非立即可視為致命失效。"
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return "較可能與 AC restore 或 runtime 條件下的 PCIe routing／compatibility 行為有關，仍需再區分 endpoint、slot path 與 root port。"
    if issue_subtype == "PCIe / link width downgrade":
        return "較可能是特定 NVMe／E3.S 路徑的 lane training 或接觸／訊號完整性異常，導致原本應為 x4 的連線降成 x2。"
    if issue_subtype == "PCIe / slot-path-location specific defect":
        return "較可能是固定 slot／riser／小板路徑異常，而非 endpoint 本身異常。"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "較可能是 front panel reset 訊號電位或板上路徑異常，而不是單純軟體流程問題。"
    if issue_subtype == "memory / margin fail":
        return "較可能是 memory margin 餘裕不足，特定測項在目前條件下貼近或低於規格邊界。"
    if issue_subtype == "memory / DIMM population sensitive":
        return "較可能與 DIMM 顆粒配置或 population 拓樸有關，同一 BIOS 條件下不同插滿方式會改變 margin。"
    if issue_subtype == "memory / BIOS-setting dependent":
        return "較可能與 BIOS training 條件有關，需區分設定變更帶來的 PASS 與硬體本身餘裕。"
    return "目前較像是不完整的故障模式，還需要更多能切分原因分支的證據。"


def build_reasoning_trace(
    *,
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
    issue_family: str,
    issue_subtype: str,
    decision_stage: str,
    action_mode: str,
    resolution_state: str,
    risk_level: str,
    applied_rules: list[str],
    missing_information: list[str],
    decisive_evidence: list[str],
    unresolved_gap: list[str],
    confidence: str,
) -> list[str]:
    trace: list[str] = []
    role_label = case_data.reporter_role or "Unknown reporter"

    trace.append(f"Source context = {role_label} case.")
    trace.append(f"Issue family = {issue_family}; issue subtype = {issue_subtype}.")
    trace.append(
        f"Decision stage = {decision_stage}; action mode = {action_mode}; resolution state = {resolution_state}; confidence = {confidence}."
    )
    trace.append(build_risk_reason(issue_subtype=issue_subtype, risk_level=risk_level, applied_rules=applied_rules))

    if decisive_evidence:
        trace.append("Decisive evidence includes: " + ", ".join(decisive_evidence[:4]) + ".")
    if missing_information:
        trace.append("Missing information still affecting this stage: " + ", ".join(missing_information[:3]) + ".")
    if unresolved_gap:
        trace.append("Current stage still depends on: " + ", ".join(unresolved_gap[:3]) + ".")

    trace.append("Retrieved historical cases are treated as reference patterns rather than final answers.")
    for bug in matched_bugs[:3]:
        reasons = ", ".join(bug.match_reasons or _fallback_match_reasons(bug))
        trace.append(f"Historical bug {bug.bug_id} matched because of {reasons}.")
    return trace


def build_reasoning_trace_zh(
    *,
    case_data: NormalizedCase,
    matched_bugs: list[HistoricalBug],
    issue_family: str,
    issue_subtype: str,
    decision_stage: str,
    action_mode: str,
    resolution_state: str,
    risk_level: str,
    applied_rules: list[str],
    missing_information: list[str],
    decisive_evidence: list[str],
    unresolved_gap: list[str],
    confidence: str,
) -> list[str]:
    trace: list[str] = []
    role_label = case_data.reporter_role or "未知角色"

    trace.append(f"來源脈絡 = {role_label} 提出的 case。")
    trace.append(f"目前較可能的 issue family = {issue_family}；issue subtype = {issue_subtype}。")
    trace.append(
        f"目前判為「{_stage_zh(decision_stage)}」，對應 action mode = {_action_mode_zh(action_mode)}，"
        f"resolution state = {resolution_state}，信心 = {_confidence_zh(confidence)}。"
    )
    trace.append(build_risk_reason_zh(issue_subtype=issue_subtype, risk_level=risk_level, applied_rules=applied_rules))

    if decisive_evidence:
        trace.append("這一輪最有決定性的證據包括：" + "、".join(decisive_evidence[:4]) + "。")
    if missing_information:
        trace.append("目前仍會影響判斷品質的缺資訊包括：" + "、".join(missing_information[:3]) + "。")
    if unresolved_gap:
        trace.append("要把案件往下一個決策階段推進，還需要補齊：" + "、".join(unresolved_gap[:3]) + "。")

    trace.append("歷史案例只拿來當參考模式，不直接當成這個 case 的最終答案。")
    for bug in matched_bugs[:3]:
        reasons = "、".join(_reason_zh(item) for item in (bug.match_reasons or _fallback_match_reasons(bug)))
        trace.append(f"參考案例 {bug.bug_id} 被拉進來，是因為它與目前 case 具有：{reasons}。")
    return trace


def build_risk_reason(*, issue_subtype: str, risk_level: str, applied_rules: list[str]) -> str:
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return (
            f"Risk level = {risk_level} because the current evidence points to an uncorrectable PCIe path failure under the trigger condition, "
            "which should be verified before shipment review can move forward."
        )
    if issue_subtype == "PCIe / link width downgrade":
        return (
            f"Risk level = {risk_level} because the endpoint is enumerating below expected width, which is already a functional path regression "
            "even before the final root cause is confirmed."
        )
    if issue_subtype == "power-reset / front panel button signal issue":
        return (
            f"Risk level = {risk_level} because the front-panel reset path is a user-visible control path, and the case still needs fix or verification "
            "evidence before it can leave shipment review scope."
        )
    if issue_subtype.startswith("memory /"):
        return (
            f"Risk level = {risk_level} because the current evidence shows a reproducible memory margin or population-sensitive branch, "
            "but the practical shipment decision depends on final BIOS, DIMM topology, and verification evidence."
        )
    if applied_rules:
        return f"Risk level = {risk_level} because these severity signals matched: " + "; ".join(applied_rules[:3]) + "."
    return f"Risk level = {risk_level} based on the currently available failure evidence."


def build_risk_reason_zh(*, issue_subtype: str, risk_level: str, applied_rules: list[str]) -> str:
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return f"目前風險評估為 {risk_level}，因為原始 trigger 下已出現 uncorrectable AER／ACS violation，這類訊號代表路徑穩定性仍需先被複驗。"
    if issue_subtype == "PCIe / link width downgrade":
        return f"目前風險評估為 {risk_level}，因為 endpoint 已經從預期的 x4 降成 x2，這本身就是明確的路徑功能／效能退化。"
    if issue_subtype == "power-reset / front panel button signal issue":
        return f"目前風險評估為 {risk_level}，因為這是 front-panel reset 這種使用者可見的控制路徑問題，在 fix 與複驗證據補齊前不宜低估。"
    if issue_subtype.startswith("memory /"):
        return f"目前風險評估為 {risk_level}，因為現有證據顯示 memory margin 或 DIMM population 分支確實會改變 PASS／FAIL，但真正的出貨判斷仍取決於最終 BIOS、DIMM 拓樸與複驗結果。"
    if applied_rules:
        return f"目前風險評估為 {risk_level}，因為目前 case 仍符合以下嚴重度訊號：" + "；".join(applied_rules[:3]) + "。"
    return f"目前風險評估為 {risk_level}，主要依據是目前已收集到的失效訊號。"


def assess_evidence_quality(case_data: NormalizedCase, missing_information: list[str]) -> str:
    score = 0
    if case_data.issue_description:
        score += 1
    if case_data.fail_rate:
        score += 1
    if case_data.test_case or case_data.test_procedure:
        score += 1
    if case_data.current_config or case_data.expected_config:
        score += 1
    if case_data.comments or case_data.log_snippet:
        score += 1
    if len(missing_information) <= 1:
        score += 1

    if score >= 5:
        return "rich"
    if score >= 3:
        return "medium"
    return "limited"


def estimate_confidence(
    *,
    evidence_quality: str,
    stage: str,
    decisive_count: int,
    unresolved_count: int,
) -> str:
    score = 0
    if evidence_quality == "rich":
        score += 2
    elif evidence_quality == "medium":
        score += 1
    if stage in {"root-cause identified", "verification", "closure"}:
        score += 1
    if decisive_count >= 2:
        score += 1
    if unresolved_count == 0:
        score += 1
    elif unresolved_count >= 3:
        score -= 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _investigation_need(issue_subtype: str) -> str:
    if issue_subtype == "PCIe / link width downgrade":
        return "slot/node/tray compare result that shows whether x2 follows the path"
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return "original AER log with endpoint, slot-path, and root-port mapping"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "reset-signal measurement or failing board-path evidence"
    if issue_subtype.startswith("memory /"):
        return "BIOS-setting and DIMM-population matrix that separates the failing branch"
    return "branch-separating compare evidence"


def _verification_need(issue_subtype: str) -> str:
    if issue_subtype == "PCIe / link width downgrade":
        return "x4 verification logs on the original node and slot"
    if issue_subtype == "PCIe / uncorrectable AER or ACS violation":
        return "full-cycle PASS log showing the original AER or ACS signature is gone"
    if issue_subtype == "power-reset / front panel button signal issue":
        return "reworked-sample PASS result on the original reset-button case"
    if issue_subtype.startswith("memory /"):
        return "PASS result on the original memory margin matrix plus final BIOS/DIMM setting record"
    return "verification evidence under the original fail condition"


def _already_present(item: str, case_data: NormalizedCase, stage: str, issue_subtype: str) -> bool:
    text = case_data.combined_text().lower()
    if item == "reproduction rate or fail scope":
        return _contains_fail_rate(case_data.fail_rate or case_data.combined_text())
    if item == "raw fail signature under the original trigger":
        return _has_any(text, ["aer", "width x2", "vref", "button signal", "no response", "fail"])
    if item == "original test condition or expected behavior":
        return bool(case_data.test_case or case_data.test_procedure or case_data.expected_config)
    if item == "failing configuration or affected component mapping":
        return bool(case_data.current_config or case_data.component)
    if item == "verification plan under the original fail condition":
        return _has_any(text, ["verify", "verification", "retest", "ready for dqa test"])
    if item == "supporting note that explains why the proposed root cause is likely":
        return bool(case_data.comments or case_data.known_context)
    if item == "PASS or retest result under the original fail condition":
        return _has_any(text, ["pass", "verified", "retest pass"])
    if item == "closure package: final PASS evidence, fix scope, and traceable status note":
        return _has_any(text, ["pass", "fixed", "closed", "resolved"])
    if item == _investigation_need(issue_subtype):
        return False
    if item == _verification_need(issue_subtype):
        return _has_any(text, ["pass", "verified", "retest pass"])
    return False


def _stage_gap_from_missing(missing_information: list[str], decision_stage: str) -> list[str]:
    if decision_stage in {"triage", "investigation"}:
        return missing_information[:2]
    return missing_information[:1]


def _excerpt(text: str, limit: int) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _fallback_match_reasons(bug: HistoricalBug) -> list[str]:
    reasons: list[str] = []
    haystack = " ".join([bug.subject or "", bug.description or "", bug.component or ""]).lower()
    if _has_any(haystack, ["aer", "pcie", "slot", "riser", "link width"]):
        reasons.append("same issue family")
    if _has_any(haystack, ["pass", "verify", "retest", "fixed"]):
        reasons.append("same recovery pattern")
    if _has_any(haystack, ["ac", "runtime", "reboot", "power cycle"]):
        reasons.append("same trigger condition")
    return reasons or ["same issue family"]


def _contains_fail_rate(text: str) -> bool:
    import re

    return bool(re.search(r"\d+\s*/\s*\d+", text or ""))


def _has_any(text: str, keywords: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = str(item).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def _confidence_zh(confidence: str) -> str:
    mapping = {"high": "高", "medium": "中", "low": "低"}
    return mapping.get(confidence, confidence)


def _stage_zh(stage: str) -> str:
    mapping = {
        "triage": "初判／分流",
        "investigation": "調查中",
        "root-cause identified": "已鎖定可能根因",
        "verification": "複驗中",
        "closure": "可進入結案判斷",
    }
    return mapping.get(stage, stage)


def _action_mode_zh(mode: str) -> str:
    mapping = {
        "triage": "先補齊初判資訊",
        "investigate": "進一步調查",
        "verify": "先做複驗／驗證",
        "close": "整理結案資料",
    }
    return mapping.get(mode, mode)


def _reason_zh(reason: str) -> str:
    mapping = {
        "same issue family": "同 issue family",
        "same issue subtype": "同 issue subtype",
        "same fail signal": "同失效訊號",
        "same trigger condition": "同觸發條件",
        "same recovery pattern": "同修復／複驗模式",
        "same test context": "同測試情境",
        "same project": "同專案脈絡",
    }
    return mapping.get(reason, reason)


def _lifecycle_signal_zh(signal: str) -> str:
    mapping = {
        "root-cause signal": "根因訊號",
        "solution/fix signal": "solution/fix 訊號",
        "verification signal": "verification 訊號",
        "PASS signal": "PASS 訊號",
    }
    return mapping.get(signal, signal)


def _event_source_fields(events: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in events:
        source_field = str(item.get("source_field", "") or "")
        if source_field and source_field not in seen:
            seen.add(source_field)
            ordered.append(source_field)
    return ordered


def _signal_source_fields(items: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        source_field = str(item.get("source_field", "") or "")
        if source_field and source_field not in seen:
            seen.add(source_field)
            ordered.append(source_field)
    return ordered


def _sample_signal_item(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for preferred_source in ["comments", "known_context", "test_procedure", "issue_description", "status_current", "status"]:
        for item in items:
            if str(item.get("source_field", "") or "") == preferred_source:
                return item
    return items[0] if items else None


def _lifecycle_signal_zh(signal: str) -> str:
    mapping = {
        "root-cause signal": "根因訊號",
        "solution/fix signal": "修正方案訊號",
        "verification signal": "複驗訊號",
        "PASS signal": "PASS 訊號",
    }
    return mapping.get(signal, signal)


def collect_lifecycle_signals(case_data: NormalizedCase) -> list[str]:
    if case_data.lifecycle_signal_items:
        ordered: list[str] = []
        seen: set[str] = set()
        for item in case_data.lifecycle_signal_items:
            signal_type = str(item.get("signal_type", "") or "")
            if signal_type and signal_type not in seen:
                seen.add(signal_type)
                ordered.append(signal_type)
        if ordered:
            return ordered
    signals: list[str] = []
    if case_data.has_root_cause_signal:
        signals.append("root-cause signal")
    if case_data.has_solution_signal:
        signals.append("solution/fix signal")
    if case_data.has_verification_signal:
        signals.append("verification signal")
    if case_data.has_pass_signal:
        signals.append("PASS signal")
    return signals


def build_lifecycle_evidence_summary(case_data: NormalizedCase) -> str:
    status = case_data.status_current or case_data.status or "N/A"
    history = ", ".join(case_data.status_history or [])
    signals = ", ".join(collect_lifecycle_signals(case_data))
    parts = [f"Normalized lifecycle status = {status}."]
    if history:
        parts.append(f"Status history = {history}.")
    if signals:
        parts.append(f"Lifecycle signals = {signals}.")
    if case_data.status_history_events:
        parts.append(f"Status history events = {len(case_data.status_history_events)}.")
        event_sources = ", ".join(_event_source_fields(case_data.status_history_events))
        if event_sources:
            parts.append(f"Status transitions were found in: {event_sources}.")
    if case_data.lifecycle_signal_items:
        parts.append(f"Lifecycle signal items = {len(case_data.lifecycle_signal_items)}.")
        signal_sources = ", ".join(_signal_source_fields(case_data.lifecycle_signal_items))
        if signal_sources:
            parts.append(f"Lifecycle evidence came from: {signal_sources}.")
        sample = _sample_signal_item(case_data.lifecycle_signal_items)
        if sample:
            parts.append(
                f"Example signal: {sample.get('signal_type')} from {sample.get('source_field')}: "
                f"{sample.get('matched_excerpt') or sample.get('matched_text')}."
            )
    return " ".join(parts)


def build_lifecycle_evidence_summary_zh(case_data: NormalizedCase) -> str:
    status = case_data.status_current or case_data.status or "N/A"
    history = "、".join(case_data.status_history or [])
    signals = "、".join(_lifecycle_signal_zh(item) for item in collect_lifecycle_signals(case_data))
    parts = [f"正規化後的 lifecycle status = {status}。"]
    if history:
        parts.append(f"狀態歷程 = {history}。")
    if signals:
        parts.append(f"已抽取到的 lifecycle 訊號 = {signals}。")
    if case_data.status_history_events:
        parts.append(f"狀態事件數 = {len(case_data.status_history_events)}。")
        event_sources = "、".join(_event_source_fields(case_data.status_history_events))
        if event_sources:
            parts.append(f"狀態轉換訊號主要來自：{event_sources}。")
    if case_data.lifecycle_signal_items:
        parts.append(f"lifecycle 訊號項目數 = {len(case_data.lifecycle_signal_items)}。")
        signal_sources = "、".join(_signal_source_fields(case_data.lifecycle_signal_items))
        if signal_sources:
            parts.append(f"lifecycle 證據主要來自：{signal_sources}。")
        sample = _sample_signal_item(case_data.lifecycle_signal_items)
        if sample:
            parts.append(
                "代表性訊號："
                f"{_lifecycle_signal_zh(str(sample.get('signal_type', '')))}，"
                f"來源欄位 = {sample.get('source_field')}，"
                f"摘要 = {sample.get('matched_excerpt') or sample.get('matched_text')}。"
            )
    return "".join(parts)

