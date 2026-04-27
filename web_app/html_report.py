"""Simple bilingual single-case HTML report for the decision-agent MVP."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def write_single_case_report(
    *,
    case_payload: dict[str, Any],
    summary: dict[str, Any],
    target_path: Path,
) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        build_single_case_report(case_payload=case_payload, summary=summary),
        encoding="utf-8",
    )
    return target_path


def build_single_case_report(
    *,
    case_payload: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    title = summary.get("case_id") or case_payload.get("case_id") or "Decision Agent Report"
    reasoning_pairs = _pair_reasoning(
        summary.get("reasoning_trace", []) or [],
        summary.get("reasoning_trace_zh", []) or [],
    )

    body = """
    <section class="hero" id="summary">
      <p class="eyebrow">AI Engineering Decision Agent / AI 工程決策代理</p>
      <h1>{title}</h1>
      <p class="lead">{decision_summary}</p>
      <p class="lead zh-lead">{decision_summary_zh}</p>
      <div class="hero-metrics">
        <div><span>Issue Family / 問題家族</span><strong>{issue_family}</strong></div>
        <div><span>Issue Subtype / 問題子型</span><strong>{issue_subtype}</strong></div>
        <div><span>Decision Stage / 決策階段</span><strong>{decision_stage}</strong></div>
        <div><span>Risk Level / 風險等級</span><strong>{risk_level}</strong></div>
      </div>
    </section>

    <section id="decision">
      <h2>Decision Summary / 決策摘要</h2>
      {decision_table}
    </section>

    <section id="workflow">
      <h2>Agent Workflow / Agent 分析流程</h2>
      {workflow}
    </section>

    <section id="uncertainty">
      <h2>Uncertainty / 不確定性</h2>
      {uncertainty_table}
    </section>

    <section id="evidence">
      <h2>Decision Evidence / 判斷證據</h2>
      <h3>Decisive Evidence / 關鍵證據</h3>
      {decisive_evidence}
      <h3>Unresolved Gap / 尚未補齊的缺口</h3>
      {unresolved_gap}
      <h3>Missing Information / 還需要補的資訊</h3>
      {missing_information}
    </section>

    <section id="reasoning-trace">
      <h2>Reasoning Trace / 判斷依據</h2>
      {reasoning_trace}
    </section>

    <section id="historical-support">
      <h2>Retrieved References / 檢索到的參考案例</h2>
      {historical_cases}
    </section>

    <section id="input-snapshot">
      <h2>Input Snapshot / 輸入摘要</h2>
      {input_snapshot}
    </section>
    """.format(
        title=html.escape(str(title)),
        decision_summary=html.escape(str(summary.get("decision_summary", "N/A"))),
        decision_summary_zh=html.escape(str(summary.get("decision_summary_zh", "N/A"))),
        issue_family=html.escape(str(summary.get("issue_family", summary.get("issue_type", "N/A")))),
        issue_subtype=html.escape(str(summary.get("issue_subtype", "N/A"))),
        decision_stage=html.escape(str(summary.get("decision_stage", "N/A"))),
        risk_level=html.escape(str(summary.get("risk_level", "N/A"))),
        decision_table=_table(
            [
                ("Case ID / 案件編號", summary.get("case_id") or case_payload.get("case_id")),
                ("Bug ID / Bug 編號", case_payload.get("bug_id")),
                ("Project / 專案", case_payload.get("project")),
                ("Reporter / 提案角色", summary.get("reporter_role", case_payload.get("reporter_role"))),
                ("Issue Family / 問題家族", summary.get("issue_family")),
                ("Issue Subtype / 問題子型", summary.get("issue_subtype")),
                ("Decision Stage / 決策階段", summary.get("decision_stage")),
                ("Action Mode / 執行模式", summary.get("action_mode")),
                ("Resolution State / 目前解決狀態", summary.get("resolution_state")),
                ("Lifecycle Status / lifecycle 狀態", summary.get("lifecycle_status")),
                ("Lifecycle Signals / lifecycle 訊號", ", ".join(summary.get("lifecycle_signals", []) or [])),
                ("Lifecycle Evidence Summary / lifecycle 依據摘要", summary.get("lifecycle_evidence_summary")),
                ("Lifecycle Evidence Summary (ZH) / lifecycle 依據摘要（中文）", summary.get("lifecycle_evidence_summary_zh")),
                ("Status History Events / 狀態事件數", len(summary.get("status_history_events", []) or [])),
                ("Lifecycle Signal Items / lifecycle 訊號項目數", len(summary.get("lifecycle_signal_items", []) or [])),
                ("Confidence / 信心", summary.get("confidence")),
                ("Root Cause Hypothesis / 可能根因", summary.get("root_cause_hypothesis")),
                ("Root Cause Hypothesis (ZH) / 可能根因（中文）", summary.get("root_cause_hypothesis_zh")),
                ("Recommended Action / 建議動作", summary.get("recommended_action")),
                ("Recommended Action (ZH) / 建議動作（中文）", summary.get("recommended_action_zh")),
                ("Next Step Focus / 優先下一步", summary.get("next_step_focus")),
                ("Next Step Focus (ZH) / 優先下一步（中文）", summary.get("next_step_focus_zh")),
                ("Source File / 來源檔案", summary.get("source_file") or case_payload.get("source_file")),
                ("Extraction Status / 解析狀態", case_payload.get("extraction_status")),
            ],
            skip_empty=True,
        ),
        workflow=_workflow_list(),
        uncertainty_table=_table(
            [
                ("Uncertainty Summary / 不確定性摘要", summary.get("uncertainty_summary")),
                ("Uncertainty Summary (ZH) / 不確定性摘要（中文）", summary.get("uncertainty_summary_zh")),
                ("Knowledge Governance Note / 知識治理提醒", summary.get("knowledge_governance_note")),
                ("Knowledge Governance Note (ZH) / 知識治理提醒（中文）", summary.get("knowledge_governance_note_zh")),
            ],
            skip_empty=True,
        ),
        decisive_evidence=_bullet_list(
            summary.get("decisive_evidence", []),
            "No decisive evidence listed. / 目前沒有列出關鍵證據。",
        ),
        unresolved_gap=_bullet_list(
            summary.get("unresolved_gap", []),
            "No unresolved gap listed. / 目前沒有列出尚未補齊的缺口。",
        ),
        missing_information=_bullet_list(
            summary.get("missing_information", []),
            "No missing information called out. / 目前沒有額外標示缺資訊。",
        ),
        reasoning_trace=_reasoning_trace(reasoning_pairs),
        historical_cases=_historical_cases(summary),
        input_snapshot=_table(
            [
                ("Subject / 標題", case_payload.get("subject")),
                ("Lifecycle Status / 目前 lifecycle status", case_payload.get("status_current") or case_payload.get("status")),
                ("Status History / 狀態歷程", ", ".join(case_payload.get("status_history", []) or [])),
                (
                    "Lifecycle Signals / lifecycle 訊號",
                    _format_lifecycle_signals(case_payload),
                ),
                ("Issue Description / 問題描述", case_payload.get("issue_description")),
                ("Log Snippet / Log 片段", case_payload.get("log_snippet")),
                ("Comments / 備註與討論", case_payload.get("comments")),
                ("Current Config / 目前設定", case_payload.get("current_config")),
                ("Expected Config / 預期行為／設定", case_payload.get("expected_config")),
                ("Fail Rate / 失效率", case_payload.get("fail_rate")),
                ("Test Case / 測試項目", case_payload.get("test_case")),
                ("Test Procedure / 測試步驟", case_payload.get("test_procedure")),
                ("Workaround / 暫行處置", case_payload.get("workaround")),
                ("Known Context / 已知背景", case_payload.get("known_context")),
            ],
            skip_empty=True,
        ),
    )

    return """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --surface: #ffffff;
      --ink: #172033;
      --subtle: #5b6577;
      --border: #d7deea;
      --soft-blue: #eef6ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Microsoft JhengHei", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.6;
    }}
    main {{
      max-width: 1040px;
      margin: 0 auto;
      padding: 24px 16px 48px;
    }}
    section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 18px;
      margin-top: 16px;
      overflow: hidden;
    }}
    .hero {{
      background: linear-gradient(135deg, var(--soft-blue), #f8fff8);
    }}
    .eyebrow {{
      margin: 0 0 8px;
      color: var(--subtle);
      font-size: 13px;
      text-transform: uppercase;
    }}
    h1, h2, h3 {{
      margin: 0 0 12px;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .lead {{
      margin: 0;
      font-size: 18px;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .zh-lead {{
      color: var(--subtle);
      font-size: 16px;
      margin-top: 6px;
    }}
    .hero-metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .hero-metrics div {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      background: rgba(255,255,255,0.9);
      min-width: 0;
    }}
    .hero-metrics span {{
      display: block;
      color: var(--subtle);
      font-size: 13px;
      margin-bottom: 4px;
      overflow-wrap: anywhere;
    }}
    .hero-metrics strong {{
      font-size: 20px;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      text-align: left;
      vertical-align: top;
      border-top: 1px solid var(--border);
      padding: 10px 0;
    }}
    th {{
      width: 260px;
      color: var(--subtle);
      font-weight: 600;
      padding-right: 18px;
    }}
    td .field-value {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      max-width: 100%;
    }}
    td .field-value.long {{
      max-height: 280px;
      overflow: auto;
      padding: 10px 12px;
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    li {{
      overflow-wrap: anywhere;
      word-break: break-word;
      margin-bottom: 10px;
    }}
    .empty {{
      color: var(--subtle);
      margin: 0;
    }}
    .workflow-list li {{
      list-style: decimal;
      margin-left: 18px;
    }}
    .workflow-en {{
      display: block;
      font-weight: 600;
    }}
    .workflow-zh {{
      display: block;
      color: var(--subtle);
    }}
    .historical-item {{
      border-top: 1px solid var(--border);
      padding: 12px 0;
    }}
    .historical-item:first-child {{
      border-top: none;
      padding-top: 0;
    }}
    .historical-meta {{
      color: var(--subtle);
      font-size: 14px;
      margin-bottom: 6px;
    }}
    .historical-desc {{
      color: var(--ink);
      font-size: 15px;
    }}
    .reasoning-item {{
      margin-bottom: 12px;
    }}
    .reasoning-zh {{
      display: block;
      color: var(--subtle);
      margin-top: 4px;
    }}
    @media (max-width: 720px) {{
      main {{
        padding: 16px 12px 36px;
      }}
      section {{
        padding: 14px;
      }}
      table, tbody, tr, th, td {{
        display: block;
        width: 100%;
      }}
      th {{
        padding: 10px 0 4px;
      }}
      td {{
        padding: 0 0 10px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>
""".format(title=html.escape(str(title)), body=body)


def _table(rows: list[tuple[str, Any]], *, skip_empty: bool = False) -> str:
    rendered: list[str] = []
    for label, value in rows:
        if skip_empty and not _has_value(value):
            continue
        value_html = _render_value(value)
        rendered.append(
            "<tr><th>{label}</th><td>{value}</td></tr>".format(
                label=html.escape(label),
                value=value_html,
            )
        )
    if not rendered:
        return '<p class="empty">No data. / 目前沒有可顯示資料。</p>'
    return "<div class='table-wrap'><table><tbody>{rows}</tbody></table></div>".format(rows="".join(rendered))


def _render_value(value: Any) -> str:
    if not _has_value(value):
        return "<div class='field-value'>N/A</div>"
    text = str(value)
    css_class = "field-value long" if len(text) > 240 or "\n" in text else "field-value"
    return "<div class='{css_class}'>{text}</div>".format(
        css_class=css_class,
        text=html.escape(text),
    )


def _bullet_list(items: list[Any], empty_text: str) -> str:
    if not items:
        return "<p class='empty'>{}</p>".format(html.escape(empty_text))
    return "<ul>{}</ul>".format(
        "".join("<li>{}</li>".format(html.escape(str(item))) for item in items if _has_value(item))
    )


def _workflow_list() -> str:
    steps = [
        (
            "Agent normalized uploaded evidence into one governed case payload.",
            "Agent 先把文字、附件與補充說明整理成同一份可追溯的 case payload。",
        ),
        (
            "Agent classified issue family, issue subtype, and decision stage under incomplete information.",
            "Agent 在資訊尚未完整時，先判斷問題家族、問題子型與目前決策階段。",
        ),
        (
            "Agent retrieved similar patterns as references rather than definitive answers.",
            "Agent 會找相似案例做參考，但不把歷史案例當成這一案的最終答案。",
        ),
        (
            "Agent produced next-step guidance, missing information, and uncertainty-aware reasoning.",
            "Agent 會輸出下一步調查方向、缺少資訊與帶有不確定性的判斷依據，幫助團隊往 decision-ready 狀態前進。",
        ),
    ]
    items = []
    for english, zh in steps:
        items.append(
            "<li><span class='workflow-en'>{}</span><span class='workflow-zh'>{}</span></li>".format(
                html.escape(english),
                html.escape(zh),
            )
        )
    return "<ol class='workflow-list'>{}</ol>".format("".join(items))


def _pair_reasoning(english: list[str], chinese: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    total = max(len(english), len(chinese))
    for index in range(total):
        en = english[index] if index < len(english) else ""
        zh = chinese[index] if index < len(chinese) else ""
        if en or zh:
            pairs.append((str(en), str(zh)))
    return pairs


def _reasoning_trace(items: list[tuple[str, str]]) -> str:
    if not items:
        return "<p class='empty'>No reasoning trace. / 目前沒有判斷依據條列。</p>"
    rendered = []
    for english, chinese in items:
        rendered.append(
            "<div class='reasoning-item'><div>{}</div>{}</div>".format(
                html.escape(english) if english else "",
                "<span class='reasoning-zh'>{}</span>".format(html.escape(chinese)) if chinese else "",
            )
        )
    return "".join(rendered)


def _historical_cases(summary: dict[str, Any]) -> str:
    details = summary.get("matched_historical_case_details", []) or []
    if not details:
        return "<p class='empty'>No historical reference cases. / 沒有檢索到參考案例。</p>"

    blocks: list[str] = []
    for item in details:
        reasons = item.get("match_reasons", []) or []
        reason_text = ", ".join(str(reason) for reason in reasons) if reasons else "No match reason."
        blocks.append(
            """
            <div class="historical-item">
              <div class="historical-meta">#{bug_id} | {project} | {status}</div>
              <div><strong>{subject}</strong></div>
              <div class="historical-desc">{description}</div>
              <div class="historical-meta">Match reason / 相似原因: {reasons}</div>
            </div>
            """.format(
                bug_id=html.escape(str(item.get("bug_id", "N/A"))),
                project=html.escape(str(item.get("project", "N/A"))),
                status=html.escape(str(item.get("status", "N/A"))),
                subject=html.escape(str(item.get("subject", "N/A"))),
                description=html.escape(str(item.get("description_excerpt", "N/A"))),
                reasons=html.escape(reason_text),
            )
        )
    return "".join(blocks)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return str(value).strip() != ""


def _format_lifecycle_signals(case_payload: dict[str, Any]) -> str:
    labels: list[str] = []
    if case_payload.get("has_root_cause_signal"):
        labels.append("root-cause signal")
    if case_payload.get("has_solution_signal"):
        labels.append("solution/fix signal")
    if case_payload.get("has_verification_signal"):
        labels.append("verification signal")
    if case_payload.get("has_pass_signal"):
        labels.append("PASS signal")
    return ", ".join(labels)
