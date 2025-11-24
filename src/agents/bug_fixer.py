"""Bug fixing agent"""
from datetime import datetime
import json
import difflib
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..state.schema import BugFixState
from ..utils.prompts import BUG_FIXER_PROMPT


class BugFixerAgent:
    """
    Analyzes test failures and fixes bugs

    Takes failed tests and modifies code to fix the issues.
    """

    def __init__(self, tracer, logger, model: str = "claude-3-5-sonnet-20241022"):
        self.llm = ChatAnthropic(model=model, temperature=0.2)
        self.tracer = tracer
        self.logger = logger

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert debugger. Output only the corrected code, nothing else."),
            ("user", BUG_FIXER_PROMPT)
        ])

        self.chain = self.prompt | self.llm

    def __call__(self, state: BugFixState) -> dict:
        """
        Fix bugs based on test failures

        Args:
            state: Current workflow state

        Returns:
            State updates
        """
        test_results = state.get('test_results', {})
        failed_count = test_results.get('failed', 0)

        # Log context entry
        self.tracer.log_context_switch({
            "timestamp": datetime.now(),
            "from_context": "executor",
            "to_context": "bug_fixer",
            "reason": f"Fix {failed_count} failing tests",
            "iteration": state['iteration']
        })

        # Format failures for prompt
        failures_text = self._format_failures(test_results.get('failures', []))

        # Format previous attempts
        previous_attempts = self._format_previous_attempts(state.get('fix_attempts', []))

        # Call LLM
        try:
            response = self.chain.invoke({
                "language": state['language'],
                "code": state['code'],
                "failures": failures_text,
                "previous_attempts": previous_attempts,
                "execution_logs": state.get('execution_logs', '')[:1000]  # Limit log size
            })

            fixed_code = response.content.strip()

            # Remove markdown code blocks if present
            if fixed_code.startswith("```"):
                lines = fixed_code.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                fixed_code = '\n'.join(lines)

            # Create fix attempt record
            fix_attempt = {
                "iteration": state['iteration'],
                "timestamp": datetime.now().isoformat(),
                "changes": self._diff(state['code'], fixed_code),
                "reason": f"Fix {failed_count} test failures"
            }

            # Log fix attempt
            self.logger.log_fix_attempt(
                iteration=state['iteration'],
                fix=fix_attempt
            )

            # Show fix in console
            self.tracer.show_fix_attempt(
                state['iteration'],
                f"Modified {len(fix_attempt['changes'])} lines"
            )

            # Update state
            return {
                "code": fixed_code,
                "iteration": state['iteration'] + 1,
                "status": "executing",
                "fix_attempts": state.get('fix_attempts', []) + [fix_attempt],
                "context_history": state.get('context_history', []) + [{
                    "timestamp": datetime.now().isoformat(),
                    "from_context": "executor",
                    "to_context": "bug_fixer",
                    "reason": "Applied bug fix",
                    "output": f"Modified {len(fix_attempt['changes'])} lines",
                    "iteration": state['iteration']
                }],
                "timestamps": {
                    **state.get('timestamps', {}),
                    "fix": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.log_error("bug_fixer", str(e), state['iteration'])
            return {
                "status": "failed",
                "error_history": state.get('error_history', []) + [{
                    "context": "bug_fixer",
                    "error": str(e),
                    "iteration": state['iteration']
                }]
            }

    def _format_failures(self, failures: list) -> str:
        """Format failure details for prompt"""
        if not failures:
            return "No specific failure details available"

        formatted = []
        for i, failure in enumerate(failures[:5], 1):  # Max 5 failures
            formatted.append(
                f"Failure {i}: {failure.get('test_name', 'unknown')}\n"
                f"Error: {failure.get('error_message', 'No message')}\n"
            )

        return "\n".join(formatted)

    def _format_previous_attempts(self, attempts: list) -> str:
        """Format previous fix attempts"""
        if not attempts:
            return "No previous attempts"

        formatted = []
        for attempt in attempts[-3:]:  # Last 3 attempts
            formatted.append(
                f"Iteration {attempt.get('iteration')}: "
                f"{attempt.get('reason', 'Fix attempt')}"
            )

        return "\n".join(formatted)

    def _diff(self, old: str, new: str) -> list:
        """Calculate diff between old and new code"""
        return list(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            lineterm=''
        ))
