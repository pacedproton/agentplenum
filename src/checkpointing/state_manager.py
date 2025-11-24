"""File-based state management and checkpointing"""
from pathlib import Path
import json
from datetime import datetime
from typing import Optional
from ..state.schema import BugFixState, serialize_state, deserialize_state


class StateManager:
    """
    Manages state persistence using flat files.

    - Saves checkpoints after each iteration
    - Maintains session directory structure
    - Supports loading from any checkpoint
    """

    def __init__(self, session_name: Optional[str] = None, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.checkpoints_dir = self.data_dir / "checkpoints"
        self.logs_dir = self.data_dir / "logs"
        self.sessions_dir = self.data_dir / "sessions"

        # Create directories
        for dir_path in [self.checkpoints_dir, self.logs_dir, self.sessions_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Session ID
        self.session_name = session_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.sessions_dir / self.session_name
        self.session_dir.mkdir(exist_ok=True)

    def save_checkpoint(self, state: BugFixState, iteration: int) -> Path:
        """
        Save state checkpoint to file

        Args:
            state: Current state to save
            iteration: Iteration number

        Returns:
            Path to saved checkpoint file
        """
        checkpoint_file = self.session_dir / f"checkpoint_iter_{iteration:03d}.json"

        checkpoint_data = {
            "state": serialize_state(state),
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_name
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        # Also save as current
        current_file = self.session_dir / "current_state.json"
        with open(current_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        return checkpoint_file

    def load_checkpoint(self, iteration: Optional[int] = None) -> Optional[BugFixState]:
        """
        Load checkpoint from file

        Args:
            iteration: Specific iteration to load, or None for latest

        Returns:
            Loaded state, or None if not found
        """
        if iteration is None:
            # Load latest
            checkpoint_file = self.session_dir / "current_state.json"
        else:
            checkpoint_file = self.session_dir / f"checkpoint_iter_{iteration:03d}.json"

        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
            return deserialize_state(data["state"])

    def list_checkpoints(self) -> list[int]:
        """
        List all checkpoint iterations

        Returns:
            List of iteration numbers with saved checkpoints
        """
        checkpoint_files = sorted(self.session_dir.glob("checkpoint_iter_*.json"))
        iterations = []
        for file in checkpoint_files:
            # Extract iteration number from filename
            try:
                iter_num = int(file.stem.split("_")[-1])
                iterations.append(iter_num)
            except ValueError:
                continue
        return iterations

    def save_session_summary(self, summary: dict) -> Path:
        """
        Save final session summary

        Args:
            summary: Summary data

        Returns:
            Path to summary file
        """
        summary_file = self.session_dir / "summary.json"
        summary_with_meta = {
            **summary,
            "session_id": self.session_name,
            "completed_at": datetime.now().isoformat()
        }

        with open(summary_file, 'w') as f:
            json.dump(summary_with_meta, f, indent=2, default=str)

        return summary_file

    def load_session_summary(self) -> Optional[dict]:
        """Load session summary if it exists"""
        summary_file = self.session_dir / "summary.json"

        if not summary_file.exists():
            return None

        with open(summary_file, 'r') as f:
            return json.load(f)

    def get_session_path(self) -> Path:
        """Get path to current session directory"""
        return self.session_dir


class SessionRegistry:
    """Registry of all sessions for browsing/resuming"""

    def __init__(self, data_dir: str = "data"):
        self.sessions_dir = Path(data_dir) / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self) -> list[dict]:
        """List all available sessions with metadata"""
        sessions = []

        for session_dir in sorted(self.sessions_dir.iterdir()):
            if not session_dir.is_dir():
                continue

            summary_file = session_dir / "summary.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                    sessions.append({
                        "session_id": session_dir.name,
                        "path": session_dir,
                        **summary
                    })
            else:
                # Session without summary (incomplete)
                sessions.append({
                    "session_id": session_dir.name,
                    "path": session_dir,
                    "status": "incomplete"
                })

        return sessions

    def get_latest_session(self) -> Optional[str]:
        """Get the most recent session ID"""
        sessions = self.list_sessions()
        if not sessions:
            return None
        return sessions[-1]["session_id"]
