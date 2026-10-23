import json
import re
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent
from ..graph.state import AgentState, ReviewResult, ReviewIssue


class ReviewIssueModel(BaseModel):
    severity: str = Field(description="HIGH | MEDIUM | LOW")
    type: str = Field(description="Security | Performance | Architecture | CodeQuality | Bug")
    file: str = Field(description="Path of affected file")
    line: int = Field(default=1, description="Line number")
    issue: str = Field(description="Description of identified issue")
    suggestion: str = Field(description="Actionable fix suggestion")
    rag_source: str = Field(default="", description="Citation or security guideline reference")


class ReviewResultModel(BaseModel):
    issues: List[ReviewIssueModel] = Field(default_factory=list)
    quality_score: int = Field(description="Quality score between 0 and 100")
    approved: bool = Field(description="True only if zero HIGH issues and score >= 80")
    review_summary: str = Field(description="Markdown executive summary")


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    role = "Staff Software Engineer & Security Lead"

    async def run(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        code_files = state.get("code_files", [])
        state["current_agent"] = self.name
        review_cycle = state.get("review_cycle", 0)

        await self._emit(session_id, "AGENT_STARTED", {
            "agent": self.name,
            "review_cycle": review_cycle,
        })
        await self._emit_thinking(session_id, f"Beginning architectural & security review (Cycle {review_cycle + 1})...")

        # 1. Query RAG for security standards and best practices
        rag_context = ""
        rag_sources = []
        if self.rag:
            await self._emit_thinking(session_id, "Querying RAG for OWASP security and performance best practices...")
            hits = await self.rag.query_multiple(
                query_text="Security vulnerabilities OWASP Top 10 SQL injection input validation authentication",
                collections=["security", "best_practices"],
                top_k=3,
            )
            if hits:
                snippets = []
                for h in hits:
                    src = h.get("source", "Security Standard")
                    rag_sources.append(src)
                    snippets.append(f"[{src}]: {h.get('page_content')}")
                rag_context = "\n\nRAG Security & Best Practice Guidelines:\n" + "\n".join(snippets)

        # 2. Prepare code for inspection
        code_snippets = []
        for cf in code_files:
            # Provide numbered lines for accurate line references
            lines = cf.content.split("\n")
            numbered_content = "\n".join(f"{idx + 1:4d} | {line}" for idx, line in enumerate(lines))
            code_snippets.append(f"=== File: {cf.path} ===\n{numbered_content}")

        code_block = "\n\n".join(code_snippets)
        user_prompt = f"""
Codebase to Review:
{code_block}
{rag_context}

Perform a rigorous code and security review:
1. Identify any HIGH (security/crash), MEDIUM (performance/maintainability), or LOW (style) issues.
2. Cite the relevant RAG source or industry guideline where applicable.
3. Compute an overall quality_score (0-100).
4. approved MUST BE FALSE if any HIGH issues are found.

Output ONLY valid JSON conforming strictly to the ReviewResult schema.
"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        await self._emit_thinking(session_id, "Evaluating static analysis, input sanitization, and typing safety...")

        try:
            try:
                res_obj = await self._call_llm(messages, structured_output_schema=ReviewResultModel)
                if isinstance(res_obj, ReviewResultModel):
                    review_dict = res_obj.model_dump()
                elif isinstance(res_obj, dict):
                    review_dict = res_obj
                else:
                    raise ValueError(f"Unexpected review output type: {type(res_obj)}")
            except Exception as struct_err:
                self.logger.warning("reviewer_structured_fallback", error=str(struct_err))
                response = await self._call_llm(messages)
                content = response.content if hasattr(response, "content") else str(response)
                json_str = self._clean_json(content)
                parsed = json.loads(json_str)
                validated = ReviewResultModel(**parsed)
                review_dict = validated.model_dump()

            # Enforce business logic on approval
            raw_issues = review_dict.get("issues", [])
            has_high_issue = any(i.get("severity", "").upper() == "HIGH" for i in raw_issues)
            quality_score = review_dict.get("quality_score", 70)

            approved = (not has_high_issue) and (quality_score >= 80)

            # Convert to dataclasses
            parsed_issues = [
                ReviewIssue(
                    severity=i.get("severity", "LOW"),
                    type=i.get("type", "CodeQuality"),
                    file=i.get("file", ""),
                    line=int(i.get("line", 1)),
                    issue=i.get("issue", ""),
                    suggestion=i.get("suggestion", ""),
                    rag_source=i.get("rag_source", ""),
                )
                for i in raw_issues
            ]

            result_dataclass = ReviewResult(
                issues=parsed_issues,
                quality_score=quality_score,
                approved=approved,
                review_summary=review_dict.get("review_summary", "Review complete."),
            )

            state["review_result"] = result_dataclass
            state["review_cycle"] = review_cycle + 1

            # Emit events for each high issue
            for issue in parsed_issues:
                if issue.severity.upper() == "HIGH":
                    await self._emit(session_id, "REVIEW_ISSUE", {
                        "severity": issue.severity,
                        "file": issue.file,
                        "line": issue.line,
                        "issue": issue.issue,
                        "suggestion": issue.suggestion,
                    })

            await self._emit_thinking(
                session_id,
                f"Review finished. Score: {quality_score}/100. Approved: {approved}. Identified {len(parsed_issues)} issues.",
            )

            await self._emit(session_id, "AGENT_COMPLETE", {
                "agent": self.name,
                "approved": approved,
                "quality_score": quality_score,
                "issues_count": len(parsed_issues),
            })

            return state

        except Exception as e:
            self.logger.error("reviewer_agent_failed", error=str(e))
            state["error_log"].append(f"Reviewer error: {str(e)}")
            state["pipeline_status"] = "failed"
            await self._emit(session_id, "AGENT_FAILED", {"agent": self.name, "error": str(e)})
            raise

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            return text[first_brace : last_brace + 1]
        return text
