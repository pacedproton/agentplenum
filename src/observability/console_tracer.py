"""Console-based tracer for real-time debugging visualization"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from datetime import datetime
from typing import Any


class ConsoleTracer:
    """
    Real-time console visualization of agent execution

    Displays:
    - Context switches between agents
    - Node completion status
    - Test results
    - Iteration progress
    """

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.context_switches = []
        self.node_count = 0

    def log_context_switch(self, switch: dict):
        """
        Log a context switch between agents

        Args:
            switch: Dictionary with from_context, to_context, reason, etc.
        """
        self.context_switches.append(switch)

        timestamp = switch.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            time_str = timestamp
        else:
            time_str = timestamp.strftime('%H:%M:%S')

        self.console.print(
            f"[dim]{time_str}[/dim] "
            f"[cyan]⟹[/cyan] "
            f"[yellow]{switch['from_context']}[/yellow] → "
            f"[green]{switch['to_context']}[/green] "
            f"[dim]({switch.get('reason', 'transition')})[/dim]"
        )

    def show_node_completion(self, node_name: str, state: dict):
        """
        Show when a graph node completes

        Args:
            node_name: Name of the completed node
            state: Current state after node execution
        """
        self.node_count += 1
        status = state.get('status', 'unknown')
        iteration = state.get('iteration', 0)

        # Build status text
        status_parts = [f"Status: [bold]{status}[/bold]"]

        # Add test results if available
        if 'test_results' in state and state['test_results']:
            results = state['test_results']
            passed = results.get('passed', 0)
            failed = results.get('failed', 0)

            if failed == 0:
                status_parts.append(f"[green]✓ {passed} tests passed[/green]")
            else:
                status_parts.append(
                    f"[green]✓ {passed}[/green] [red]✗ {failed}[/red]"
                )

        status_text = "\n".join(status_parts)

        # Display panel
        self.console.print(Panel(
            f"[bold cyan]{node_name}[/bold cyan] completed\n"
            f"{status_text}\n"
            f"Iteration: {iteration}",
            border_style="blue",
            padding=(0, 1)
        ))

    def show_iteration_start(self, iteration: int, max_iterations: int):
        """Show start of new iteration"""
        self.console.print()
        self.console.rule(
            f"[bold magenta]Iteration {iteration}/{max_iterations}[/bold magenta]",
            style="magenta"
        )

    def show_test_failures(self, failures: list[dict]):
        """
        Display detailed test failure information

        Args:
            failures: List of failure details
        """
        if not failures:
            return

        self.console.print("\n[bold red]Test Failures:[/bold red]")

        for i, failure in enumerate(failures[:5], 1):  # Show first 5
            test_name = failure.get('test_name', 'unknown')
            error_msg = failure.get('error_message', '')

            self.console.print(f"\n[red]{i}. {test_name}[/red]")
            if error_msg:
                # Truncate long error messages
                error_lines = error_msg.split('\n')
                for line in error_lines[:3]:  # First 3 lines
                    self.console.print(f"   [dim]{line}[/dim]")

        if len(failures) > 5:
            self.console.print(f"\n[dim]... and {len(failures) - 5} more failures[/dim]")

    def show_fix_attempt(self, iteration: int, fix_description: str):
        """Show that a bug fix is being attempted"""
        self.console.print(Panel(
            f"[bold yellow]Attempting fix...[/bold yellow]\n{fix_description}",
            title=f"Iteration {iteration}",
            border_style="yellow"
        ))

    def create_summary_table(self, state: dict) -> Table:
        """
        Create a summary table of the current state

        Args:
            state: Current workflow state

        Returns:
            Rich Table object
        """
        table = Table(title="Session Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Language", state.get('language', 'unknown'))
        table.add_row("Status", state.get('status', 'unknown'))
        table.add_row("Iteration", str(state.get('iteration', 0)))

        if 'test_results' in state and state['test_results']:
            results = state['test_results']
            table.add_row("Tests Passed", str(results.get('passed', 0)))
            table.add_row("Tests Failed", str(results.get('failed', 0)))

        table.add_row(
            "Context Switches",
            str(len(state.get('context_history', [])))
        )
        table.add_row(
            "Fix Attempts",
            str(len(state.get('fix_attempts', [])))
        )

        return table

    def show_final_summary(self, state: dict):
        """Display final summary of the session"""
        self.console.print("\n")
        self.console.rule("[bold]Session Complete[/bold]")
        self.console.print(self.create_summary_table(state))
