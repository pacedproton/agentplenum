#!/usr/bin/env python3
"""Example client for bug-fixing forum API"""
import requests
import time
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

API_BASE = "http://localhost:8000"


def create_session(code: str, language: str = "python", max_iterations: int = 5):
    """Create a new bug-fixing session"""

    console.print("[bold cyan]Creating bug-fixing session...[/bold cyan]")

    response = requests.post(f"{API_BASE}/sessions", json={
        "code": code,
        "language": language,
        "test_framework": "pytest",
        "max_iterations": max_iterations
    })

    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        console.print(f"[green]✓ Session created: {session_id}[/green]")
        return session_id
    else:
        console.print(f"[red]✗ Error: {response.status_code}[/red]")
        console.print(response.text)
        return None


def watch_session(session_id: str):
    """Poll session status until complete"""

    console.print(f"\n[bold yellow]Watching session: {session_id}[/bold yellow]\n")

    while True:
        response = requests.get(f"{API_BASE}/sessions/{session_id}")

        if response.status_code == 200:
            status = response.json()

            console.print(
                f"[cyan]Status:[/cyan] {status['status']} | "
                f"[cyan]Iteration:[/cyan] {status['iteration']}/{status['max_iterations']} | "
                f"[cyan]Step:[/cyan] {status['current_step']}"
            )

            if status.get('test_results'):
                results = status['test_results']
                console.print(
                    f"  [green]✓ Passed: {results.get('passed', 0)}[/green] | "
                    f"[red]✗ Failed: {results.get('failed', 0)}[/red]"
                )

            if status['status'] in ['completed', 'failed', 'cancelled']:
                break

        else:
            console.print(f"[red]Error: {response.status_code}[/red]")
            break

        time.sleep(2)


def get_result(session_id: str):
    """Get final result of session"""

    console.print(f"\n[bold cyan]Fetching results...[/bold cyan]\n")

    response = requests.get(f"{API_BASE}/sessions/{session_id}/result")

    if response.status_code == 200:
        result = response.json()

        if result['status'] == 'passed':
            console.print(Panel(
                "[bold green]✓ All tests passed![/bold green]\n\n"
                f"Iterations: {result['iterations']}\n"
                f"Tests passed: {result['test_results'].get('passed', 0)}",
                title="Success",
                border_style="green"
            ))

            console.print("\n[bold]Fixed Code:[/bold]")
            console.print(Panel(result['final_code'], title="Fixed Code", border_style="green"))
        else:
            console.print(Panel(
                f"[bold red]✗ Failed to fix all bugs[/bold red]\n\n"
                f"Iterations: {result['iterations']}\n"
                f"Tests failed: {result['test_results'].get('failed', 0)}",
                title="Incomplete",
                border_style="red"
            ))

        console.print(f"\n[dim]Session data: {result['session_path']}[/dim]")

        return result

    else:
        console.print(f"[red]Error: {response.status_code}[/red]")
        console.print(response.text)
        return None


def check_health():
    """Check if server is healthy"""
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]✓ Server is {data['status']}[/green]")
            console.print(f"  Version: {data['version']}")
            return True
        return False
    except requests.ConnectionError:
        console.print(f"[red]✗ Cannot connect to server at {API_BASE}[/red]")
        console.print(f"  Make sure to run: python start_server.py")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bug-fixing forum API client")
    parser.add_argument("--example", default="division", help="Example problem")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max iterations")

    args = parser.parse_args()

    # Examples
    examples = {
        "division": """def divide(a: float, b: float) -> float:
    '''Divide two numbers'''
    return a / b

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    '''Safely divide, return default if division by zero'''
    return a / b
""",
        "overflow": """def add_numbers(a: int, b: int) -> int:
    '''Add two integers'''
    return a + b

def multiply_safe(a: int, b: int, max_value: int = 1000000) -> int:
    '''Multiply two numbers, return -1 if overflow'''
    result = a * b
    return result if result <= max_value else -1
"""
    }

    console.print(Panel.fit(
        "[bold cyan]Bug-Fixing Forum API Client[/bold cyan]\n"
        f"API: {API_BASE}",
        border_style="cyan"
    ))

    # Check health
    if not check_health():
        exit(1)

    # Get code
    code = examples.get(args.example, examples["division"])

    console.print("\n[bold]Original Code:[/bold]")
    console.print(Panel(code, title="Buggy Code", border_style="red"))

    # Create session
    session_id = create_session(code, max_iterations=args.max_iterations)

    if not session_id:
        exit(1)

    # Watch progress
    watch_session(session_id)

    # Get results
    get_result(session_id)
