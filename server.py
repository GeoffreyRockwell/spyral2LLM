#!/usr/bin/env python3
"""
Local dev server for spyral2LLM.
- Serves static files on GET requests
- Proxies POST /api/claude → https://api.anthropic.com/v1/messages (streaming)
- Proxies GET /api/ollama/tags → http://localhost:11434/api/tags
- Proxies POST /api/ollama/chat → http://localhost:11434/api/chat (streaming)

The Ollama proxy routes exist because Ollama rejects requests whose Origin
header is "null" (what browsers send for pages opened via file://), so the
page's direct fetch to Ollama fails when it isn't served over http://.
"""

import http.server
import http.client
import json
import os
import ssl

PORT = 8080
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434


class Handler(http.server.SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/ollama/tags":
            self._proxy(OLLAMA_HOST, OLLAMA_PORT, "GET", "/api/tags", use_ssl=False)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/claude":
            api_key = self.headers.get("x-api-key", "")
            version = self.headers.get("anthropic-version", "2023-06-01")
            self._proxy(
                "api.anthropic.com", 443, "POST", "/v1/messages", use_ssl=True,
                extra_headers={"x-api-key": api_key, "anthropic-version": version},
            )
        elif self.path == "/api/ollama/chat":
            self._proxy(OLLAMA_HOST, OLLAMA_PORT, "POST", "/api/chat", use_ssl=False)
        else:
            self.send_error(404)

    def _proxy(self, host, port, method, path, use_ssl, extra_headers=None):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length) if length else None

        conn = None
        try:
            if use_ssl:
                try:
                    import certifi
                    ctx = ssl.create_default_context(cafile=certifi.where())
                except ImportError:
                    ctx = ssl._create_unverified_context()
                conn = http.client.HTTPSConnection(host, port, context=ctx)
            else:
                conn = http.client.HTTPConnection(host, port)

            headers = {"Content-Type": "application/json"}
            if extra_headers:
                headers.update(extra_headers)

            conn.request(method, path, body=body, headers=headers)
            resp = conn.getresponse()

            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/octet-stream"))
            self.send_header("Cache-Control", "no-cache")
            self._cors()
            self.end_headers()

            while True:
                chunk = resp.read(512)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()

        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())
        finally:
            if conn:
                conn.close()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, x-api-key, anthropic-version")

    def log_message(self, fmt, *args):
        if len(args) >= 2 and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Ready →  http://localhost:{PORT}")
    http.server.HTTPServer(("", PORT), Handler).serve_forever()
