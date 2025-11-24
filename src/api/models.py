"""API request/response models"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class BugFixRequest(BaseModel):
    """Request to start a bug-fixing session"""
    code: str = Field(..., description="Buggy code to fix")
    language: str = Field(default="python", description="Programming language")
    test_framework: str = Field(default="pytest", description="Test framework")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Maximum fix iterations")
    session_name: Optional[str] = Field(None, description="Optional session identifier")


class SessionStatus(BaseModel):
    """Current status of a bug-fixing session"""
    session_id: str
    status: Literal["running", "completed", "failed", "cancelled"]
    iteration: int
    max_iterations: int
    test_results: Optional[dict] = None
    current_step: str
    started_at: datetime
    updated_at: datetime


class SessionResult(BaseModel):
    """Final result of a bug-fixing session"""
    session_id: str
    status: Literal["passed", "failed"]
    iterations: int
    final_code: str
    test_results: dict
    context_history: list
    fix_attempts: list
    session_path: str


class StreamEvent(BaseModel):
    """Event streamed during session execution"""
    event_type: Literal["context_switch", "node_complete", "test_result", "iteration_start", "session_complete"]
    timestamp: datetime
    data: dict


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "0.1.0"
    agents: dict = Field(default_factory=dict)
