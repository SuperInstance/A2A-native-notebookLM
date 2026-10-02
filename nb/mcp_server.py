"""nb.mcp_server — MCP (stdio, JSON-RPC 2.0) deployment surface.

Exposes the sheet as MCP tools so any agent/runtime can drive the
notebook: nb_add, nb_eval, nb_get, nb_graph, nb_receipts. Protocol:
newline-delimited JSON-RPC — initialize / tools/list / tools/call.
Stdlib only; run:  python3 -m nb.mcp_server [--root PATH]
"""
import json
import sys
from pathlib import Path

from nb.engine import CycleError, Sheet

TOOLS = [
    {"name": "nb_add", "description": "add a cell (op: const|py|port) to the sheet",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "string"}, "deps": {"type": "array", "items": {"type": "string"}},
         "op": {"type": "string"}, "code": {"type": "string"}}, "required": ["id", "op", "code"]}},
    {"name": "nb_eval", "description": "re-eval stale cells, book receipts",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "nb_get", "description": "read a cell value",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "nb_graph", "description": "sheet DAG (nodes+edges+receipts)",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "nb_receipts", "description": "all cell receipts",
     "inputSchema": {"type": "object", "properties": {}}},
]


def call(root, name, args):
    sheet = Sheet(root)
    if name == "nb_add":
        sheet.add(args["id"], args.get("deps", []), args["op"], args["code"])
        sheet.save()
        return {"added": args["id"]}
    if name == "nb_eval":
        log = []
        sheet.eval(eval_log=log)
        return {"evaled": log}
    if name == "nb_get":
        return {"value": sheet.values[args["id"]]}
    if name == "nb_graph":
        return sheet.graph()
    if name == "nb_receipts":
        return sheet.receipts
    raise ValueError(name)


def serve(root):
    for line in sys.stdin:
        req = json.loads(line)
        rid, method = req.get("id"), req.get("method")
        try:
            if method == "initialize":
                result = {"protocolVersion": "2024-11-05",
                          "capabilities": {"tools": {}},
                          "serverInfo": {"name": "nb-spreadsheet", "version": "0.1"}}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                result = {"content": [{"type": "text",
                                       "text": json.dumps(call(root, req["params"]["name"],
                                                               req["params"].get("arguments", {})))}]}
            elif method == "notifications/initialized":
                continue
            else:
                raise ValueError(f"unknown method {method}")
            if rid is not None:
                sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}) + "\n")
        except (CycleError, KeyError, ValueError) as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid,
                                         "error": {"code": -32000, "message": str(e)}}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path.cwd()
    serve(root)
