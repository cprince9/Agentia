from typing import TypedDict, Optional, List, Literal, Any, Dict
from dataclasses import dataclass, field, asdict


@dataclass
class CodeFile:
    path: str
    content: str
    language: str = "python"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass  
class AgentMessageLog:
    from_agent: str
    to_agent: str
    message: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestError:
    test_name: str
    error: str
    traceback: str
    file: str
    line: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestResults:
    passed: int
    failed: int
    errors: List[TestError]
    coverage_percent: float
    all_passed: bool
    raw_output: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "errors": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.errors],
            "coverage_percent": self.coverage_percent,
            "all_passed": self.all_passed,
            "raw_output": self.raw_output,
        }


@dataclass
class ReviewIssue:
    severity: str  # HIGH | MEDIUM | LOW
    type: str
    file: str
    line: int
    issue: str
    suggestion: str
    rag_source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewResult:
    issues: List[ReviewIssue]
    quality_score: int
    approved: bool
    review_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issues": [i.to_dict() if hasattr(i, "to_dict") else i for i in self.issues],
            "quality_score": self.quality_score,
            "approved": self.approved,
            "review_summary": self.review_summary,
        }


class AgentState(TypedDict):
    session_id: str
    requirement: str
    project_plan: Optional[dict]
    architecture: Optional[dict]
    code_files: List[CodeFile]
    current_module_index: int
    coder_attempt: int
    test_files: List[CodeFile]
    test_results: Optional[TestResults]
    review_result: Optional[ReviewResult]
    review_cycle: int
    devops_artifacts: List[CodeFile]
    staging_url: Optional[str]
    pipeline_status: str
    error_log: List[str]
    agent_messages: List[AgentMessageLog]
    current_agent: str
