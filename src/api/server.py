"""FastAPI server for bug-fixing forum"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime
from typing import Dict
import uvicorn

from .models import BugFixRequest, SessionStatus, SessionResult, StreamEvent, HealthCheck
from ..state.schema import create_initial_state
from ..checkpointing.state_manager import StateManager, SessionRegistry
from ..observability.file_logger import FileLogger
from ..graph.workflow import create_workflow


# Session storage
active_sessions: Dict[str, dict] = {}
session_registry = SessionRegistry()


class SimpleTracer:
    """Lightweight tracer for API mode"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events = []

    def log_context_switch(self, switch: dict):
        self.events.append({
            "type": "context_switch",
            "timestamp": datetime.now().isoformat(),
            "data": switch
        })

    def show_node_completion(self, node_name: str, state: dict):
        self.events.append({
            "type": "node_complete",
            "timestamp": datetime.now().isoformat(),
            "data": {"node": node_name, "status": state.get('status')}
        })

    def show_iteration_start(self, iteration: int, max_iterations: int):
        self.events.append({
            "type": "iteration_start",
            "timestamp": datetime.now().isoformat(),
            "data": {"iteration": iteration, "max_iterations": max_iterations}
        })

    def show_test_failures(self, failures: list):
        pass  # Logged elsewhere

    def show_fix_attempt(self, iteration: int, fix_description: str):
        pass  # Logged elsewhere

    def create_summary_table(self, state: dict):
        return None

    def show_final_summary(self, state: dict):
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Bug-Fixing Forum API starting up...")
    yield
    # Shutdown
    print("🛑 Bug-Fixing Forum API shutting down...")


app = FastAPI(
    title="Bug-Fixing Forum API",
    description="Multi-agent bug-fixing system with LangGraph",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run_bug_fix_session(
    request: BugFixRequest,
    session_id: str
):
    """Run bug-fixing session in background"""
    try:
        # Initialize
        state_manager = StateManager(request.session_name or session_id)
        tracer = SimpleTracer(session_id)
        logger = FileLogger(state_manager.logs_dir / f"{session_id}.jsonl")

        # Create workflow
        workflow = create_workflow(tracer, logger, state_manager)

        # Initial state
        initial_state = create_initial_state(
            code=request.code,
            language=request.language,
            test_framework=request.test_framework,
            max_iterations=request.max_iterations
        )

        # Update session info
        active_sessions[session_id]["status"] = "running"
        active_sessions[session_id]["started_at"] = datetime.now()

        # Log session start
        logger.log_session_start(request.language, request.max_iterations)

        # Run workflow
        final_state = None
        async for chunk in workflow.astream(initial_state):
            node_name = list(chunk.keys())[0]
            node_output = chunk[node_name]

            # Save checkpoint
            if 'iteration' in node_output:
                state_manager.save_checkpoint(node_output, node_output['iteration'])

            # Update session
            active_sessions[session_id].update({
                "iteration": node_output.get('iteration', 0),
                "status": "running",
                "current_step": node_name,
                "test_results": node_output.get('test_results'),
                "updated_at": datetime.now()
            })

            # Track final state
            if final_state is None:
                final_state = node_output
            else:
                final_state = {**final_state, **node_output}

        # Save summary
        state_manager.save_session_summary({
            "session_id": session_id,
            "status": final_state['status'],
            "iterations": final_state['iteration'],
            "final_test_results": final_state.get('test_results', {}),
            "context_switches": len(final_state.get('context_history', [])),
            "fix_attempts": len(final_state.get('fix_attempts', []))
        })

        # Log session end
        logger.log_session_end(
            status=final_state['status'],
            iterations=final_state['iteration'],
            test_results=final_state.get('test_results', {})
        )

        # Update final session info
        active_sessions[session_id].update({
            "status": "completed",
            "final_state": final_state,
            "session_path": str(state_manager.session_dir),
            "completed_at": datetime.now()
        })

    except Exception as e:
        active_sessions[session_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now()
        })


@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version="0.1.0",
        agents={
            "behavior_specifier": "ready",
            "test_generator": "ready",
            "bug_fixer": "ready",
            "executor": "ready"
        }
    )


@app.post("/sessions", response_model=dict)
async def create_session(
    request: BugFixRequest,
    background_tasks: BackgroundTasks
):
    """Start a new bug-fixing session"""

    # Generate session ID
    session_id = request.session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Check if session already exists
    if session_id in active_sessions:
        raise HTTPException(status_code=409, detail=f"Session {session_id} already exists")

    # Initialize session
    active_sessions[session_id] = {
        "session_id": session_id,
        "status": "initializing",
        "iteration": 0,
        "max_iterations": request.max_iterations,
        "current_step": "starting",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    # Run in background
    background_tasks.add_task(run_bug_fix_session, request, session_id)

    return {
        "session_id": session_id,
        "status": "started",
        "message": f"Bug-fixing session {session_id} started"
    }


@app.get("/sessions/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get current status of a session"""

    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session = active_sessions[session_id]

    return SessionStatus(
        session_id=session["session_id"],
        status=session["status"],
        iteration=session.get("iteration", 0),
        max_iterations=session.get("max_iterations", 5),
        test_results=session.get("test_results"),
        current_step=session.get("current_step", "unknown"),
        started_at=session.get("started_at", session["created_at"]),
        updated_at=session["updated_at"]
    )


@app.get("/sessions/{session_id}/result", response_model=SessionResult)
async def get_session_result(session_id: str):
    """Get final result of a completed session"""

    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session = active_sessions[session_id]

    if session["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail=f"Session {session_id} is still {session['status']}")

    if session["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Session {session_id} failed: {session.get('error')}")

    final_state = session.get("final_state", {})

    return SessionResult(
        session_id=session_id,
        status=final_state.get('status', 'failed'),
        iterations=final_state.get('iteration', 0),
        final_code=final_state.get('code', ''),
        test_results=final_state.get('test_results', {}),
        context_history=final_state.get('context_history', []),
        fix_attempts=final_state.get('fix_attempts', []),
        session_path=session.get('session_path', '')
    )


@app.get("/sessions")
async def list_sessions():
    """List all sessions"""
    return {
        "active_sessions": list(active_sessions.keys()),
        "total": len(active_sessions)
    }


@app.delete("/sessions/{session_id}")
async def cancel_session(session_id: str):
    """Cancel a running session"""

    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session = active_sessions[session_id]

    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail=f"Session {session_id} already completed")

    # Mark as cancelled
    active_sessions[session_id]["status"] = "cancelled"
    active_sessions[session_id]["updated_at"] = datetime.now()

    return {"message": f"Session {session_id} cancelled"}


@app.websocket("/ws/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time session updates"""
    await websocket.accept()

    try:
        if session_id not in active_sessions:
            await websocket.send_json({"error": f"Session {session_id} not found"})
            await websocket.close()
            return

        # Stream updates
        last_update = None
        while True:
            session = active_sessions.get(session_id)

            if not session:
                break

            # Send update if changed
            current_update = session.get("updated_at")
            if current_update != last_update:
                await websocket.send_json({
                    "type": "status_update",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "status": session["status"],
                        "iteration": session.get("iteration", 0),
                        "current_step": session.get("current_step", "unknown"),
                        "test_results": session.get("test_results")
                    }
                })
                last_update = current_update

            # Exit if completed or failed
            if session["status"] in ["completed", "failed", "cancelled"]:
                await websocket.send_json({
                    "type": "session_complete",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"status": session["status"]}
                })
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
