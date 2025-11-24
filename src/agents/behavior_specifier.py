"""Behavior specification agent"""
from datetime import datetime
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..state.schema import BugFixState
from ..utils.prompts import BEHAVIOR_SPECIFIER_PROMPT


class BehaviorSpecifierAgent:
    """
    Analyzes code and specifies expected behavior

    This agent examines the code and produces a structured
    specification of what the code should do.
    """

    def __init__(self, tracer, logger, model: str = "claude-3-5-sonnet-20241022"):
        self.llm = ChatAnthropic(model=model, temperature=0)
        self.tracer = tracer
        self.logger = logger

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a behavior specification expert. Output only valid JSON."),
            ("user", BEHAVIOR_SPECIFIER_PROMPT)
        ])

        self.chain = self.prompt | self.llm

    def __call__(self, state: BugFixState) -> dict:
        """
        Specify behavior from code

        Args:
            state: Current workflow state

        Returns:
            State updates
        """
        # Log context entry
        self.tracer.log_context_switch({
            "timestamp": datetime.now(),
            "from_context": "start",
            "to_context": "behavior_specifier",
            "reason": "Initial behavior analysis",
            "iteration": state['iteration']
        })

        # Call LLM
        try:
            response = self.chain.invoke({
                "language": state['language'],
                "code": state['code']
            })

            # Parse JSON response
            try:
                behavior_spec = json.loads(response.content)
            except json.JSONDecodeError:
                # If not valid JSON, create basic spec
                behavior_spec = {
                    "purpose": "Code analysis failed - JSON parse error",
                    "raw_response": response.content[:500]
                }

            # Log decision
            self.logger.log_agent_decision(
                context="behavior_specifier",
                iteration=state['iteration'],
                decision={
                    "action": "specified_behavior",
                    "spec_keys": list(behavior_spec.keys())
                }
            )

            # Update state
            return {
                "behavior_spec": behavior_spec,
                "status": "testing",
                "context_history": state.get('context_history', []) + [{
                    "timestamp": datetime.now().isoformat(),
                    "from_context": "start",
                    "to_context": "behavior_specifier",
                    "reason": "Analyzed code behavior",
                    "output": f"Specified: {behavior_spec.get('purpose', 'N/A')[:100]}",
                    "iteration": state['iteration']
                }],
                "timestamps": {
                    **state.get('timestamps', {}),
                    "behavior_spec": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.log_error("behavior_specifier", str(e), state['iteration'])
            return {
                "behavior_spec": {"error": str(e)},
                "status": "failed",
                "error_history": state.get('error_history', []) + [{
                    "context": "behavior_specifier",
                    "error": str(e),
                    "iteration": state['iteration']
                }]
            }
