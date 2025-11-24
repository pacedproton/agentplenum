"""File-based structured logging"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


class FileLogger:
    """
    JSONL-based structured logger for bug-fixing sessions

    Each log entry is a JSON object on a single line.
    This format is easy to parse and analyze later.
    """

    def __init__(self, log_file: Path):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Also set up Python logging for errors
        self.logger = logging.getLogger(f"BugFixForum.{log_file.stem}")
        self.logger.setLevel(logging.INFO)

        # File handler for structured JSON logs
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def _write_entry(self, entry: dict[str, Any]):
        """Write a JSON entry to the log file"""
        entry_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            **entry
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry_with_timestamp, default=str) + '\n')

    def log_context_switch(self, context: str, to_context: str, iteration: int, reason: str = ""):
        """Log a context switch between agents"""
        self._write_entry({
            "event": "context_switch",
            "from_context": context,
            "to_context": to_context,
            "iteration": iteration,
            "reason": reason
        })

    def log_agent_decision(self, context: str, iteration: int, decision: dict):
        """Log an agent's decision"""
        self._write_entry({
            "event": "agent_decision",
            "context": context,
            "iteration": iteration,
            "decision": decision
        })

    def log_test_execution(self, iteration: int, results: dict):
        """Log test execution results"""
        self._write_entry({
            "event": "test_execution",
            "iteration": iteration,
            "results": {
                "passed": results.get('passed', 0),
                "failed": results.get('failed', 0),
                "errors": results.get('errors', 0),
                "failure_count": len(results.get('failures', []))
            }
        })

    def log_fix_attempt(self, iteration: int, fix: dict):
        """Log a bug fix attempt"""
        self._write_entry({
            "event": "fix_attempt",
            "iteration": iteration,
            "fix": fix
        })

    def log_node_execution(self, node_name: str, iteration: int, status: str):
        """Log graph node execution"""
        self._write_entry({
            "event": "node_execution",
            "node": node_name,
            "iteration": iteration,
            "status": status
        })

    def log_error(self, context: str, error: str, iteration: int):
        """Log an error"""
        self._write_entry({
            "event": "error",
            "context": context,
            "iteration": iteration,
            "error": error
        })

    def log_session_start(self, language: str, max_iterations: int):
        """Log session start"""
        self._write_entry({
            "event": "session_start",
            "language": language,
            "max_iterations": max_iterations
        })

    def log_session_end(self, status: str, iterations: int, test_results: Optional[dict] = None):
        """Log session completion"""
        self._write_entry({
            "event": "session_end",
            "status": status,
            "iterations": iterations,
            "test_results": test_results or {}
        })

    def read_log_entries(self) -> list[dict]:
        """Read all log entries from file"""
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return entries
