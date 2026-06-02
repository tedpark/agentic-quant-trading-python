from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from agentic_quant.serving.model_registry import build_checkpoint


ROOT = Path(__file__).resolve().parents[2]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body)


@pytest.fixture
def live_server() -> Generator[str]:
    port = free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "agentic_quant.serving.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"

    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise RuntimeError(f"uvicorn exited early: {stderr}")
            try:
                status, body = request_json("GET", f"{base_url}/health")
                if status == 200 and body.get("status") == "ok":
                    break
            except (OSError, urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        else:
            raise RuntimeError("uvicorn did not become ready within 10 seconds")

        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_live_server_predict_reload_and_health(live_server: str, tmp_path: Path) -> None:
    health_status, health = request_json("GET", f"{live_server}/health")
    assert health_status == 200
    assert health["status"] == "ok"
    assert health["model_version"] == "demo-v1"

    predict_status, prediction = request_json(
        "POST",
        f"{live_server}/predict",
        {"features": [0.1, 0.2, 0.3]},
    )
    assert predict_status == 200
    assert prediction["model_version"] == "demo-v1"
    assert isinstance(prediction["prediction"], float)

    missing_status, _ = request_json(
        "POST",
        f"{live_server}/reload",
        {"checkpoint_path": str(tmp_path / "missing.pt")},
    )
    assert missing_status == 400

    current_status, current = request_json(
        "POST",
        f"{live_server}/predict",
        {"features": [0.1, 0.2, 0.3]},
    )
    assert current_status == 200
    assert current["model_version"] == "demo-v1"

    checkpoint = tmp_path / "demo-v2.pt"
    build_checkpoint(checkpoint, model_version="demo-v2", input_dim=3)

    reload_status, reload_body = request_json(
        "POST",
        f"{live_server}/reload",
        {"checkpoint_path": str(checkpoint)},
    )
    assert reload_status == 200
    assert reload_body["model_version"] == "demo-v2"
    assert reload_body["input_dim"] == 3

    reloaded_status, reloaded = request_json(
        "POST",
        f"{live_server}/predict",
        {"features": [0.1, 0.2, 0.3]},
    )
    assert reloaded_status == 200
    assert reloaded["model_version"] == "demo-v2"

    wrong_dim_status, wrong_dim = request_json(
        "POST",
        f"{live_server}/predict",
        {"features": [0.1, 0.2]},
    )
    assert wrong_dim_status == 422
    assert "expected 3 features" in wrong_dim["detail"]
