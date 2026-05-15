"""Local HTTP bridge for OpenClaw-style tool invocation.

This module exposes the existing decision-agent flow over a small HTTP API so
an agent runtime can call it as a tool without knowing the internal Python
structure.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from decision_agent.assistant_notes import LocalModelConfig, build_assistant_note
from decision_agent.models import NormalizedCase
from decision_agent.service import analyze_single_case

BRIDGE_NAME = "decision_agent_openclaw_bridge"
BRIDGE_VERSION = "0.1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


@dataclass(frozen=True)
class BridgeConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    decision_root: Path = Path(__file__).resolve().parent
    assistant_mode: str = "none"
    assistant_style: str = "brief"
    local_model_base_url: str = ""
    local_model_model: str = ""
    local_model_api_path: str = "/chat/completions"
    local_model_timeout_seconds: float = 30.0
    local_model_max_tokens: int = 256
    local_model_temperature: float = 0.2


def build_tool_manifest() -> list[dict[str, Any]]:
    """Return a simple tool manifest suitable for agent runtimes."""

    return [
        {
            "name": "analyze_single_case",
            "description": (
                "Analyze one engineering case and return a decision-ready summary "
                "with issue family, issue subtype, decision stage, missing "
                "information, recommended action, and uncertainty signals."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "case_input": {
                        "description": (
                            "Normalized case object or raw case dictionary. "
                            "If you already have a file path, use case_path instead."
                        ),
                        "type": "object",
                    },
                    "case_path": {
                        "description": "Optional path to a JSON or PDF case file.",
                        "type": "string",
                    },
                    "decision_root": {
                        "description": (
                            "Optional path to the decision_agent package root. "
                            "Defaults to the package directory."
                        ),
                        "type": "string",
                    },
                    "output_path": {
                        "description": "Optional path to write the JSON summary.",
                        "type": "string",
                    },
                    "assistant_mode": {
                        "description": (
                            "Optional assistant-note mode. Use 'none' for a deterministic note "
                            "or 'local' to rewrite the summary with a local OpenAI-compatible model."
                        ),
                        "type": "string",
                        "enum": ["none", "local"],
                    },
                    "assistant_style": {
                        "description": (
                            "Optional note style for the assistant output."
                        ),
                        "type": "string",
                        "enum": ["brief", "bullet", "narrative"],
                    },
                    "local_model": {
                        "description": "Optional local model config used when assistant_mode is local.",
                        "type": "object",
                        "properties": {
                            "base_url": {"type": "string"},
                            "model": {"type": "string"},
                            "api_path": {"type": "string"},
                            "timeout_seconds": {"type": "number"},
                            "max_tokens": {"type": "integer"},
                            "temperature": {"type": "number"},
                        },
                        "additionalProperties": False,
                    },
                },
                "additionalProperties": False,
            },
        }
    ]


def invoke_tool(
    tool: str,
    args: dict[str, Any],
    *,
    decision_root: Path,
    config: BridgeConfig | None = None,
) -> dict[str, Any]:
    """Invoke a supported tool by name."""

    tool_name = (tool or "").strip()
    effective_config = config or BridgeConfig()
    if tool_name in {"analyze_single_case", "analyze_case"}:
        return _invoke_analyze_single_case(args, decision_root=decision_root, config=effective_config)
    raise ValueError(f"Unsupported tool: {tool_name!r}")


def run_server(config: BridgeConfig) -> int:
    handler = _build_handler(config)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    print(
        f"{BRIDGE_NAME} listening on http://{config.host}:{config.port} "
        f"(decision_root={config.decision_root}, assistant_mode={config.assistant_mode}, "
        f"assistant_style={config.assistant_style}, local_model={config.local_model_model or 'none'})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the local OpenClaw-style bridge for decision_agent."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--decision-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Path to the decision_agent package root.",
    )
    parser.add_argument(
        "--print-tools",
        action="store_true",
        help="Print the tool manifest as JSON and exit.",
    )
    parser.add_argument("--assistant-mode", default="none", choices=["none", "local"])
    parser.add_argument("--assistant-style", default="brief", choices=["brief", "bullet", "narrative"])
    parser.add_argument("--local-model-base-url", default="")
    parser.add_argument("--local-model-model", default="")
    parser.add_argument("--local-model-api-path", default="/chat/completions")
    parser.add_argument("--local-model-timeout-seconds", type=float, default=30.0)
    parser.add_argument("--local-model-max-tokens", type=int, default=256)
    parser.add_argument("--local-model-temperature", type=float, default=0.2)
    args = parser.parse_args(argv)

    config = BridgeConfig(
        host=args.host,
        port=args.port,
        decision_root=args.decision_root.resolve(),
        assistant_mode=args.assistant_mode,
        assistant_style=args.assistant_style,
        local_model_base_url=args.local_model_base_url,
        local_model_model=args.local_model_model,
        local_model_api_path=args.local_model_api_path,
        local_model_timeout_seconds=args.local_model_timeout_seconds,
        local_model_max_tokens=args.local_model_max_tokens,
        local_model_temperature=args.local_model_temperature,
    )

    if args.print_tools:
        json.dump(build_tool_manifest(), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    return run_server(config)


def _build_handler(config: BridgeConfig) -> type[BaseHTTPRequestHandler]:
    class BridgeHandler(BaseHTTPRequestHandler):
        server_version = f"{BRIDGE_NAME}/{BRIDGE_VERSION}"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            route = urlparse(self.path).path
            if route in {"/", "/health"}:
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "service": BRIDGE_NAME,
                        "version": BRIDGE_VERSION,
                        "decision_root": str(config.decision_root),
                        "assistant_mode": config.assistant_mode,
                        "assistant_style": config.assistant_style,
                        "local_model_configured": bool(
                            config.local_model_base_url.strip() and config.local_model_model.strip()
                        ),
                        "local_model_model": config.local_model_model,
                        "tools": [tool["name"] for tool in build_tool_manifest()],
                    },
                )
                return
            if route in {"/tools", "/manifest"}:
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "service": BRIDGE_NAME,
                        "version": BRIDGE_VERSION,
                        "tools": build_tool_manifest(),
                    },
                )
                return
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "ok": False,
                    "error": {
                        "type": "not_found",
                        "message": f"Unknown route: {route}",
                    },
                },
            )

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            route = urlparse(self.path).path
            try:
                payload = self._read_json_body()
                if route in {"/invoke", "/tools/invoke"}:
                    response = _handle_invoke_request(
                        payload,
                        decision_root=config.decision_root,
                        config=config,
                    )
                    self._send_json(HTTPStatus.OK, response)
                    return
                if route in {"/tools/analyze_single_case", "/analyze_single_case"}:
                    response = _handle_analyze_single_case_request(
                        payload,
                        decision_root=config.decision_root,
                        config=config,
                    )
                    self._send_json(HTTPStatus.OK, response)
                    return
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {
                        "ok": False,
                        "error": {
                            "type": "not_found",
                            "message": f"Unknown route: {route}",
                        },
                    },
                )
            except _RequestError as exc:
                self._send_json(
                    exc.status,
                    {
                        "ok": False,
                        "error": {
                            "type": exc.error_type,
                            "message": exc.message,
                        },
                    },
                )
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                traceback.print_exc()
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {
                        "ok": False,
                        "error": {
                            "type": type(exc).__name__,
                            "message": "Unexpected bridge failure.",
                        },
                    },
                )

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _read_json_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            if content_length <= 0:
                raise _RequestError(HTTPStatus.BAD_REQUEST, "invalid_request", "Request body is required.")
            if content_length > 2 * 1024 * 1024:
                raise _RequestError(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    "payload_too_large",
                    "Request body exceeds the 2 MB bridge limit.",
                )
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise _RequestError(HTTPStatus.BAD_REQUEST, "invalid_json", f"Invalid JSON body: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise _RequestError(
                    HTTPStatus.BAD_REQUEST,
                    "invalid_request",
                    "JSON body must be an object.",
                )
            return payload

        def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return BridgeHandler


def _handle_invoke_request(
    payload: dict[str, Any],
    *,
    decision_root: Path,
    config: BridgeConfig,
) -> dict[str, Any]:
    tool = str(payload.get("tool", "") or payload.get("name", "") or payload.get("action", "") or "")
    args = payload.get("args") or {}
    if not isinstance(args, dict):
        raise _RequestError(HTTPStatus.BAD_REQUEST, "invalid_request", "Field 'args' must be an object.")
    result = invoke_tool(tool, args, decision_root=decision_root, config=config)
    return {
        "ok": True,
        "tool": tool,
        "result": result,
        "bridge": {
            "name": BRIDGE_NAME,
            "version": BRIDGE_VERSION,
            "decision_root": str(decision_root),
        },
    }


def _handle_analyze_single_case_request(
    payload: dict[str, Any],
    *,
    decision_root: Path,
    config: BridgeConfig,
) -> dict[str, Any]:
    result = _invoke_analyze_single_case(payload, decision_root=decision_root, config=config)
    return {
        "ok": True,
        "tool": "analyze_single_case",
        "result": result,
        "bridge": {
            "name": BRIDGE_NAME,
            "version": BRIDGE_VERSION,
            "decision_root": str(decision_root),
        },
    }


def _invoke_analyze_single_case(
    payload: dict[str, Any],
    *,
    decision_root: Path,
    config: BridgeConfig,
) -> dict[str, Any]:
    case_input = _coerce_case_input(payload)
    output_path = payload.get("output_path")
    resolved_output_path = Path(output_path).expanduser() if output_path else None
    requested_root = payload.get("decision_root")
    resolved_root = _resolve_decision_root(
        Path(requested_root).expanduser() if requested_root else None,
        default_root=decision_root,
    )

    started_at = time.perf_counter()
    summary = analyze_single_case(
        case_input,
        decision_root=resolved_root,
        output_path=resolved_output_path,
    )
    assistant_mode = _resolve_assistant_mode(payload, default_mode=config.assistant_mode)
    assistant_style = _resolve_assistant_style(payload, default_style=config.assistant_style)
    local_model = _resolve_local_model_config(payload, default_config=config)
    elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
    assistant = build_assistant_note(
        summary,
        mode=assistant_mode,
        style=assistant_style,
        local_model=local_model,
    )
    return {
        "summary": summary,
        "assistant": assistant,
        "meta": {
            "elapsed_ms": elapsed_ms,
            "decision_root": str(resolved_root),
            "output_path": str(resolved_output_path) if resolved_output_path else "",
            "assistant_mode": assistant["requested_mode"],
            "assistant_style": assistant["style"],
            "local_model_configured": bool(local_model and local_model.base_url.strip() and local_model.model.strip()),
        },
    }


def _coerce_case_input(payload: dict[str, Any]) -> Path | NormalizedCase | dict[str, Any]:
    if "case_input" in payload:
        case_input = payload["case_input"]
        if isinstance(case_input, dict):
            return case_input
        if isinstance(case_input, str):
            return Path(case_input).expanduser()
    if "case_path" in payload:
        return Path(str(payload["case_path"])).expanduser()
    raise _RequestError(
        HTTPStatus.BAD_REQUEST,
        "missing_case_input",
        "Provide either 'case_input' or 'case_path'.",
    )


def _resolve_decision_root(requested_root: Path | None, *, default_root: Path) -> Path:
    if requested_root is None:
        return default_root

    candidate = requested_root.expanduser().resolve()
    if _looks_like_decision_root(candidate):
        return candidate

    nested_candidate = (candidate / "decision_agent").resolve()
    if _looks_like_decision_root(nested_candidate):
        return nested_candidate

    return candidate


def _looks_like_decision_root(path: Path) -> bool:
    required_entries = ["knowledge_base", "rules", "templates"]
    return all((path / entry).exists() for entry in required_entries)


def _resolve_assistant_mode(payload: dict[str, Any], *, default_mode: str) -> str:
    candidate = payload.get("assistant_mode", payload.get("analysis_mode", default_mode))
    normalized = str(candidate or default_mode or "none").strip().lower()
    if normalized in {"local", "local_model", "model", "on"}:
        return "local"
    return "none"


def _resolve_assistant_style(payload: dict[str, Any], *, default_style: str) -> str:
    candidate = str(payload.get("assistant_style", default_style) or default_style or "brief").strip().lower()
    if candidate in {"bullet", "bullets", "list"}:
        return "bullet"
    if candidate in {"narrative", "story", "paragraph"}:
        return "narrative"
    return "brief"


def _resolve_local_model_config(
    payload: dict[str, Any],
    *,
    default_config: BridgeConfig,
) -> LocalModelConfig | None:
    model_payload = payload.get("local_model")
    if model_payload is None:
        model_payload = {}
    if not isinstance(model_payload, dict):
        raise _RequestError(
            HTTPStatus.BAD_REQUEST,
            "invalid_request",
            "Field 'local_model' must be an object when provided.",
        )

    base_url = str(model_payload.get("base_url", default_config.local_model_base_url) or default_config.local_model_base_url).strip()
    model = str(model_payload.get("model", default_config.local_model_model) or default_config.local_model_model).strip()
    api_path = str(model_payload.get("api_path", default_config.local_model_api_path) or default_config.local_model_api_path).strip()
    timeout_seconds = _coerce_number(
        model_payload.get("timeout_seconds", default_config.local_model_timeout_seconds),
        default_config.local_model_timeout_seconds,
    )
    max_tokens = int(
        _coerce_number(
            model_payload.get("max_tokens", default_config.local_model_max_tokens),
            default_config.local_model_max_tokens,
        )
    )
    temperature = _coerce_number(
        model_payload.get("temperature", default_config.local_model_temperature),
        default_config.local_model_temperature,
    )

    if not base_url and not model:
        return None
    if not base_url or not model:
        raise _RequestError(
            HTTPStatus.BAD_REQUEST,
            "invalid_request",
            "Local model config requires both 'base_url' and 'model'.",
        )

    return LocalModelConfig(
        base_url=base_url,
        model=model,
        api_path=api_path or "/chat/completions",
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def _coerce_number(value: Any, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


class _RequestError(Exception):
    def __init__(self, status: HTTPStatus, error_type: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.error_type = error_type
        self.message = message


if __name__ == "__main__":
    raise SystemExit(main())
