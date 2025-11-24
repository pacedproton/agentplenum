# Bug-Fixing Forum API Guide

## Starting the Server

```bash
python start_server.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API docs: `http://localhost:8000/docs`

## Endpoints

### Health Check

```bash
GET /
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "agents": {
    "behavior_specifier": "ready",
    "test_generator": "ready",
    "bug_fixer": "ready",
    "executor": "ready"
  }
}
```

### Create Bug-Fixing Session

```bash
POST /sessions
Content-Type: application/json

{
  "code": "def safe_divide(a, b):\n    return a / b",
  "language": "python",
  "test_framework": "pytest",
  "max_iterations": 5,
  "session_name": "my-session"  // optional
}
```

Response:
```json
{
  "session_id": "my-session",
  "status": "started",
  "message": "Bug-fixing session my-session started"
}
```

### Get Session Status

```bash
GET /sessions/{session_id}
```

Response:
```json
{
  "session_id": "my-session",
  "status": "running",
  "iteration": 2,
  "max_iterations": 5,
  "current_step": "bug_fixer",
  "test_results": {
    "passed": 2,
    "failed": 1,
    "errors": 0
  },
  "started_at": "2025-11-24T12:34:56",
  "updated_at": "2025-11-24T12:35:23"
}
```

Status values:
- `initializing`: Session starting
- `running`: Actively fixing bugs
- `completed`: Finished successfully
- `failed`: Error occurred
- `cancelled`: User cancelled

### Get Session Result

```bash
GET /sessions/{session_id}/result
```

Response (when completed):
```json
{
  "session_id": "my-session",
  "status": "passed",
  "iterations": 3,
  "final_code": "def safe_divide(a, b):\n    if b == 0:\n        return 0\n    return a / b",
  "test_results": {
    "passed": 5,
    "failed": 0,
    "errors": 0
  },
  "context_history": [...],
  "fix_attempts": [...],
  "session_path": "/path/to/session/data"
}
```

### List All Sessions

```bash
GET /sessions
```

Response:
```json
{
  "active_sessions": ["session-1", "session-2", "my-session"],
  "total": 3
}
```

### Cancel Session

```bash
DELETE /sessions/{session_id}
```

Response:
```json
{
  "message": "Session my-session cancelled"
}
```

### WebSocket - Real-time Updates

```javascript
ws://localhost:8000/ws/{session_id}
```

Messages received:
```json
{
  "type": "status_update",
  "timestamp": "2025-11-24T12:35:23",
  "data": {
    "status": "running",
    "iteration": 2,
    "current_step": "bug_fixer",
    "test_results": {...}
  }
}
```

```json
{
  "type": "session_complete",
  "timestamp": "2025-11-24T12:36:00",
  "data": {
    "status": "completed"
  }
}
```

## Usage Examples

### Python Client

```python
import requests
import json

# Start session
response = requests.post('http://localhost:8000/sessions', json={
    "code": """
def safe_divide(a, b):
    return a / b
""",
    "language": "python",
    "test_framework": "pytest",
    "max_iterations": 5
})

session_id = response.json()["session_id"]
print(f"Session started: {session_id}")

# Poll for status
import time
while True:
    status = requests.get(f'http://localhost:8000/sessions/{session_id}').json()
    print(f"Status: {status['status']}, Iteration: {status['iteration']}")

    if status['status'] in ['completed', 'failed']:
        break

    time.sleep(2)

# Get result
result = requests.get(f'http://localhost:8000/sessions/{session_id}/result').json()
print(f"Final code:\n{result['final_code']}")
print(f"Tests passed: {result['test_results']['passed']}")
```

### WebSocket Client (Python)

```python
import asyncio
import websockets
import json

async def watch_session(session_id):
    async with websockets.connect(f'ws://localhost:8000/ws/{session_id}') as ws:
        while True:
            message = await ws.recv()
            data = json.loads(message)

            if data['type'] == 'status_update':
                print(f"Update: {data['data']['status']} - {data['data']['current_step']}")
            elif data['type'] == 'session_complete':
                print(f"Session completed: {data['data']['status']}")
                break

asyncio.run(watch_session("my-session"))
```

### cURL Examples

```bash
# Start session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def divide(a,b): return a/b",
    "language": "python",
    "max_iterations": 3
  }'

# Check status
curl http://localhost:8000/sessions/session_20251124_123456

# Get result
curl http://localhost:8000/sessions/session_20251124_123456/result

# Cancel
curl -X DELETE http://localhost:8000/sessions/session_20251124_123456
```

### JavaScript/Fetch

```javascript
// Start session
const response = await fetch('http://localhost:8000/sessions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    code: 'def divide(a,b): return a/b',
    language: 'python',
    max_iterations: 5
  })
});

const {session_id} = await response.json();

// Watch via WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/${session_id}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'status_update') {
    console.log('Status:', data.data.status);
    console.log('Iteration:', data.data.iteration);
  } else if (data.type === 'session_complete') {
    console.log('Done!', data.data.status);
  }
};
```

## Error Responses

### 404 - Session Not Found
```json
{
  "detail": "Session my-session not found"
}
```

### 409 - Session Already Exists
```json
{
  "detail": "Session my-session already exists"
}
```

### 400 - Bad Request
```json
{
  "detail": "Session my-session is still running"
}
```

### 500 - Session Failed
```json
{
  "detail": "Session my-session failed: [error message]"
}
```

## Session Data

All session data is saved to `data/sessions/{session_id}/`:
- `checkpoint_iter_N.json` - State at each iteration
- `current_state.json` - Latest state
- `summary.json` - Final summary

Logs saved to `data/logs/{session_id}.jsonl`

## Deployment

### Production Server

```bash
# With Gunicorn
gunicorn src.api.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With Uvicorn directly
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "start_server.py", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t bug-fixing-forum .
docker run -p 8000:8000 bug-fixing-forum
```

## Environment Variables

Set these in `.env`:

```bash
ANTHROPIC_API_KEY=your_key_here

# Optional
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=bug-fixing-forum
```

## Next Steps

1. Start the server: `python start_server.py`
2. Open API docs: http://localhost:8000/docs
3. Try the examples above
4. Integrate with your application!
