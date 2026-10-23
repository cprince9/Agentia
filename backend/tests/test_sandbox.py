"""Unit and Integration tests for MASDS Sandbox Executor.

Tests:
- test_execute_simple_python: run a simple print('hello') and verify stdout
- test_execute_timeout: run sleep(999), verify timed_out=True
- test_execute_syntax_error: run invalid Python, verify exit_code != 0
- Docker availability check: skips or uses local container sandbox when Docker daemon is available
"""

import os
import sys
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Optional
import pytest


# ------------------------------------------------------------------------------
# Sandbox Execution Result & Executor Definition
# ------------------------------------------------------------------------------
@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_seconds: float


class SandboxExecutor:
    """Executes untrusted code within an isolated container or isolated subprocess."""

    def __init__(self, timeout_seconds: int = 10, use_docker: bool = False):
        self.timeout_seconds = timeout_seconds
        self.use_docker = use_docker

    def execute_python(self, code: str, timeout: Optional[int] = None) -> SandboxResult:
        timeout = timeout or self.timeout_seconds
        start_time = time.time()

        if self.use_docker:
            return self._execute_in_docker(code, timeout)
        else:
            return self._execute_in_subprocess(code, timeout)

    def _execute_in_subprocess(self, code: str, timeout: int) -> SandboxResult:
        start_time = time.time()
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name

        try:
            process = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.time() - start_time
            return SandboxResult(
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode,
                timed_out=False,
                duration_seconds=elapsed,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.time() - start_time
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return SandboxResult(
                stdout=stdout,
                stderr=stderr + "\nExecution timed out.",
                exit_code=124,
                timed_out=True,
                duration_seconds=elapsed,
            )
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _execute_in_docker(self, code: str, timeout: int) -> SandboxResult:
        import docker

        client = docker.from_env()
        start_time = time.time()

        container = None
        try:
            container = client.containers.run(
                "python:3.11-slim",
                command=["python", "-c", code],
                detach=True,
                mem_limit="256m",
                nano_cpus=1000000000,
                network_mode="none",
            )

            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)
                logs = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                err_logs = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
                elapsed = time.time() - start_time
                return SandboxResult(
                    stdout=logs,
                    stderr=err_logs,
                    exit_code=exit_code,
                    timed_out=False,
                    duration_seconds=elapsed,
                )
            except Exception:
                container.kill()
                elapsed = time.time() - start_time
                return SandboxResult(
                    stdout="",
                    stderr="Container execution timed out.",
                    exit_code=124,
                    timed_out=True,
                    duration_seconds=elapsed,
                )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass


def is_docker_available() -> bool:
    """Check if Docker daemon is responsive."""
    try:
        import docker
        client = docker.from_env()
        return client.ping()
    except Exception:
        return False


# ------------------------------------------------------------------------------
# Unit Tests
# ------------------------------------------------------------------------------
def test_execute_simple_python():
    """Verify executing a simple print('hello') captures stdout correctly and returns exit code 0."""
    executor = SandboxExecutor(timeout_seconds=5, use_docker=False)
    code = "print('hello')"

    result = executor.execute_python(code)

    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert result.timed_out is False
    assert result.duration_seconds < 5.0


def test_execute_timeout():
    """Verify executing a long sleep with short timeout marks timed_out=True."""
    executor = SandboxExecutor(timeout_seconds=1, use_docker=False)
    code = "import time\ntime.sleep(999)"

    result = executor.execute_python(code, timeout=1)

    assert result.timed_out is True
    assert result.exit_code != 0
    assert "timed out" in result.stderr.lower()


def test_execute_syntax_error():
    """Verify executing invalid Python results in a non-zero exit code and stderr captures the SyntaxError."""
    executor = SandboxExecutor(timeout_seconds=5, use_docker=False)
    code = "def broken_syntax(\n    print('missing closing parenthesis')"

    result = executor.execute_python(code)

    assert result.exit_code != 0
    assert result.timed_out is False
    assert "SyntaxError" in result.stderr


# ------------------------------------------------------------------------------
# Docker-Specific Sandbox Tests (Skipped if Docker daemon not active)
# ------------------------------------------------------------------------------
@pytest.mark.skipif(not is_docker_available(), reason="Docker daemon is not reachable in current environment")
def test_docker_sandbox_execution():
    """Verify execution inside an actual Docker container when Docker daemon is available."""
    executor = SandboxExecutor(timeout_seconds=10, use_docker=True)
    code = "import sys; sys.stdout.write('container-ok'); exit(0)"

    result = executor.execute_python(code)

    assert result.exit_code == 0
    assert "container-ok" in result.stdout
    assert result.timed_out is False
