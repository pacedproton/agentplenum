#!/usr/bin/env python3
"""
Main entry point for bug-fixing debug session.
Fully self-contained - runs in browser/terminal context.
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.state.schema import create_initial_state, BugFixState
from src.checkpointing.state_manager import StateManager
from src.observability.console_tracer import ConsoleTracer
from src.observability.file_logger import FileLogger
from src.graph.workflow import create_workflow

console = Console()


async def run_debug_session(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    max_iterations: int = 5,
    session_name: str = None
):
    """
    Run a bug-fixing debug session with full observability

    Args:
        code: The buggy code to fix
        language: Programming language
        test_framework: Test framework to use
        max_iterations: Maximum fix iterations
        session_name: Optional session identifier

    Returns:
        Final state
    """

    # Initialize components
    state_manager = StateManager(session_name)
    tracer = ConsoleTracer(console)
    logger = FileLogger(state_manager.logs_dir / f"{state_manager.session_name}.jsonl")

    # Show welcome
    console.print(Panel.fit(
        f"[bold cyan]Bug Fixing Forum - Debug Session[/bold cyan]\n"
        f"Session: {state_manager.session_name}\n"
        f"Language: {language}\n"
        f"Max Iterations: {max_iterations}",
        border_style="cyan"
    ))

    # Log session start
    logger.log_session_start(language, max_iterations)

    # Create workflow
    workflow = create_workflow(tracer, logger, state_manager)

    # Initial state
    initial_state = create_initial_state(
        code=code,
        language=language,
        test_framework=test_framework,
        max_iterations=max_iterations
    )

    console.print("\n[bold yellow]Starting bug-fixing workflow...[/bold yellow]\n")

    # Run workflow
    try:
        final_state = None

        async for chunk in workflow.astream(initial_state):
            # chunk is dict with single key (node name)
            node_name = list(chunk.keys())[0]
            node_output = chunk[node_name]

            # Save checkpoint after each node
            if 'iteration' in node_output:
                state_manager.save_checkpoint(node_output, node_output['iteration'])

            # Show progress
            tracer.show_node_completion(node_name, node_output)

            # Track final state
            if final_state is None:
                final_state = node_output
            else:
                # Merge updates
                final_state = {**final_state, **node_output}

        # Show final results
        console.print("\n" + "="*60 + "\n")
        show_final_results(final_state, console, tracer)

        # Save summary
        save_session_summary(final_state, state_manager, logger)

        return final_state

    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted by user[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def show_final_results(state: BugFixState, console: Console, tracer: ConsoleTracer):
    """Display final results"""

    if state['status'] == 'passed':
        console.print(Panel(
            "[bold green]✓ All tests passed![/bold green]\n\n"
            f"Iterations: {state['iteration']}\n"
            f"Tests passed: {state['test_results'].get('passed', 0)}",
            title="Success",
            border_style="green"
        ))

        console.print("\n[bold]Final Code:[/bold]")
        console.print(Panel(state['code'], title="Fixed Code", border_style="green"))

    else:
        console.print(Panel(
            f"[bold red]✗ Failed to fix all bugs[/bold red]\n\n"
            f"Iterations: {state['iteration']}/{state['max_iterations']}\n"
            f"Tests passed: {state['test_results'].get('passed', 0)}\n"
            f"Tests failed: {state['test_results'].get('failed', 0)}",
            title="Incomplete",
            border_style="red"
        ))

        if state['test_results'].get('failures'):
            console.print("\n[bold]Remaining Failures:[/bold]")
            for failure in state['test_results']['failures'][:3]:
                test_name = failure.get('test_name', 'unknown')
                error_msg = failure.get('error_message', '')[:100]
                console.print(f"  • {test_name}: {error_msg}")

    # Show summary table
    console.print("\n")
    console.print(tracer.create_summary_table(state))


def save_session_summary(state: BugFixState, state_manager: StateManager, logger: FileLogger):
    """Save session summary"""
    summary = {
        "session_id": state_manager.session_name,
        "status": state['status'],
        "iterations": state['iteration'],
        "final_test_results": state.get('test_results', {}),
        "context_switches": len(state.get('context_history', [])),
        "fix_attempts": len(state.get('fix_attempts', []))
    }
    state_manager.save_session_summary(summary)

    # Log session end
    logger.log_session_end(
        status=state['status'],
        iterations=state['iteration'],
        test_results=state.get('test_results', {})
    )


def load_example_problem(name: str = "overflow") -> dict:
    """Load example problem"""
    examples = {
        "overflow": {
            "code": """def add_numbers(a: int, b: int) -> int:
    '''Add two integers'''
    return a + b

def multiply_safe(a: int, b: int, max_value: int = 1000000) -> int:
    '''Multiply two numbers, return -1 if overflow'''
    result = a * b
    return result if result <= max_value else -1
""",
            "language": "python",
            "test_framework": "pytest"
        },
        "division": {
            "code": """def divide(a: float, b: float) -> float:
    '''Divide two numbers'''
    return a / b

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    '''Safely divide, return default if division by zero'''
    return a / b
""",
            "language": "python",
            "test_framework": "pytest"
        },
        "list_bounds": {
            "code": """def get_element(lst: list, index: int):
    '''Get element at index from list'''
    return lst[index]

def get_first_and_last(lst: list) -> tuple:
    '''Get first and last elements'''
    return (lst[0], lst[-1])
""",
            "language": "python",
            "test_framework": "pytest"
        }
    }
    return examples.get(name, examples["overflow"])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run bug-fixing debug session")
    parser.add_argument("--example", default="overflow", help="Example problem to load (overflow, division, list_bounds)")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max iterations")
    parser.add_argument("--session-name", help="Session identifier")

    args = parser.parse_args()

    # Load example
    problem = load_example_problem(args.example)

    # Run
    asyncio.run(run_debug_session(
        code=problem["code"],
        language=problem["language"],
        test_framework=problem["test_framework"],
        max_iterations=args.max_iterations,
        session_name=args.session_name
    ))
