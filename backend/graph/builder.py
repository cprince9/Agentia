from typing import Optional, Any
from langgraph.graph import StateGraph, END

from .state import AgentState
from .edges import route_after_tester, route_after_reviewer, route_after_coder
from ..agents import (
    PlannerAgent,
    ArchitectAgent,
    CoderAgent,
    TesterAgent,
    ReviewerAgent,
    DevOpsAgent,
)
from ..config.settings import Settings, get_settings
from ..services.event_bus import EventBus
from ..rag.retriever import RAGRetriever
from ..sandbox.executor import SandboxExecutor


async def fail_node(state: AgentState) -> AgentState:
    """Terminal node entered when pipeline retries are exhausted or fatal error occurs."""
    state["pipeline_status"] = "failed"
    state["current_agent"] = "system"
    return state


def build_pipeline(
    settings: Optional[Settings] = None,
    event_bus: Optional[EventBus] = None,
    rag_retriever: Optional[RAGRetriever] = None,
    sandbox_executor: Optional[SandboxExecutor] = None,
) -> Any:
    """
    Construct, wire, and compile the full MASDS LangGraph workflow.
    """
    settings = settings or get_settings()
    rag = rag_retriever or RAGRetriever()
    sandbox = sandbox_executor or SandboxExecutor(settings)

    # 1. Instantiate agents
    planner = PlannerAgent(settings=settings, event_bus=event_bus, rag_retriever=rag)
    architect = ArchitectAgent(settings=settings, event_bus=event_bus, rag_retriever=rag)
    coder = CoderAgent(settings=settings, event_bus=event_bus, rag_retriever=rag)
    tester = TesterAgent(settings=settings, event_bus=event_bus, rag_retriever=rag, sandbox_executor=sandbox)
    reviewer = ReviewerAgent(settings=settings, event_bus=event_bus, rag_retriever=rag)
    devops = DevOpsAgent(settings=settings, event_bus=event_bus, rag_retriever=rag, sandbox_executor=sandbox)

    # 2. Build StateGraph
    workflow = StateGraph(AgentState)

    # 3. Add Nodes
    workflow.add_node("planner", planner.run)
    workflow.add_node("architect", architect.run)
    workflow.add_node("coder", coder.run)
    workflow.add_node("tester", tester.run)
    workflow.add_node("reviewer", reviewer.run)
    workflow.add_node("devops", devops.run)
    workflow.add_node("fail", fail_node)

    # 4. Set entry point and static edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "architect")
    workflow.add_edge("architect", "coder")

    # 5. Conditional edges
    workflow.add_conditional_edges(
        "coder",
        route_after_coder,
        {
            "coder": "coder",
            "tester": "tester",
            "reviewer": "reviewer",
        },
    )

    workflow.add_conditional_edges(
        "tester",
        route_after_tester,
        {
            "reviewer": "reviewer",
            "coder": "coder",
            "fail": "fail",
        },
    )

    workflow.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "devops": "devops",
            "coder": "coder",
        },
    )

    # Terminal edges
    workflow.add_edge("devops", END)
    workflow.add_edge("fail", END)

    # 6. Compile
    return workflow.compile()
