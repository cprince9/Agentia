import json
import re
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent
from ..graph.state import AgentState


class ApiEndpoint(BaseModel):
    method: str = Field(description="HTTP method: GET, POST, PUT, DELETE, PATCH")
    path: str = Field(description="URL path")
    description: str = Field(description="Endpoint functionality")
    request_body: Optional[Dict[str, Any]] = Field(default=None)
    response_schema: Optional[Dict[str, Any]] = Field(default=None)


class ColumnDef(BaseModel):
    name: str
    type: str
    constraints: List[str] = Field(default_factory=list)
    nullable: bool = True


class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnDef]
    indexes: List[str] = Field(default_factory=list)


class ModuleContract(BaseModel):
    provider_module: str
    consumer_module: str
    interface_name: str
    contract_definition: str


class DesignDecision(BaseModel):
    decision: str
    rationale: str
    tradeoffs: str


class ArchitectureSchema(BaseModel):
    directory_structure: Dict[str, Any]
    api_endpoints: List[ApiEndpoint]
    db_schema: List[TableSchema]
    inter_module_contracts: List[ModuleContract]
    design_decisions: List[DesignDecision]


class ArchitectAgent(BaseAgent):
    name = "architect"
    role = "Principal Software Architect"

    async def run(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        project_plan = state.get("project_plan") or {}
        state["current_agent"] = self.name

        await self._emit(session_id, "AGENT_STARTED", {"agent": self.name})
        await self._emit_thinking(session_id, "Reviewing project plan and engineering constraints...")

        # 1. Query RAG for architectural patterns & framework recommendations
        tech_stack = ", ".join(project_plan.get("tech_stack", ["Python", "FastAPI"]))
        rag_query = f"Architecture patterns and best practices for {tech_stack}"
        rag_context = ""
        rag_sources = []

        if self.rag:
            await self._emit_thinking(session_id, f"Querying RAG knowledge base for '{tech_stack}' design patterns...")
            hits = await self.rag.query_multiple(rag_query, collections=["patterns", "frameworks"], top_k=2)
            if hits:
                rag_snippets = []
                for hit in hits:
                    source = hit.get("source", "Knowledge Base")
                    rag_sources.append(source)
                    rag_snippets.append(f"[{source}]: {hit.get('page_content')}")
                rag_context = "\n\nRetrieved Architectural Best Practices:\n" + "\n".join(rag_snippets)

        await self._emit(session_id, "RAG_RETRIEVAL_COMPLETE", {
            "query": rag_query,
            "sources": rag_sources,
        })

        # 2. Build Prompt
        user_prompt = f"""
Project Plan:
{json.dumps(project_plan, indent=2)}
{rag_context}

Design the complete system architecture based on the ProjectPlan above.
Specify the directory structure, REST API endpoints, database schemas with column types,
contracts between modules, and key design decisions with trade-offs.
Output ONLY valid JSON conforming strictly to the Architecture schema.
"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        await self._emit_thinking(session_id, "Synthesizing API contracts, data models, and directory tree...")

        try:
            try:
                arch_obj = await self._call_llm(messages, structured_output_schema=ArchitectureSchema)
                if isinstance(arch_obj, ArchitectureSchema):
                    arch_dict = arch_obj.model_dump()
                elif isinstance(arch_obj, dict):
                    arch_dict = arch_obj
                else:
                    raise ValueError(f"Unexpected arch output: {type(arch_obj)}")
            except Exception as struct_err:
                self.logger.warning("architect_structured_output_fallback", error=str(struct_err))
                raw_response = await self._call_llm(messages)
                content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
                json_str = self._clean_json(content)
                parsed = json.loads(json_str)
                validated = ArchitectureSchema(**parsed)
                arch_dict = validated.model_dump()

            state["architecture"] = arch_dict
            state["pipeline_status"] = "architecture_completed"

            await self._emit_thinking(
                session_id,
                f"Designed {len(arch_dict.get('api_endpoints', []))} API endpoints and {len(arch_dict.get('db_schema', []))} database tables.",
            )

            await self._emit(session_id, "AGENT_COMPLETE", {
                "agent": self.name,
                "architecture": arch_dict,
                "rag_sources": rag_sources,
            })

            return state

        except Exception as e:
            self.logger.error("architect_agent_failed", error=str(e))
            state["error_log"].append(f"Architect error: {str(e)}")
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
