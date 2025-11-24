"""State schema for bug-fixing workflow"""
from typing import TypedDict, Literal, Any
from datetime import datetime


class ContextSwitch(TypedDict, total=False):
    """Record of a context switch between agents"""
    timestamp: str
    from_context: str
    to_context: str
    reason: str
    output: str
    iteration: int


class FailureDetail(TypedDict, total=False):
    """Details of a test failure"""
    test_name: str
    error_message: str
    stack_trace: str
    line_number: int


class TestResults(TypedDict, total=False):
    """Test execution results"""
    passed: int
    failed: int
    errors: int
    failures: list[FailureDetail]
    stdout: str
    stderr: str
    returncode: int


class FixAttempt(TypedDict, total=False):
    """Record of a bug fix attempt"""
    iteration: int
    timestamp: str
    changes: list[str]
    reason: str


class BugFixState(TypedDict, total=False):
    """
    Complete state that flows through the LangGraph workflow.

    This state is passed between agents and modified at each step.
    All fields are optional to allow partial updates.
    """

    # Core data
    language: str                              # "python", "java", "go", etc.
    code: str                                  # Current code being fixed
    test_framework: str                        # "pytest", "junit", etc.

    # Specifications
    behavior_spec: dict[str, Any]              # Expected behavior from analysis
    test_cases: str                            # Generated test code

    # Execution results
    test_results: TestResults                  # Latest test execution results
    execution_logs: str                        # stdout/stderr from execution

    # Iteration tracking
    iteration: int                             # Current iteration number
    max_iterations: int                        # Maximum allowed iterations
    status: Literal[
        "specifying",                          # Analyzing behavior
        "testing",                             # Generating tests
        "executing",                           # Running tests
        "fixing",                              # Fixing bugs
        "passed",                              # All tests passed
        "failed"                               # Max iterations without success
    ]

    # Debug metadata
    context_history: list[ContextSwitch]       # All context switches
    decision_log: list[dict[str, Any]]         # Decision rationale
    timestamps: dict[str, str]                 # Timing of each step

    # Error tracking
    error_history: list[dict[str, Any]]        # Previous errors
    fix_attempts: list[FixAttempt]             # All fix attempts


def create_initial_state(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    max_iterations: int = 5
) -> BugFixState:
    """Create initial state for a bug-fixing session"""
    return BugFixState(
        language=language,
        code=code,
        test_framework=test_framework,
        iteration=0,
        max_iterations=max_iterations,
        status="specifying",
        behavior_spec={},
        test_cases="",
        test_results={},
        execution_logs="",
        context_history=[],
        decision_log=[],
        timestamps={},
        error_history=[],
        fix_attempts=[]
    )


def serialize_state(state: BugFixState) -> dict[str, Any]:
    """Convert state to JSON-serializable dict"""
    return dict(state)


def deserialize_state(data: dict[str, Any]) -> BugFixState:
    """Convert dict to BugFixState"""
    return BugFixState(**data)
