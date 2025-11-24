"""Test generation agent"""
from datetime import datetime
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..state.schema import BugFixState
from ..utils.prompts import TEST_GENERATOR_PROMPT


class TestGeneratorAgent:
    """
    Generates test cases from behavior specification

    Creates executable test code based on the specified behavior.
    """

    def __init__(self, tracer, logger, model: str = "claude-3-5-sonnet-20241022"):
        self.llm = ChatAnthropic(model=model, temperature=0.3)
        self.tracer = tracer
        self.logger = logger

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a test generation expert. Output only executable test code."),
            ("user", TEST_GENERATOR_PROMPT)
        ])

        self.chain = self.prompt | self.llm

    def __call__(self, state: BugFixState) -> dict:
        """
        Generate tests from behavior spec

        Args:
            state: Current workflow state

        Returns:
            State updates
        """
        # Log context entry
        self.tracer.log_context_switch({
            "timestamp": datetime.now(),
            "from_context": "behavior_specifier",
            "to_context": "test_generator",
            "reason": "Generate test cases from spec",
            "iteration": state['iteration']
        })

        # Call LLM
        try:
            response = self.chain.invoke({
                "language": state['language'],
                "test_framework": state['test_framework'],
                "behavior_spec": json.dumps(state['behavior_spec'], indent=2),
                "code": state['code']
            })

            test_cases = response.content

            # Count tests (rough estimate)
            test_count = test_cases.count("def test_") if state['language'] == "python" else "unknown"

            # Log decision
            self.logger.log_agent_decision(
                context="test_generator",
                iteration=state['iteration'],
                decision={
                    "action": "generated_tests",
                    "test_count": test_count,
                    "test_length": len(test_cases)
                }
            )

            # Update state
            return {
                "test_cases": test_cases,
                "status": "executing",
                "context_history": state.get('context_history', []) + [{
                    "timestamp": datetime.now().isoformat(),
                    "from_context": "behavior_specifier",
                    "to_context": "test_generator",
                    "reason": "Generated test suite",
                    "output": f"Created {test_count} test functions",
                    "iteration": state['iteration']
                }],
                "timestamps": {
                    **state.get('timestamps', {}),
                    "test_gen": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.log_error("test_generator", str(e), state['iteration'])
            return {
                "test_cases": "",
                "status": "failed",
                "error_history": state.get('error_history', []) + [{
                    "context": "test_generator",
                    "error": str(e),
                    "iteration": state['iteration']
                }]
            }
