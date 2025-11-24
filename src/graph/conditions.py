"""Conditional routing logic for workflow"""
from ..state.schema import BugFixState


def should_continue_fixing(state: BugFixState) -> str:
    """
    Decide whether to continue fixing or end

    Args:
        state: Current workflow state

    Returns:
        Next node name: "fix_bugs", "done", or "max_iterations"
    """
    results = state.get('test_results', {})

    # Check if all tests passed
    if results.get('failed', 1) == 0 and results.get('errors', 1) == 0:
        return "done"

    # Check iteration limit
    if state['iteration'] >= state['max_iterations']:
        return "max_iterations"

    # Continue fixing
    return "fix_bugs"


def make_routing_decision(state: BugFixState) -> dict:
    """
    Make and document routing decision

    Args:
        state: Current workflow state

    Returns:
        Decision dict with route and reason
    """
    route = should_continue_fixing(state)
    results = state.get('test_results', {})

    if route == "done":
        reason = "All tests passed!"
    elif route == "max_iterations":
        reason = f"Reached max iterations ({state['max_iterations']})"
    else:
        failed = results.get('failed', 0)
        errors = results.get('errors', 0)
        reason = f"{failed + errors} tests still failing"

    return {
        "route": route,
        "reason": reason,
        "iteration": state['iteration'],
        "test_results": {
            "passed": results.get('passed', 0),
            "failed": results.get('failed', 0),
            "errors": results.get('errors', 0)
        }
    }
