#!/usr/bin/env python3
"""
Tiny HTTP server that serves the UV Playground page
and provides a /exec endpoint to run shell commands.

Usage:
    python server.py          # starts on port 8000
    python server.py 3000     # starts on port 3000

Then open http://localhost:8000 in your browser.
"""

import http.server
import json
import subprocess
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

ALLOWED_PREFIXES = (
    "uv ",
    "which ",
    "ls ",
    "uname ",
    "rm -rf /tmp/uv-playground-venv",
)


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/exec":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            cmd = body.get("cmd", "")

            if not any(cmd.strip().startswith(p) for p in ALLOWED_PREFIXES):
                self._json_response(
                    {"stdout": "", "stderr": "Command not allowed.", "exit_code": 1}
                )
                return

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.path.expanduser("~"),
                )
                self._json_response(
                    {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.returncode,
                    }
                )
            except subprocess.TimeoutExpired:
                self._json_response(
                    {"stdout": "", "stderr": "Command timed out.", "exit_code": 124}
                )
            except Exception as e:
                self._json_response(
                    {"stdout": "", "stderr": str(e), "exit_code": 1}
                )
        else:
            self.send_error(404)

    def _json_response(self, data):
        payload = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(f"  {args[0]}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"\n  🌱 UV Playground server running at http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop.\n")
    http.server.HTTPServer(("", PORT), Handler).serve_forever()
