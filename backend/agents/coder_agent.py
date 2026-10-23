import ast
import re
from typing import List, Optional, Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent
from ..graph.state import AgentState, CodeFile


class CoderAgent(BaseAgent):
    name = "coder"
    role = "Senior Software Engineer"

    async def run(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        project_plan = state.get("project_plan") or {}
        architecture = state.get("architecture") or {}
        modules = project_plan.get("modules", [])
        current_idx = state.get("current_module_index", 0)
        coder_attempt = state.get("coder_attempt", 0)
        existing_code_files = state.get("code_files", [])

        state["current_agent"] = self.name
        await self._emit(session_id, "AGENT_STARTED", {
            "agent": self.name,
            "module_index": current_idx,
            "coder_attempt": coder_attempt,
        })

        # Determine target module
        if current_idx >= len(modules):
            # All modules have been coded once; if this is a retry from tester/reviewer, work on failed files
            current_module = modules[-1] if modules else {"name": "Core Application", "tasks": []}
            is_fix_cycle = True
        else:
            current_module = modules[current_idx]
            is_fix_cycle = (coder_attempt > 0)

        module_name = current_module.get("name", f"Module {current_idx + 1}")
        await self._emit_thinking(
            session_id,
            f"Developing module '{module_name}' (Attempt {coder_attempt + 1})...",
        )

        # 1. Query RAG for best practices and coding patterns
        rag_context = ""
        if self.rag:
            rag_query = f"Implementation patterns and best practices for {module_name}"
            hits = await self.rag.query_multiple(rag_query, collections=["best_practices", "frameworks"], top_k=2)
            if hits:
                rag_snippets = [f"[{h.get('source')}]: {h.get('page_content')}" for h in hits]
                rag_context = "\n\nCoding Guidelines & Standards:\n" + "\n".join(rag_snippets)

        # 2. Existing codebase summary
        existing_summary = ""
        if existing_code_files:
            summaries = []
            for cf in existing_code_files[-10:]:  # Keep recent files context concise
                summaries.append(f"--- File: {cf.path} ---\n{cf.content[:1500]}\n...")
            existing_summary = "\n\nPreviously Implemented Files:\n" + "\n".join(summaries)

        # 3. Handle retry feedback (test errors or code review comments)
        feedback_context = ""
        test_results = state.get("test_results")
        review_result = state.get("review_result")

        if is_fix_cycle:
            feedbacks = []
            if test_results and not test_results.all_passed:
                feedbacks.append(f"TEST FAILURES ({test_results.failed} failed):")
                for err in test_results.errors:
                    feedbacks.append(f"- Test: {err.test_name}\n  Error: {err.error}\n  Traceback:\n{err.traceback}")
            if review_result and not review_result.approved:
                feedbacks.append(f"CODE REVIEW ISSUES (Score: {review_result.quality_score}/100):")
                for issue in review_result.issues:
                    if issue.severity in ("HIGH", "MEDIUM"):
                        feedbacks.append(f"- [{issue.severity}] {issue.file}:{issue.line} - {issue.issue}\n  Suggestion: {issue.suggestion}")

            if feedbacks:
                feedback_context = "\n\nCRITICAL ISSUES TO FIX IMMEDIATELY:\n" + "\n\n".join(feedbacks)
                await self._emit_thinking(session_id, f"Addressing {len(feedbacks)} failure/review reports...")

        # 4. Formulate Prompt
        user_prompt = f"""
Current Module Specification:
{json.dumps(current_module, indent=2)}

Full System Architecture:
{json.dumps(architecture, indent=2)}
{existing_summary}
{rag_context}
{feedback_context}

Instructions:
1. Implement all source code files required for this module according to the architecture.
2. If this is a fix attempt, resolve every reported test error or security issue.
3. Use the exact delimiter format for each file:
===FILE: path/to/file.py===
<complete, production-ready code with full implementations, types, and docstrings>
===END_FILE===

Do not truncate code. Do not output markdown text outside these delimiters.
"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        await self._emit_thinking(session_id, "Generating production code with GPT-4o...")
        response = await self._call_llm(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # 5. Parse files from delimiter format
        parsed_files = self._parse_code_files(content)
        if not parsed_files:
            # Fallback regex search if delimiters were slightly altered
            parsed_files = self._fallback_parse_files(content)

        if not parsed_files:
            self.logger.warning("no_files_parsed_from_coder_output")
            # Create a fallback module file if parsing failed
            fallback_filename = f"app/{current_module.get('id', 'module')}.py"
            parsed_files = [CodeFile(path=fallback_filename, content=content, language="python")]

        # 6. Validate Python syntax
        for cf in parsed_files:
            if cf.path.endswith(".py"):
                is_valid, err_msg = self._validate_python_syntax(cf.content)
                if not is_valid:
                    self.logger.warning("syntax_validation_warning", file=cf.path, error=err_msg)
                    # We can attempt a quick cleanup or proceed to let tester catch it

            # Update or append in state["code_files"]
            self._upsert_code_file(state["code_files"], cf)

            await self._emit(session_id, "FILE_CREATED", {
                "file_path": cf.path,
                "language": cf.language,
                "size_bytes": len(cf.content.encode("utf-8")),
            })
            await self._emit_thinking(session_id, f"Saved source file: {cf.path}")

        # If we just implemented this module on normal forward pass, advance module index
        if not is_fix_cycle and current_idx < len(modules):
            state["current_module_index"] = current_idx + 1

        state["pipeline_status"] = "coding_in_progress"

        await self._emit(session_id, "AGENT_COMPLETE", {
            "agent": self.name,
            "module_name": module_name,
            "files_count": len(parsed_files),
        })

        return state

    def _validate_python_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"

    def _parse_code_files(self, text: str) -> List[CodeFile]:
        pattern = r"===FILE:\s*([^\n\r]+)===\s*\n([\s\S]*?)\s*===END_FILE==="
        matches = re.findall(pattern, text)
        files = []
        for file_path, code in matches:
            clean_path = file_path.strip().replace("\\", "/")
            ext = clean_path.split(".")[-1].lower() if "." in clean_path else "python"
            lang = "python" if ext in ("py", "pyw") else ext
            files.append(CodeFile(path=clean_path, content=code.strip(), language=lang))
        return files

    def _fallback_parse_files(self, text: str) -> List[CodeFile]:
        """Attempt extracting markdown code blocks with file path hints."""
        pattern = r"```(?:python|py)?\s*(?:#|//)?\s*(?:file:)?\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        files = []
        for file_path, code in matches:
            clean_path = file_path.strip().replace("\\", "/")
            files.append(CodeFile(path=clean_path, content=code.strip(), language="python"))
        return files

    def _upsert_code_file(self, file_list: List[CodeFile], new_file: CodeFile) -> None:
        for idx, existing in enumerate(file_list):
            if existing.path == new_file.path:
                file_list[idx] = new_file
                return
        file_list.append(new_file)
