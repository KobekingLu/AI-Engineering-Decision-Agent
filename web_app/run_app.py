"""Stable local launcher for the Streamlit MVP app."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    streamlit_home = repo_root / ".tmp" / "streamlit_home"
    streamlit_home.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("HOME", str(streamlit_home))
    os.environ.setdefault("USERPROFILE", str(streamlit_home))
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
    os.environ.setdefault("STREAMLIT_SERVER_RUN_ON_SAVE", "false")

    from streamlit.web import cli as stcli

    port = _choose_port([8501, 8502, 8503, 8504, 8505])

    sys.argv = [
        "streamlit",
        "run",
        str(repo_root / "web_app" / "app.py"),
        "--server.headless=true",
        f"--server.port={port}",
    ]
    return stcli.main()


def _choose_port(candidates: list[int]) -> int:
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                is_in_use = sock.connect_ex(("127.0.0.1", port)) == 0
                if is_in_use:
                    continue
                return port
            except OSError:
                continue
    return candidates[0]


if __name__ == "__main__":
    raise SystemExit(main())
