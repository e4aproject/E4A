"""Shared fixtures for the E4A 1.0 conformance suite.

The normative artifacts (spec schema + test vectors) are located relative
to this file when run from a checkout; when the suite is run against an
installed artifact from elsewhere, set E4A_REPO_ROOT to the checkout path.
Only public implementation interfaces are imported here.
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(os.environ.get("E4A_REPO_ROOT", Path(__file__).resolve().parent.parent))
PROTOCOL_DIR = REPO_ROOT / "docs" / "protocol"
VECTORS_DIR = PROTOCOL_DIR / "test-vectors"
SCHEMA_PATH = PROTOCOL_DIR / "mandate.schema.json"


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def schema_vector_files():
    return sorted(p for p in VECTORS_DIR.glob("*.json") if p.name != "lifecycle-vectors.json")


def vector_mandate(filename):
    return load_json(VECTORS_DIR / filename)["mandate"]


@pytest.fixture()
def engine():
    """A fresh reference engine through the public API, in-memory store."""
    from e4a_sdk import InMemoryStore, MandateEngine

    return MandateEngine(store=InMemoryStore())


def state_of(record):
    """The lifecycle state as exposed on a public mandate record."""
    return record.get("status") or record.get("state")


def error_code(exc):
    """The stable error code carried by a public-API error."""
    return getattr(exc, "code", None)


def http_get(url, **kwargs):
    """GET against a local service, ignoring any ambient proxy config."""
    with httpx.Client(trust_env=False, timeout=kwargs.pop("timeout", 10)) as client:
        return client.get(url, **kwargs)


def http_post(url, **kwargs):
    """POST against a local service, ignoring any ambient proxy config."""
    with httpx.Client(trust_env=False, timeout=kwargs.pop("timeout", 10)) as client:
        return client.post(url, **kwargs)


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class RunningService:
    def __init__(self, proc, base_url):
        self.proc = proc
        self.base_url = base_url


def _service_pythonpath():
    """PYTHONPATH for the service subprocess.

    When the package is installed, the subprocess imports it unaided and
    this returns None. From a bare source checkout the service needs the
    checkout's package locations; detect that with a probe import.
    """
    probe = subprocess.run(
        [sys.executable, "-c", "import e4a_sdk, api.server"],
        capture_output=True,
        cwd=str(REPO_ROOT.parent),
    )
    if probe.returncode == 0:
        return None
    return os.pathsep.join([str(REPO_ROOT), str(REPO_ROOT / "sdk" / "python")])


_SERVICE_PYTHONPATH = _service_pythonpath()


def _launch_service(db_path, api_token=None):
    port = _free_port()
    env = dict(os.environ)
    env["E4A_DB_PATH"] = str(db_path)
    if _SERVICE_PYTHONPATH:
        env["PYTHONPATH"] = _SERVICE_PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    if api_token is not None:
        env["E4A_API_TOKEN"] = api_token
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.server:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if http_get(base_url + "/health", timeout=2).status_code == 200:
                return RunningService(proc, base_url)
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    proc.kill()
    raise RuntimeError("reference service did not become healthy in 30s")


@pytest.fixture()
def service(tmp_path):
    """A black-box reference service on a temporary database."""
    svc = _launch_service(tmp_path / "tck.db")
    yield svc
    svc.proc.terminate()
    svc.proc.wait(timeout=10)


@pytest.fixture()
def restartable_service(tmp_path):
    """Factory to (re)launch the service on the same database file."""

    running = []

    def launch(api_token=None):
        svc = _launch_service(tmp_path / "tck-restart.db", api_token=api_token)
        running.append(svc)
        return svc

    yield launch
    for svc in running:
        if svc.proc.poll() is None:
            svc.proc.terminate()
            svc.proc.wait(timeout=10)


def stop_service(svc):
    svc.proc.terminate()
    svc.proc.wait(timeout=10)
