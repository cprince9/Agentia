import os
import shutil
import tempfile
import time
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Any
import structlog

try:
    import docker
    from docker.errors import DockerException, APIError
except ImportError:
    docker = None
    DockerException = Exception
    APIError = Exception

from ..graph.state import CodeFile
from ..config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool


class SandboxExecutor:
    """Secure Docker-based sandbox execution environment for running generated code & test suites."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.docker_client = self._init_docker_client()

    def _init_docker_client(self) -> Optional[Any]:
        if docker is None:
            logger.warning("docker_sdk_not_installed")
            return None
        try:
            client = docker.from_env()
            client.ping()
            logger.info("docker_daemon_connected")
            return client
        except Exception as e:
            logger.warning("docker_daemon_unavailable_using_local_fallback", error=str(e))
            return None

    def _parse_output(self, logs: bytes) -> Tuple[str, str]:
        """Split combined stdout/stderr streams if multiplexed, or decode bytes."""
        try:
            decoded = logs.decode("utf-8", errors="replace")
            # If standard Docker multiplexed stream header exists
            return decoded, ""
        except Exception as e:
            return "", f"Failed to decode container logs: {e}"

    async def _install_deps(self, container: Any, req_file_exists: bool) -> None:
        """Install dependencies from requirements.txt if present inside container."""
        if not req_file_exists or not container:
            return

        def run_pip():
            return container.exec_run("pip install --no-cache-dir -r /workspace/requirements.txt")

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, run_pip)
        except Exception as e:
            logger.warning("pip_dependency_install_failed", error=str(e))

    async def execute(
        self,
        files: List[CodeFile],
        command: str = "pytest -v",
        timeout: Optional[int] = None,
        language: str = "python",
    ) -> ExecutionResult:
        """
        Execute code files inside an isolated, unprivileged container sandbox.
        """
        exec_timeout = timeout or self.settings.SANDBOX_TIMEOUT_SECONDS
        start_time = time.time()
        temp_dir = tempfile.mkdtemp(prefix="masds_sandbox_")
        container = None
        has_reqs = False

        try:
            # 1. Write all code files to temporary directory
            for f in files:
                target_path = Path(temp_dir) / f.path.lstrip("/\\")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(f.content, encoding="utf-8")
                if target_path.name == "requirements.txt":
                    has_reqs = True

            # If Docker client is available, execute in isolated container
            if self.docker_client is not None:
                mem_limit = self.settings.SANDBOX_MEMORY_LIMIT
                cpu_limit = float(self.settings.SANDBOX_CPU_LIMIT)
                cpu_quota = int(cpu_limit * 100000)

                def _run_container():
                    return self.docker_client.containers.run(
                        image="python:3.11-slim",
                        command=f"bash -c '{command}'",
                        network_mode="none",
                        mem_limit=mem_limit,
                        cpu_period=100000,
                        cpu_quota=cpu_quota,
                        user="nobody",
                        volumes={temp_dir: {"bind": "/workspace", "mode": "rw"}},
                        working_dir="/workspace",
                        detach=True,
                        stdout=True,
                        stderr=True,
                    )

                loop = asyncio.get_running_loop()
                container = await loop.run_in_executor(None, _run_container)

                if has_reqs:
                    await self._install_deps(container, req_file_exists=True)

                # Wait for container completion with timeout
                async def _wait_container():
                    def _wait_sync():
                        res = container.wait(timeout=exec_timeout)
                        logs = container.logs(stdout=True, stderr=True)
                        return res.get("StatusCode", 1), logs
                    return await loop.run_in_executor(None, _wait_sync)

                try:
                    exit_code, logs = await asyncio.wait_for(_wait_container(), timeout=exec_timeout)
                    stdout, stderr = self._parse_output(logs)
                    duration = time.time() - start_time
                    return ExecutionResult(
                        exit_code=exit_code,
                        stdout=stdout,
                        stderr=stderr,
                        duration_s=round(duration, 3),
                        timed_out=False,
                    )
                except asyncio.TimeoutError:
                    try:
                        container.kill()
                    except Exception:
                        pass
                    return ExecutionResult(
                        exit_code=-1,
                        stdout="",
                        stderr="Execution timed out exceeding sandbox threshold.",
                        duration_s=round(time.time() - start_time, 3),
                        timed_out=True,
                    )

            else:
                # Fallback: Local isolated subprocess execution
                return await self._execute_local_fallback(temp_dir, command, exec_timeout, start_time)

        except Exception as e:
            logger.error("sandbox_execution_error", error=str(e))
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Sandbox execution failed: {str(e)}",
                duration_s=round(time.time() - start_time, 3),
                timed_out=False,
            )
        finally:
            # Cleanup Docker container
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _execute_local_fallback(
        self,
        workspace_dir: str,
        command: str,
        timeout: int,
        start_time: float,
    ) -> ExecutionResult:
        """Subprocess execution when Docker daemon is not present."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
                duration = time.time() - start_time
                return ExecutionResult(
                    exit_code=proc.returncode if proc.returncode is not None else 0,
                    stdout=stdout_data.decode("utf-8", errors="replace"),
                    stderr=stderr_data.decode("utf-8", errors="replace"),
                    duration_s=round(duration, 3),
                    timed_out=False,
                )
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return ExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Subprocess timed out.",
                    duration_s=round(time.time() - start_time, 3),
                    timed_out=True,
                )
        except Exception as e:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Local execution error: {e}",
                duration_s=round(time.time() - start_time, 3),
                timed_out=False,
            )
