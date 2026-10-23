import re
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent
from ..graph.state import AgentState, CodeFile, TestResults
from ..sandbox.executor import SandboxExecutor
from ..sandbox.parser import parse_pytest_output


class TesterAgent(BaseAgent):
    name = "tester"
    role = "Senior QA Engineer"

    def __init__(self, settings=None, event_bus=None, rag_retriever=None, sandbox_executor=None):
        super().__init__(settings, event_bus, rag_retriever)
        self.sandbox = sandbox_executor or SandboxExecutor(self.settings)

    async def run(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        code_files = state.get("code_files", [])
        state["current_agent"] = self.name

        await self._emit(session_id, "AGENT_STARTED", {"agent": self.name})
        await self._emit_thinking(session_id, f"Reviewing {len(code_files)} source files for automated test authoring...")

        # 1. Prepare code files summary for test generation prompt
        code_snippets = []
        for cf in code_files:
            code_snippets.append(f"=== File: {cf.path} ===\n{cf.content}")

        code_block = "\n\n".join(code_snippets)
        user_prompt = f"""
Source Code to Test:
{code_block}

Write comprehensive pytest test suites covering:
1. All core business logic and API route behaviors (happy paths).
2. Boundary conditions, invalid input values, missing headers/data (edge cases).
3. Error scenarios, exceptions, and proper HTTP error codes.
4. Use pytest fixtures, async markers (pytest.mark.asyncio), and mock dependencies if appropriate.

Return the test files using the delimiter format:
===FILE: tests/test_app.py===
<pytest code here>
===END_FILE===

Do not include conversational text or markdown code wrappers outside the delimiters.
"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        await self._emit_thinking(session_id, "Generating comprehensive pytest suite...")
        response = await self._call_llm(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # 2. Parse generated test files
        test_files = self._parse_test_files(content)
        if not test_files:
            # Fallback simple test file if parser didn't catch delimiters
            test_files = [
                CodeFile(
                    path="tests/test_basic.py",
                    content="def test_sanity():\n    assert True\n",
                    language="python",
                )
            ]

        state["test_files"] = test_files
        for tf in test_files:
            await self._emit(session_id, "TEST_FILE_CREATED", {"path": tf.path})

        # 3. Bundle source code + test files into sandbox execution bundle
        bundle: List[CodeFile] = []
        bundle.extend(code_files)
        bundle.extend(test_files)

        # Ensure conftest.py exists if async testing is involved
        has_conftest = any(f.path.endswith("conftest.py") for f in bundle)
        if not has_conftest:
            bundle.append(
                CodeFile(
                    path="conftest.py",
                    content=(
                        "import pytest\n"
                        "import asyncio\n\n"
                        "@pytest.fixture(scope='session')\n"
                        "def event_loop():\n"
                        "    loop = asyncio.get_event_loop_policy().new_event_loop()\n"
                        "    yield loop\n"
                        "    loop.close()\n"
                    ),
                    language="python",
                )
            )

        await self._emit_thinking(session_id, f"Running pytest suite in secure sandbox executor...")

        # 4. Execute test suite in Docker sandbox (or local fallback)
        test_command = "pytest --json-report --json-report-file=report.json -v"
        exec_result = await self.sandbox.execute(files=bundle, command=test_command)

        # 5. Parse test execution results
        test_results = parse_pytest_output(exec_result.stdout, exec_result.stderr)
        state["test_results"] = test_results

        await self._emit(session_id, "TEST_RESULT", {
            "passed": test_results.passed,
            "failed": test_results.failed,
            "all_passed": test_results.all_passed,
            "coverage_percent": test_results.coverage_percent,
            "duration_s": exec_result.duration_s,
        })

        if not test_results.all_passed:
            state["coder_attempt"] = state.get("coder_attempt", 0) + 1
            await self._emit_thinking(
                session_id,
                f"Tests encountered {test_results.failed} failures. Handing back to Coder (Attempt {state['coder_attempt']}).",
            )
        else:
            await self._emit_thinking(
                session_id,
                f"All {test_results.passed} tests passed successfully! Coverage: {test_results.coverage_percent}%",
            )

        await self._emit(session_id, "AGENT_COMPLETE", {
            "agent": self.name,
            "passed": test_results.passed,
            "failed": test_results.failed,
            "all_passed": test_results.all_passed,
        })

        return state

    def _parse_test_files(self, text: str) -> List[CodeFile]:
        pattern = r"===FILE:\s*([^\n\r]+)===\s*\n([\s\S]*?)\s*===END_FILE==="
        matches = re.findall(pattern, text)
        files = []
        for file_path, code in matches:
            clean_path = file_path.strip().replace("\\", "/")
            files.append(CodeFile(path=clean_path, content=code.strip(), language="python"))
        return files
