import json
import re
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent
from ..graph.state import AgentState


class ModulePlan(BaseModel):
    id: str = Field(description="Unique module identifier, e.g. module_1")
    name: str = Field(description="Descriptive module name")
    priority: int = Field(default=1, description="Execution priority")
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent modules")
    estimated_complexity: str = Field(default="MEDIUM", description="LOW, MEDIUM, or HIGH")
    tasks: List[str] = Field(default_factory=list, description="List of specific implementation tasks")


class MilestonePlan(BaseModel):
    id: str = Field(description="Milestone ID, e.g. milestone_1")
    name: str = Field(description="Milestone title")
    target_modules: List[str] = Field(default_factory=list, description="Module IDs included")
    description: str = Field(description="Acceptance criteria and deliverables")


class ProjectPlanSchema(BaseModel):
    project_name: str = Field(description="Kebab or snake case project name")
    description: str = Field(description="Executive and architectural summary")
    tech_stack: List[str] = Field(description="Selected technologies, libraries, and tools")
    modules: List[ModulePlan] = Field(description="Ordered list of decoupled system modules")
    milestones: List[MilestonePlan] = Field(description="Key progress milestones")


class PlannerAgent(BaseAgent):
    name = "planner"
    role = "Senior Engineering Manager"

    async def run(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        requirement = state["requirement"]
        state["current_agent"] = self.name

        await self._emit(session_id, "AGENT_STARTED", {"agent": self.name})
        await self._emit_thinking(session_id, "Analyzing requirements and domain boundaries...")

        # Formulate prompt
        user_prompt = f"""
Requirement Specification:
{requirement}

Analyze the above system requirement. Break it down into clean, decoupled, sequential modules.
Define the tech stack, dependency ordering, and milestones.
Produce the ProjectPlan in valid JSON adhering strictly to the schema.
"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        await self._emit_thinking(session_id, "Synthesizing project plan and technical dependency graph...")

        try:
            # Attempt structured output invocation
            try:
                plan_obj = await self._call_llm(messages, structured_output_schema=ProjectPlanSchema)
                if isinstance(plan_obj, ProjectPlanSchema):
                    plan_dict = plan_obj.model_dump()
                elif isinstance(plan_obj, dict):
                    plan_dict = plan_obj
                else:
                    raise ValueError(f"Unexpected output type: {type(plan_obj)}")
            except Exception as struct_err:
                self.logger.warning("structured_output_fallback", error=str(struct_err))
                # Fallback to direct raw output
                raw_response = await self._call_llm(messages)
                content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
                json_str = self._clean_json(content)
                parsed = json.loads(json_str)
                validated = ProjectPlanSchema(**parsed)
                plan_dict = validated.model_dump()

            await self._emit_thinking(
                session_id,
                f"Generated plan for '{plan_dict.get('project_name', 'project')}' with {len(plan_dict.get('modules', []))} modules.",
            )

            state["project_plan"] = plan_dict
            state["current_module_index"] = 0
            state["pipeline_status"] = "planning_completed"

            await self._emit(session_id, "AGENT_COMPLETE", {
                "agent": self.name,
                "project_plan": plan_dict,
            })

            return state

        except Exception as e:
            self.logger.error("planner_agent_failed", error=str(e))
            state["error_log"].append(f"Planner error: {str(e)}")
            state["pipeline_status"] = "failed"
            await self._emit(session_id, "AGENT_FAILED", {"agent": self.name, "error": str(e)})
            raise

    def _clean_json(self, text: str) -> str:
        """Strip markdown code delimiters and extract valid JSON."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            return text[first_brace : last_brace + 1]
        return text
