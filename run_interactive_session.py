#!/usr/bin/env python3
"""
Interactive mode - No API calls needed!

This mode shows you the prompts that would be sent to the LLM,
and you (Claude in this session) can provide the responses directly.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.state.schema import create_initial_state
from src.checkpointing.state_manager import StateManager
from src.observability.console_tracer import ConsoleTracer
from src.observability.file_logger import FileLogger
from src.utils.prompts import BEHAVIOR_SPECIFIER_PROMPT, TEST_GENERATOR_PROMPT, BUG_FIXER_PROMPT
from src.execution.local_executor import LocalCodeExecutor
import json
from datetime import datetime

console = Console()


def interactive_behavior_spec(code: str, language: str) -> dict:
    """Show behavior spec prompt and get manual response"""

    console.print(Panel.fit(
        "[bold cyan]BEHAVIOR SPECIFIER AGENT[/bold cyan]\n"
        "This agent analyzes code and outputs JSON spec",
        border_style="cyan"
    ))

    prompt_text = BEHAVIOR_SPECIFIER_PROMPT.format(
        language=language,
        code=code
    )

    console.print("\n[bold yellow]PROMPT TO LLM:[/bold yellow]")
    console.print(Panel(prompt_text, border_style="yellow"))

    console.print("\n[bold green]Please provide the behavior specification as JSON:[/bold green]")
    console.print("[dim](Paste JSON spec and press Enter twice)[/dim]\n")

    # Read multi-line input
    lines = []
    print(">>> ", end="")
    while True:
        try:
            line = input()
            if line.strip() == "" and lines:
                break
            lines.append(line)
            if not line.strip():
                continue
            print("... ", end="")
        except EOFError:
            break

    response = "\n".join(lines)

    try:
        behavior_spec = json.loads(response)
        console.print("\n[green]✓ Valid JSON received[/green]")
        return behavior_spec
    except json.JSONDecodeError as e:
        console.print(f"\n[red]✗ Invalid JSON: {e}[/red]")
        console.print("[yellow]Using fallback spec[/yellow]")
        return {
            "purpose": "Manual spec needed",
            "raw_input": response[:200]
        }


def interactive_test_gen(code: str, language: str, test_framework: str, behavior_spec: dict) -> str:
    """Show test gen prompt and get manual response"""

    console.print(Panel.fit(
        "[bold cyan]TEST GENERATOR AGENT[/bold cyan]\n"
        "This agent creates test cases from behavior spec",
        border_style="cyan"
    ))

    prompt_text = TEST_GENERATOR_PROMPT.format(
        language=language,
        test_framework=test_framework,
        behavior_spec=json.dumps(behavior_spec, indent=2),
        code=code
    )

    console.print("\n[bold yellow]PROMPT TO LLM:[/bold yellow]")
    console.print(Panel(prompt_text, border_style="yellow"))

    console.print("\n[bold green]Please provide the test code:[/bold green]")
    console.print("[dim](Paste test code and press Enter twice)[/dim]\n")

    # Read multi-line input
    lines = []
    print(">>> ", end="")
    while True:
        try:
            line = input()
            if line.strip() == "" and lines:
                break
            lines.append(line)
            if not line.strip():
                continue
            print("... ", end="")
        except EOFError:
            break

    test_code = "\n".join(lines)
    console.print("\n[green]✓ Test code received[/green]")

    return test_code


def interactive_bug_fix(code: str, language: str, failures: list, execution_logs: str, previous_attempts: list) -> str:
    """Show bug fix prompt and get manual response"""

    console.print(Panel.fit(
        "[bold cyan]BUG FIXER AGENT[/bold cyan]\n"
        "This agent fixes bugs based on test failures",
        border_style="cyan"
    ))

    # Format failures
    failures_text = "\n".join([
        f"Failure {i+1}: {f.get('test_name', 'unknown')}\n"
        f"Error: {f.get('error_message', 'No message')}\n"
        for i, f in enumerate(failures[:5])
    ])

    # Format previous attempts
    attempts_text = "\n".join([
        f"Iteration {a.get('iteration')}: {a.get('reason', 'Fix attempt')}"
        for a in previous_attempts[-3:]
    ]) if previous_attempts else "No previous attempts"

    prompt_text = BUG_FIXER_PROMPT.format(
        language=language,
        code=code,
        failures=failures_text,
        previous_attempts=attempts_text,
        execution_logs=execution_logs[:1000]
    )

    console.print("\n[bold yellow]PROMPT TO LLM:[/bold yellow]")
    console.print(Panel(prompt_text, border_style="yellow"))

    console.print("\n[bold green]Please provide the fixed code:[/bold green]")
    console.print("[dim](Paste corrected code and press Enter twice)[/dim]\n")

    # Read multi-line input
    lines = []
    print(">>> ", end="")
    while True:
        try:
            line = input()
            if line.strip() == "" and lines:
                break
            lines.append(line)
            if not line.strip():
                continue
            print("... ", end="")
        except EOFError:
            break

    fixed_code = "\n".join(lines)
    console.print("\n[green]✓ Fixed code received[/green]")

    return fixed_code


def run_interactive_session(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    max_iterations: int = 5
):
    """Run interactive bug-fixing session"""

    # Initialize
    state_manager = StateManager()
    tracer = ConsoleTracer(console)
    logger = FileLogger(state_manager.logs_dir / f"{state_manager.session_name}.jsonl")
    executor = LocalCodeExecutor()

    console.print(Panel.fit(
        f"[bold cyan]Interactive Bug Fixing Session[/bold cyan]\n"
        f"Session: {state_manager.session_name}\n"
        f"Language: {language}\n"
        f"Mode: [yellow]Manual/Interactive[/yellow] (No API calls)",
        border_style="cyan"
    ))

    # Initial state
    state = create_initial_state(
        code=code,
        language=language,
        test_framework=test_framework,
        max_iterations=max_iterations
    )

    console.print("\n[bold]Original Code:[/bold]")
    console.print(Panel(code, title="Buggy Code", border_style="red"))

    # Step 1: Behavior Specification
    console.print("\n" + "="*60)
    console.print("[bold]STEP 1: Behavior Specification[/bold]")
    console.print("="*60 + "\n")

    behavior_spec = interactive_behavior_spec(code, language)
    state["behavior_spec"] = behavior_spec
    state_manager.save_checkpoint(state, 0)

    # Step 2: Test Generation
    console.print("\n" + "="*60)
    console.print("[bold]STEP 2: Test Generation[/bold]")
    console.print("="*60 + "\n")

    test_cases = interactive_test_gen(code, language, test_framework, behavior_spec)
    state["test_cases"] = test_cases
    state_manager.save_checkpoint(state, 0)

    # Step 3: Execute Tests
    console.print("\n" + "="*60)
    console.print("[bold]STEP 3: Execute Tests[/bold]")
    console.print("="*60 + "\n")

    console.print("[yellow]Running tests locally...[/yellow]")
    results = executor.execute_python_tests(code, test_cases)

    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  ✓ Passed: {results.get('passed', 0)}")
    console.print(f"  ✗ Failed: {results.get('failed', 0)}")
    console.print(f"  ⚠ Errors: {results.get('errors', 0)}")

    if results.get('failures'):
        console.print(f"\n[bold red]Failures:[/bold red]")
        for i, failure in enumerate(results['failures'][:3], 1):
            console.print(f"\n{i}. {failure.get('test_name', 'unknown')}")
            console.print(f"   {failure.get('error_message', '')[:200]}")

    state["test_results"] = results
    state["execution_logs"] = results.get('stdout', '') + '\n' + results.get('stderr', '')
    state_manager.save_checkpoint(state, 0)

    # Iteration loop
    iteration = 1
    while iteration <= max_iterations:
        if results.get('failed', 1) == 0 and results.get('errors', 1) == 0:
            console.print(Panel(
                "[bold green]✓ All tests passed![/bold green]",
                border_style="green"
            ))
            break

        console.print("\n" + "="*60)
        console.print(f"[bold]ITERATION {iteration}: Bug Fixing[/bold]")
        console.print("="*60 + "\n")

        # Get fix
        fixed_code = interactive_bug_fix(
            state['code'],
            language,
            results.get('failures', []),
            state['execution_logs'],
            state.get('fix_attempts', [])
        )

        state['code'] = fixed_code
        state['iteration'] = iteration
        state['fix_attempts'] = state.get('fix_attempts', []) + [{
            'iteration': iteration,
            'timestamp': datetime.now().isoformat()
        }]
        state_manager.save_checkpoint(state, iteration)

        # Re-run tests
        console.print("\n[yellow]Re-running tests with fixed code...[/yellow]")
        results = executor.execute_python_tests(fixed_code, test_cases)

        console.print(f"\n[bold]Results:[/bold]")
        console.print(f"  ✓ Passed: {results.get('passed', 0)}")
        console.print(f"  ✗ Failed: {results.get('failed', 0)}")
        console.print(f"  ⚠ Errors: {results.get('errors', 0)}")

        if results.get('failures'):
            console.print(f"\n[bold red]Remaining Failures:[/bold red]")
            for i, failure in enumerate(results['failures'][:3], 1):
                console.print(f"\n{i}. {failure.get('test_name', 'unknown')}")
                console.print(f"   {failure.get('error_message', '')[:200]}")

        state['test_results'] = results
        state_manager.save_checkpoint(state, iteration)

        iteration += 1

    # Final results
    console.print("\n" + "="*60)
    console.print("[bold]FINAL RESULTS[/bold]")
    console.print("="*60 + "\n")

    if state['test_results'].get('failed', 1) == 0:
        console.print(Panel(
            "[bold green]✓ SUCCESS - All tests passing![/bold green]\n\n"
            f"Iterations: {iteration - 1}\n"
            f"Session: {state_manager.session_name}",
            title="Success",
            border_style="green"
        ))
        console.print("\n[bold]Fixed Code:[/bold]")
        console.print(Panel(state['code'], title="Working Code", border_style="green"))
    else:
        console.print(Panel(
            f"[bold red]✗ Reached max iterations ({max_iterations})[/bold red]\n\n"
            f"Tests still failing: {state['test_results'].get('failed', 0)}",
            title="Incomplete",
            border_style="red"
        ))

    # Save summary
    state_manager.save_session_summary({
        "status": "passed" if state['test_results'].get('failed', 1) == 0 else "failed",
        "iterations": iteration - 1,
        "final_test_results": state['test_results']
    })

    console.print(f"\n[dim]Session data saved to: {state_manager.session_dir}[/dim]")

    return state


def load_example(name: str = "overflow") -> dict:
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
        }
    }
    return examples.get(name, examples["overflow"])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run interactive bug-fixing session (no API key needed)")
    parser.add_argument("--example", default="division", help="Example problem (overflow, division)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max iterations")

    args = parser.parse_args()

    problem = load_example(args.example)

    console.print("\n[bold cyan]═══════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  Interactive Bug Fixing with Claude      [/bold cyan]")
    console.print("[bold cyan]  No API Key Needed - Manual Mode         [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]\n")

    run_interactive_session(
        code=problem["code"],
        language=problem["language"],
        test_framework=problem["test_framework"],
        max_iterations=args.max_iterations
    )
