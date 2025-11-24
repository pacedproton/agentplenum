"""Test execution agent"""
from datetime import datetime
from ..state.schema import BugFixState
from ..execution.local_executor import LocalCodeExecutor


class ExecutorAgent:
    """
    Executes tests and reports results

    Runs the generated tests against the code and captures results.
    """

    def __init__(self, tracer, logger):
        self.executor = LocalCodeExecutor()
        self.tracer = tracer
        self.logger = logger

    def __call__(self, state: BugFixState) -> dict:
        """
        Execute tests

        Args:
            state: Current workflow state

        Returns:
            State updates with test results
        """
        # Log context entry
        self.tracer.log_context_switch({
            "timestamp": datetime.now(),
            "from_context": state.get('status', 'unknown'),
            "to_context": "executor",
            "reason": "Execute tests",
            "iteration": state['iteration']
        })

        # Execute based on language
        if state['language'] == 'python':
            results = self.executor.execute_python_tests(
                state['code'],
                state['test_cases']
            )
        else:
            results = {
                "passed": 0,
                "failed": 1,
                "errors": 1,
                "failures": [{
                    "test_name": "execution",
                    "error_message": f"Language {state['language']} not yet supported",
                    "stack_trace": "",
                    "line_number": 0
                }],
                "stdout": "",
                "stderr": f"Unsupported language: {state['language']}",
                "returncode": -1
            }

        # Log results
        self.logger.log_test_execution(
            iteration=state['iteration'],
            results=results
        )

        # Show failures in console
        if results.get('failures'):
            self.tracer.show_test_failures(results['failures'])

        # Determine next status
        if results.get('failed', 1) == 0 and results.get('errors', 1) == 0:
            next_status = "passed"
        else:
            next_status = "fixing"

        # Update state
        return {
            "test_results": results,
            "execution_logs": results.get('stdout', '') + '\n' + results.get('stderr', ''),
            "status": next_status,
            "context_history": state.get('context_history', []) + [{
                "timestamp": datetime.now().isoformat(),
                "from_context": state.get('status', 'unknown'),
                "to_context": "executor",
                "reason": "Executed tests",
                "output": f"✓ {results.get('passed', 0)} passed, ✗ {results.get('failed', 0)} failed",
                "iteration": state['iteration']
            }],
            "timestamps": {
                **state.get('timestamps', {}),
                "execute": datetime.now().isoformat()
            }
        }
