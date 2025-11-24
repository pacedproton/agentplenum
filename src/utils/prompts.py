"""Prompt templates for agents"""

BEHAVIOR_SPECIFIER_PROMPT = """You are a behavior specification expert.

Analyze the provided code and specify its intended behavior in detail.

Output a JSON object with:
- "purpose": What the code should do (1-2 sentences)
- "inputs": Expected inputs and their types/constraints
- "outputs": Expected outputs and their types
- "edge_cases": Important edge cases to handle
- "constraints": Any constraints or invariants

Be specific and thorough. This spec will be used to generate test cases.

Language: {language}

Code:
```{language}
{code}
```

Output ONLY valid JSON, no other text."""

TEST_GENERATOR_PROMPT = """You are a test generation expert.

Create comprehensive test cases based on the behavior specification.

Generate tests for:
- Normal/happy path cases (at least 2)
- Edge cases from the spec
- Error conditions
- Boundary values

Test Framework: {test_framework}
Language: {language}

Behavior Specification:
{behavior_spec}

Original Code:
```{language}
{code}
```

Output ONLY valid {test_framework} test code that can be executed directly.
Import from 'solution' module (the code will be in solution.py).
NO explanations, NO markdown formatting, just the test code."""

BUG_FIXER_PROMPT = """You are an expert debugger and code fixer.

Analyze the test failures and fix the bugs in the code.

Consider:
1. Root cause of each failure
2. Previous fix attempts (to avoid repeating mistakes)
3. Minimal changes needed
4. Don't break passing tests

Language: {language}

Current Code:
```{language}
{code}
```

Test Failures:
{failures}

Previous Fix Attempts:
{previous_attempts}

Execution Logs:
{execution_logs}

Output ONLY the corrected code, nothing else.
NO explanations, NO markdown formatting, just the fixed code."""

SIMPLE_BEHAVIOR_PROMPT = """Analyze this {language} code and describe what it should do:

{code}

Provide a concise JSON with: purpose, inputs, outputs, edge_cases."""

SIMPLE_TEST_PROMPT = """Generate {test_framework} tests for this {language} code.

Code:
{code}

Expected behavior:
{behavior}

Create at least 3 tests covering normal cases and edge cases."""
