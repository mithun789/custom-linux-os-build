#!/usr/bin/env python3
"""Tiny OpenAI-compatible server that replays a scripted tool-calling session.
Used to test orchard-agent without downloading a model. Usage: mock_llm.py PORT"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

SCRIPT = [
    {"tool_calls": [{"id": "c1", "type": "function", "function": {
        "name": "system_status", "arguments": "{}"}}]},
    {"tool_calls": [{"id": "c2", "type": "function", "function": {
        "name": "write_file", "arguments": json.dumps({"path": "/tmp/orchard-agent-test/hello.py",
                                                         "content": "print(sum(range(10)))\n"})}}]},
    {"tool_calls": [{"id": "c3", "type": "function", "function": {
        "name": "run_command", "arguments": json.dumps({"command": "python3 /tmp/orchard-agent-test/hello.py"})}}]},
    {"tool_calls": [{"id": "c4", "type": "function", "function": {
        "name": "edit_file", "arguments": json.dumps({"path": "/tmp/orchard-agent-test/hello.py",
                                                        "old_text": "range(10)", "new_text": "range(101)"})}}]},
    {"tool_calls": [{"id": "c5", "type": "function", "function": {
        "name": "run_command", "arguments": json.dumps({"command": "python3 /tmp/orchard-agent-test/hello.py"})}}]},
    {"tool_calls": [{"id": "c6", "type": "function", "function": {
        "name": "run_command", "arguments": json.dumps({"command": "sudo rm -rf / --no-preserve-root"})}}]},
]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        msgs = body["messages"]
        step = sum(1 for m in msgs if m["role"] == "assistant")
        if step < len(SCRIPT):
            msg = {"role": "assistant", "content": "", **SCRIPT[step]}
        else:
            results = [m["content"] for m in msgs if m["role"] == "tool"]
            msg = {"role": "assistant", "content": "DONE. Tool results:\n" + "\n".join(results)}
        out = json.dumps({"choices": [{"message": msg}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)


HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
