#!/usr/bin/env python3
"""Minimal web dashboard for the Codespace Agent TUI.

Run on port 8080 inside the codespace.
Developer monitors via: gh codespace port 8080
"""

import json
import http.server
import socketserver
import os

PORT = 8080
STATE_FILE = "/tmp/agent-state.json"
REPORT_FILE = "/tmp/agent-report.md"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>📓 A2A Notebook Agent</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
         background: #0d1117; color: #c9d1d9; padding: 20px; }}
  h1 {{ color: #58a6ff; margin-bottom: 8px; }}
  .status {{ display: flex; gap: 20px; margin: 20px 0; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
           padding: 16px; flex: 1; }}
  .card h2 {{ font-size: 14px; color: #8b949e; margin-bottom: 8px; text-transform: uppercase; }}
  .card .value {{ font-size: 24px; font-weight: bold; }}
  .phase {{ color: #d2a8ff; }}
  .progress {{ color: #3fb950; }}
  .log {{ background: #0d1117; border: 1px solid #30363d; border-radius: 8px;
          padding: 16px; margin: 20px 0; max-height: 400px; overflow-y: auto;
          font-family: monospace; font-size: 13px; }}
  .log-entry {{ padding: 2px 0; }}
  .log-time {{ color: #484f58; margin-right: 8px; }}
  .progress-bar {{ width: 100%; height: 8px; background: #21262d; border-radius: 4px;
                   margin-top: 8px; overflow: hidden; }}
  .progress-fill {{ height: 100%; background: linear-gradient(90deg, #3fb950, #58a6ff);
                   border-radius: 4px; transition: width 0.5s ease; }}
  .report {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
             padding: 16px; margin: 20px 0; white-space: pre-wrap; font-size: 13px; }}
</style>
</head>
<body>
<h1>📓 A2A Notebook Agent</h1>
<div class="status">
  <div class="card">
    <h2>Phase</h2>
    <div class="value phase" id="phase">booting</div>
  </div>
  <div class="card">
    <h2>Progress</h2>
    <div class="value progress" id="progress">0%</div>
    <div class="progress-bar"><div class="progress-fill" id="fill" style="width:0%"></div></div>
  </div>
  <div class="card">
    <h2>Errors</h2>
    <div class="value" id="errors">0</div>
  </div>
</div>
<div class="log" id="log"></div>
<div class="report" id="report">Waiting for report...</div>
<script>
  function update() {{
    fetch('/state')
      .then(r => r.json())
      .then(s => {{
        document.getElementById('phase').textContent = s.phase;
        document.getElementById('progress').textContent = s.progress + '%';
        document.getElementById('fill').style.width = s.progress + '%';
        document.getElementById('errors').textContent = s.errors.length;
        const log = document.getElementById('log');
        log.innerHTML = s.logs.map(l =>
          `<div class="log-entry"><span class="log-time">${{l.time.slice(11,19)}}</span>${{l.msg}}</div>`
        ).join('');
        log.scrollTop = log.scrollHeight;
      }});
    fetch('/report')
      .then(r => r.text())
      .then(t => {{
        if (t && t !== 'pending') {{
          document.getElementById('report').textContent = t;
        }}
      }});
  }}
  setInterval(update, 1000);
  update();
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/state':
            try:
                with open(STATE_FILE) as f:
                    data = f.read()
            except (FileNotFoundError, json.JSONDecodeError):
                data = '{"phase":"booting","progress":0,"logs":[],"errors":[]}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data.encode())
        elif self.path == '/report':
            try:
                with open(REPORT_FILE) as f:
                    data = f.read()
            except FileNotFoundError:
                data = 'pending'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(data.encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())

    def log_message(self, format, *args):
        pass  # suppress HTTP server logs


print(f"📓 Agent dashboard at http://localhost:{PORT}")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
