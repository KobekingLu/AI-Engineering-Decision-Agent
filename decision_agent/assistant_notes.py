"""Assistant-note generation for bridge-style workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class LocalModelConfig:
    base_url: str
    model: str
    api_path: str = "/chat/completions"
    timeout_seconds: float = 30.0
    max_tokens: int = 256
    temperature: float = 0.2


def build_assistant_note(
    summary: dict[str, Any],
    *,
    mode: str = "none",
    style: str = "brief",
    local_model: LocalModelConfig | None = None,
) -> dict[str, Any]:
    """Return a deterministic note or a local-model rewrite with fallback."""

    requested_mode = _normalize_mode(mode)
    normalized_style = _normalize_style(style)
    deterministic_note = _build_deterministic_note(summary, style=normalized_style)

    if requested_mode != "local":
        return {
            "requested_mode": requested_mode,
            "effective_mode": "none",
            "style": normalized_style,
            "note": deterministic_note,
            "source": "deterministic_template",
            "model": "",
            "error": "",
        }

    if local_model is None or not local_model.base_url.strip() or not local_model.model.strip():
        return {
            "requested_mode": "local",
            "effective_mode": "fallback",
            "style": normalized_style,
            "note": deterministic_note,
            "source": "deterministic_template",
            "model": "",
            "error": "Local model configuration is missing.",
        }

    try:
        note = _call_local_chat_model(summary, style=normalized_style, config=local_model)
        return {
            "requested_mode": "local",
            "effective_mode": "local",
            "style": normalized_style,
            "note": note,
            "source": "local_model",
            "model": local_model.model,
            "error": "",
        }
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        return {
            "requested_mode": "local",
            "effective_mode": "fallback",
            "style": normalized_style,
            "note": deterministic_note,
            "source": "deterministic_template",
            "model": local_model.model,
            "error": str(exc),
        }


def _build_deterministic_note(summary: dict[str, Any], *, style: str) -> str:
    stage = str(summary.get("decision_stage", "") or "")
    family = str(summary.get("issue_family", summary.get("issue_type", "")) or "")
    subtype = str(summary.get("issue_subtype", "") or "")
    risk_level = str(summary.get("risk_level", "") or "")
    confidence = str(summary.get("confidence", "") or "")
    next_step = str(summary.get("next_step_focus_zh", summary.get("next_step_focus", "")) or "")
    missing = _join_items(summary.get("missing_information"))
    evidence = _join_items(summary.get("decisive_evidence"))

    if style == "bullet":
        lines = [
            f"- 目前判讀: {stage} / {family} / {subtype}",
            f"- 風險與信心: {risk_level} / {confidence}",
        ]
        if evidence:
            lines.append(f"- 關鍵證據: {evidence}")
        if missing:
            lines.append(f"- 缺資訊: {missing}")
        if next_step:
            lines.append(f"- 下一步: {next_step}")
        return "\n".join(lines)

    if style == "narrative":
        parts = [
            f"目前這個 case 被判讀為 {stage}，較可能屬於 {family} / {subtype}。",
            f"現階段風險為 {risk_level}，信心為 {confidence}。",
        ]
        if evidence:
            parts.append(f"關鍵證據包括 {evidence}。")
        if missing:
            parts.append(f"目前最值得補齊的資訊是 {missing}。")
        if next_step:
            parts.append(f"下一步建議是 {next_step}。")
        return "".join(parts)

    parts = [
        f"目前判讀為 {stage}，較可能屬於 {family} / {subtype}。",
        f"風險為 {risk_level}，信心為 {confidence}。",
    ]
    if next_step:
        parts.append(f"下一步：{next_step}")
    if evidence:
        parts.append(f"關鍵證據：{evidence}")
    if missing:
        parts.append(f"缺資訊：{missing}")
    return " ".join(parts)


def _call_local_chat_model(
    summary: dict[str, Any],
    *,
    style: str,
    config: LocalModelConfig,
) -> str:
    system_prompt = (
        "You are an internal engineering decision assistant. "
        "Rewrite structured case output into a concise Chinese assistant note. "
        "Do not add facts. Do not claim a final root cause. "
        "Keep the note faithful to the summary and useful for human review."
    )
    user_prompt = _build_user_prompt(summary, style=style)
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": False,
    }

    url = config.base_url.rstrip("/") + "/" + config.api_path.lstrip("/")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Local model HTTP error {exc.code}: {detail}") from exc

    data = json.loads(raw)
    note = _extract_chat_content(data)
    if not note.strip():
        raise ValueError("Local model returned an empty completion.")
    return note.strip()


def _build_user_prompt(summary: dict[str, Any], *, style: str) -> str:
    payload = {
        "issue_family": summary.get("issue_family", summary.get("issue_type", "")),
        "issue_subtype": summary.get("issue_subtype", ""),
        "decision_stage": summary.get("decision_stage", ""),
        "risk_level": summary.get("risk_level", ""),
        "confidence": summary.get("confidence", ""),
        "decisive_evidence": summary.get("decisive_evidence", []),
        "missing_information": summary.get("missing_information", []),
        "next_step_focus": summary.get("next_step_focus_zh", summary.get("next_step_focus", "")),
        "recommended_action": summary.get("recommended_action_zh", summary.get("recommended_action", "")),
    }
    return (
        "請根據以下結構化摘要，改寫成精簡的中文助理說明。\n"
        "要求：\n"
        f"- 風格偏好：{style}\n"
        "- 不要新增事實\n"
        "- 不要宣稱最終 root cause\n"
        "- 保留 decision stage、risk、confidence、missing information、next step\n"
        "- 只回傳說明文字，不要額外解釋\n"
        f"結構化摘要：{json.dumps(payload, ensure_ascii=False)}"
    )


def _extract_chat_content(data: Any) -> str:
    if isinstance(data, dict):
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first.get("text")
                if isinstance(text, str):
                    return text
        content = data.get("content")
        if isinstance(content, str):
            return content
        output_text = data.get("output_text")
        if isinstance(output_text, str):
            return output_text
    raise ValueError("Could not extract completion text from local model response.")


def _normalize_mode(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"local", "local_model", "model", "on"}:
        return "local"
    return "none"


def _normalize_style(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"bullet", "bullets", "list"}:
        return "bullet"
    if normalized in {"narrative", "story", "paragraph"}:
        return "narrative"
    return "brief"


def _join_items(value: Any) -> str:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "、".join(items)
    if isinstance(value, str):
        return value.strip()
    return ""
