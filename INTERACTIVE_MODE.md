# Interactive Mode - No API Key Required!

This mode lets you bootstrap the bug-fixing forum using **Claude in this session** instead of API calls.

## How It Works

Instead of making API calls to Claude/OpenAI:
1. The script shows you each prompt that would be sent to the LLM
2. You (Claude in this session) provide the responses manually
3. The system executes tests and shows results
4. Repeat until bugs are fixed!

## Running Interactive Mode

```bash
python run_interactive_session.py --example division
```

## Workflow

### Step 1: Behavior Specification

The script shows:
```
PROMPT TO LLM:
[The behavior specification prompt with the code]
```

**You provide:** JSON behavior specification

Example response:
```json
{
  "purpose": "divide() divides two numbers, safe_divide() should handle division by zero",
  "inputs": "Two floats a and b, optional default float",
  "outputs": "Float result or default value",
  "edge_cases": ["division by zero", "infinity", "NaN"],
  "constraints": ["safe_divide must not raise exception on zero division"]
}
```

### Step 2: Test Generation

The script shows the test generation prompt.

**You provide:** pytest test code

Example response:
```python
import pytest

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_safe_divide_normal():
    assert safe_divide(10, 2) == 5.0

def test_safe_divide_by_zero_returns_default():
    assert safe_divide(10, 0, default=0.0) == 0.0

def test_safe_divide_by_zero_no_default():
    assert safe_divide(10, 0) == 0.0
```

### Step 3: Test Execution

The script automatically runs the tests and shows results:
```
Results:
  ✓ Passed: 2
  ✗ Failed: 3
  ⚠ Errors: 0

Failures:
1. test_safe_divide_by_zero_returns_default
   ZeroDivisionError: division by zero
...
```

### Step 4: Bug Fixing (Iterative)

The script shows the bug fix prompt with failure details.

**You provide:** Fixed code

Example response:
```python
def divide(a: float, b: float) -> float:
    '''Divide two numbers'''
    return a / b

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    '''Safely divide, return default if division by zero'''
    if b == 0:
        return default
    return a / b
```

The script re-runs tests and continues until passing or max iterations.

## Input Format

For multi-line input (code, JSON):
1. Type or paste your response
2. Press Enter twice (empty line) to submit

## Tips

### For Behavior Specs

Always include:
- `purpose`: What the code should do
- `inputs`: Expected inputs and types
- `outputs`: Expected outputs
- `edge_cases`: Edge cases to test
- `constraints`: Important constraints

### For Test Generation

- Cover normal cases
- Test all edge cases from the spec
- Include error conditions
- Use descriptive test names
- Import from `solution` module (code will be in solution.py)

### For Bug Fixes

- Only fix the actual bugs
- Don't add unnecessary features
- Keep the code simple
- Match the original structure

## Example Session

```bash
$ python run_interactive_session.py --example division

Interactive Bug Fixing Session
Session: 20251124_123456
Language: python
Mode: Manual/Interactive (No API calls)

Original Code:
┌─ Buggy Code ────┐
│ def divide(...) │
│ ...            │
└─────────────────┘

════════════════════════════════════════════════════════════
STEP 1: Behavior Specification
════════════════════════════════════════════════════════════

BEHAVIOR SPECIFIER AGENT
This agent analyzes code and outputs JSON spec

PROMPT TO LLM:
┌──────────────────────────────────────────┐
│ You are a behavior specification expert. │
│ ...                                       │
└──────────────────────────────────────────┘

Please provide the behavior specification as JSON:
(Paste JSON spec and press Enter twice)

>>> {"purpose": "divide numbers, safe_divide handles zero", ...}
>>>

✓ Valid JSON received

════════════════════════════════════════════════════════════
STEP 2: Test Generation
...
```

## Advantages

✅ **No API key needed** - Works immediately
✅ **Full control** - You see every prompt and response
✅ **Educational** - Understand how agents work
✅ **Fast** - No API latency
✅ **Debug-friendly** - See exactly what's happening

## Limitations

- Requires manual input for each step
- Slower than automated mode (for human typing)
- Best for understanding/demos, not production

## After the Session

All data is still saved:
- Checkpoints: `data/sessions/{session_id}/`
- Logs: `data/logs/{session_id}.jsonl`
- Summary: `data/sessions/{session_id}/summary.json`

## Next Steps

Once you understand the workflow:
1. Set up API key for automated mode
2. Run automated sessions with `run_debug_session.py`
3. Compare manual vs automated results
