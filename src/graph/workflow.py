"""LangGraph workflow construction"""
from langgraph.graph import StateGraph, END
from ..state.schema import BugFixState
from ..agents.behavior_specifier import BehaviorSpecifierAgent
from ..agents.test_generator import TestGeneratorAgent
from ..agents.bug_fixer import BugFixerAgent
from ..agents.executor import ExecutorAgent
from .conditions import should_continue_fixing, make_routing_decision


def create_workflow(tracer, logger, state_manager):
    """
    Create the bug-fixing LangGraph workflow

    Args:
        tracer: Console tracer for visualization
        logger: File logger for structured logging
        state_manager: State management for checkpointing

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize agents
    behavior_agent = BehaviorSpecifierAgent(tracer, logger)
    test_gen_agent = TestGeneratorAgent(tracer, logger)
    bug_fixer_agent = BugFixerAgent(tracer, logger)
    executor_agent = ExecutorAgent(tracer, logger)

    # Build graph
    workflow = StateGraph(BugFixState)

    # Add nodes
    workflow.add_node("specify_behavior", behavior_agent)
    workflow.add_node("generate_tests", test_gen_agent)
    workflow.add_node("execute_tests", executor_agent)
    workflow.add_node("fix_bugs", bug_fixer_agent)

    # Define edges
    workflow.set_entry_point("specify_behavior")
    workflow.add_edge("specify_behavior", "generate_tests")
    workflow.add_edge("generate_tests", "execute_tests")

    # Conditional routing after test execution
    def route_after_tests(state: BugFixState) -> str:
        decision = make_routing_decision(state)

        # Log decision
        logger.log_agent_decision(
            context="router",
            iteration=state['iteration'],
            decision=decision
        )

        # Show in console
        tracer.console.print(
            f"[bold magenta]Router:[/bold magenta] {decision['reason']} → [cyan]{decision['route']}[/cyan]"
        )

        return decision['route']

    workflow.add_conditional_edges(
        "execute_tests",
        route_after_tests,
        {
            "fix_bugs": "fix_bugs",
            "done": END,
            "max_iterations": END
        }
    )

    # Loop back from fixer to executor
    workflow.add_edge("fix_bugs", "execute_tests")

    # Compile (no checkpoint saver - we handle it manually)
    return workflow.compile()
