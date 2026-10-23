from .state import AgentState
from ..config.settings import get_settings


def route_after_coder(state: AgentState) -> str:
    """
    Decide whether to code the next module or proceed to testing.
    If all modules in project_plan are coded, route to tester.
    """
    project_plan = state.get("project_plan") or {}
    modules = project_plan.get("modules", [])
    current_idx = state.get("current_module_index", 0)
    coder_attempt = state.get("coder_attempt", 0)

    # If this was a retry run from tester or reviewer, always go back to verify
    if coder_attempt > 0 and state.get("test_results") is not None and not state["test_results"].all_passed:
        return "tester"

    if state.get("review_result") is not None and not state["review_result"].approved:
        return "reviewer"

    # Forward module progression
    if current_idx < len(modules):
        return "coder"
    else:
        return "tester"


def route_after_tester(state: AgentState) -> str:
    """
    Evaluate test results:
    - If all passed -> route to 'reviewer'
    - If failed and coder_attempt < MAX_CODER_RETRIES -> route back to 'coder'
    - If failed and retries exhausted -> route to 'fail'
    """
    settings = get_settings()
    max_retries = settings.MAX_CODER_RETRIES
    test_results = state.get("test_results")
    coder_attempt = state.get("coder_attempt", 0)

    if test_results and test_results.all_passed:
        return "reviewer"

    if coder_attempt <= max_retries:
        return "coder"

    # Retries exhausted
    return "fail"


def route_after_reviewer(state: AgentState) -> str:
    """
    Evaluate review results:
    - If approved -> route to 'devops'
    - If unapproved and review_cycle < MAX_REVIEWER_CYCLES -> route back to 'coder'
    - If max review cycles exceeded -> route to 'devops' (force approve with warning)
    """
    settings = get_settings()
    max_cycles = settings.MAX_REVIEWER_CYCLES
    review_result = state.get("review_result")
    review_cycle = state.get("review_cycle", 0)

    if review_result and review_result.approved:
        return "devops"

    if review_cycle < max_cycles:
        return "coder"

    # Max cycles reached: proceed to devops to deliver working state with review annotations
    return "devops"
