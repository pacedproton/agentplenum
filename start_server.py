#!/usr/bin/env python3
"""Start the bug-fixing forum API server"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.server import start_server

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start bug-fixing forum API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  Bug-Fixing Forum API Server                            ║
║                                                          ║
║  Starting on http://{args.host}:{args.port}                    ║
║                                                          ║
║  API Docs: http://{args.host}:{args.port}/docs                 ║
║  Health: http://{args.host}:{args.port}/                       ║
╚══════════════════════════════════════════════════════════╝
""")

    start_server(host=args.host, port=args.port)
