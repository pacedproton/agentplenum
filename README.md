# AgentPlenum - Bug Fixing Forum

Language-agnostic bug fixing system using LangGraph multi-agent orchestration.

## Overview

A forum where AI agents iterate to fix bugs across different contexts:
- **Behavior Specifier**: Analyzes code and defines expected behavior
- **Test Generator**: Creates comprehensive test cases
- **Code Executor**: Runs tests in isolated environment
- **Bug Fixer**: Analyzes failures and fixes bugs

The system iterates until all tests pass or max iterations reached.

## Features

- 🔄 **Iterative fixing**: Agents collaborate until bugs resolved
- 📊 **Full observability**: Real-time console tracing + structured logs
- 💾 **File-based checkpointing**: Resume sessions from any iteration
- 🚀 **No external dependencies**: Runs locally with subprocess execution
- 🌐 **Language-agnostic**: Designed to support Python, Java, Go, etc.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run example
python run_debug_session.py --example overflow

# Run with custom iterations
python run_debug_session.py --example division --max-iterations 10
```

## Architecture

```
Browser/Terminal Context
├── LangGraph Workflow (orchestration)
├── Flat File Storage (checkpoints/logs)
└── Local Subprocess Execution (no Docker/cloud)
```

## Project Structure

```
agentplenum/
├── src/
│   ├── state/           # State schema definitions
│   ├── checkpointing/   # File-based state management
│   ├── agents/          # Agent implementations
│   ├── execution/       # Local code executor
│   ├── graph/           # LangGraph workflow
│   └── observability/   # Tracing and logging
├── data/
│   ├── checkpoints/     # State snapshots
│   ├── logs/            # JSONL logs
│   └── sessions/        # Session summaries
├── examples/            # Sample bug problems
└── run_debug_session.py # Main entry point
```

## Session Data

All session data is saved to flat files:
- `data/checkpoints/`: State at each iteration
- `data/logs/`: Structured JSONL logs
- `data/sessions/{session_id}/`: Full session history

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## License

MIT
