import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Any, Dict, Type
import structlog
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from ..config.settings import Settings, get_settings
from ..services.event_bus import EventBus
from ..services.llm_router import get_llm_for_agent, call_with_fallback, AGENT_TIER_MAPPING
from ..rag.retriever import RAGRetriever
from ..graph.state import AgentState, AgentMessageLog


class BaseAgent(ABC):
    """Abstract base class for all autonomous engineering agents in MASDS."""

    name: str = "base"
    role: str = "Engineering Agent"

    def __init__(
        self,
        settings: Optional[Settings] = None,
        event_bus: Optional[EventBus] = None,
        rag_retriever: Optional[RAGRetriever] = None,
    ):
        self.settings = settings or get_settings()
        self.event_bus = event_bus
        self.rag = rag_retriever
        self.logger = structlog.get_logger(agent=self.name)
        self.system_prompt: str = ""
        self._load_system_prompt()

    def _load_system_prompt(self) -> None:
        """Load corresponding prompt template from config/prompts/{name}.txt."""
        base_dir = Path(__file__).resolve().parent.parent
        prompt_file = base_dir / "config" / "prompts" / f"{self.name}.txt"

        if prompt_file.exists():
            self.system_prompt = prompt_file.read_text(encoding="utf-8").strip()
            self.logger.debug("system_prompt_loaded", file=str(prompt_file))
        else:
            self.system_prompt = f"You are a helpful {self.role} in a software development team."
            self.logger.warning("prompt_file_not_found_using_default", file=str(prompt_file))

    async def _emit(
        self,
        session_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish an event to the session event bus."""
        if self.event_bus:
            await self.event_bus.publish(
                session_id=session_id,
                event_type=event_type,
                agent_name=self.name,
                payload=payload or {},
            )
        self.logger.info("agent_event_emitted", session_id=session_id, event_type=event_type)

    async def _emit_thinking(self, session_id: str, message: str) -> None:
        """Emit real-time reasoning/status updates for UI visibility."""
        await self._emit(session_id, "AGENT_THINKING", {"message": message})

    async def _call_llm(
        self,
        messages: List[BaseMessage],
        structured_output_schema: Optional[Type[Any]] = None,
    ) -> Any:
        """Invoke LLM with tiered retries and fallback."""
        primary_tier = AGENT_TIER_MAPPING.get(self.name.lower(), "balanced")
        return await call_with_fallback(
            messages=messages,
            primary_tier=primary_tier,
            max_retries=3,
            structured_output_schema=structured_output_schema,
        )

    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        """Execute agent workflow step and return modified AgentState."""
        pass
