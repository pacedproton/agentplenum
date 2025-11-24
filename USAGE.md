# AgentPlenum Usage Guide

## Quick Start

### 1. Set up environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### 2. Run a debug session

```bash
# Run with default example (overflow)
python run_debug_session.py

# Run with specific example
python run_debug_session.py --example division

# Run with more iterations
python run_debug_session.py --example list_bounds --max-iterations 10

# Run with custom session name
python run_debug_session.py --example overflow --session-name "test-session-1"
```

## Available Examples

- **overflow**: Integer overflow handling bugs
- **division**: Division by zero issues
- **list_bounds**: List index out of bounds errors

## What Happens During a Session

1. **Behavior Specification**: LLM analyzes code and defines expected behavior
2. **Test Generation**: LLM creates comprehensive test cases
3. **Test Execution**: Tests run locally using pytest
4. **Bug Fixing** (if tests fail): LLM fixes bugs based on failures
5. **Iteration**: Steps 3-4 repeat until tests pass or max iterations reached

## Observability

### Real-time Console Output

Watch the agents work in real-time with Rich console formatting:
- Context switches between agents
- Test execution results
- Iteration progress
- Final summary

### Structured Logs

All sessions are logged to `data/logs/{session_id}.jsonl`:

```bash
# View logs
cat data/logs/20251124_123456.jsonl | jq

# Find all failures
grep "test_execution" data/logs/*.jsonl | jq '.results.failed'
```

### Checkpoints

State is saved after each iteration in `data/sessions/{session_id}/`:

```
data/sessions/20251124_123456/
├── checkpoint_iter_000.json  # Initial state
├── checkpoint_iter_001.json  # After first fix
├── checkpoint_iter_002.json  # After second fix
├── current_state.json        # Latest state
└── summary.json              # Final summary
```

### Browsing Sessions

```bash
# List all sessions
ls -la data/sessions/

# View session summary
cat data/sessions/20251124_123456/summary.json | jq

# View specific checkpoint
cat data/sessions/20251124_123456/checkpoint_iter_001.json | jq
```

## Session Data Structure

### State Schema

```json
{
  "language": "python",
  "code": "def add(a, b): return a + b",
  "test_framework": "pytest",
  "iteration": 2,
  "max_iterations": 5,
  "status": "fixing",
  "behavior_spec": {...},
  "test_cases": "def test_add(): ...",
  "test_results": {
    "passed": 1,
    "failed": 2,
    "failures": [...]
  },
  "context_history": [...],
  "fix_attempts": [...],
  "timestamps": {...}
}
```

### Log Entry Format (JSONL)

```json
{
  "timestamp": "2025-11-24T12:34:56.789",
  "event": "test_execution",
  "iteration": 1,
  "results": {
    "passed": 1,
    "failed": 2
  }
}
```

## Advanced Usage

### Custom Code

You can modify `run_debug_session.py` to test your own code:

```python
custom_code = """
def my_buggy_function(x):
    return x / 0  # Oops!
"""

asyncio.run(run_debug_session(
    code=custom_code,
    language="python",
    test_framework="pytest",
    max_iterations=5
))
```

### Resume from Checkpoint

```python
from src.checkpointing.state_manager import StateManager

# Load previous session
state_manager = StateManager(session_name="20251124_123456")
state = state_manager.load_checkpoint(iteration=2)

# Continue from that state...
```

## Troubleshooting

### "pytest not found"

```bash
pip install pytest
```

### "ModuleNotFoundError: No module named 'rich'"

```bash
pip install -r requirements.txt
```

### "OpenAI API key not found"

Make sure `.env` file exists with:
```
OPENAI_API_KEY=sk-your-key-here
```

### Viewing Detailed Errors

Check the structured logs:

```bash
# All errors from a session
cat data/logs/SESSION_ID.jsonl | jq 'select(.event == "error")'

# Test failures
cat data/logs/SESSION_ID.jsonl | jq 'select(.event == "test_execution" and .results.failed > 0)'
```

## File Locations

- **Sessions**: `data/sessions/{session_id}/`
- **Logs**: `data/logs/{session_id}.jsonl`
- **Checkpoints**: `data/checkpoints/` (legacy, now in sessions/)
- **Test Workspaces**: `data/test_workspaces/` (temporary)

## Next Steps

1. Try all example problems
2. Create your own buggy code to test
3. Analyze session logs to understand agent behavior
4. Experiment with different iteration limits
5. Extend to support other languages (Java, Go, etc.)
