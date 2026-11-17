from __future__ import annotations
import json, sys, time, uuid
from pathlib import Path
from turingfall.core.registry import SOLVERS, load_builtin
from turingfall.core.result import Result, Status, Code, Code as C
from turingfall.core.challenge import Challenge, Class

PROTO = "2026-07-28"
TTL = 300.0
HANDLES: dict[str, tuple[Challenge, float]] = {}

OUT_SCHEMA = {
    "type": "object",
    "required": ["status", "kind", "next_action"],
    "properties": {
        "status": {"enum": ["solved", "abstain", "failed"]},
        "answer": {"type": ["string", "null"]},
        "kind": {"type": "string"},
        "confidence": {"type": "number"},
        "next_action": {"enum": ["submit", "retry", "escalate_human", "give_up"]},
        "error": {"type": ["string", "null"]},
        "elapsed_ms": {"type": "integer"},
        "cost_usd": {"type": "number"},
    },
    "additionalProperties": False,
}

TOOLS = [
    {"name": "tf_classes", "title": "List captcha classes",
     "description": "Kembalikan 5 kelas captcha dan solver yang tersedia per kelas. Panggil ini dulu.",
     "inputSchema": {"type": "object", "additionalProperties": False},
     "annotations": {"readOnlyHint": True}},
    {"name": "tf_challenge_open", "title": "Open a challenge",
     "description": "Ambil tantangan dari file lokal atau spec. Mengembalikan handle opaque berumur 300 detik.",
     "inputSchema": {"type": "object", "additionalProperties": False,
                     "required": ["path"],
                     "properties": {"path": {"type": "string"},
                                    "class": {"enum": ["A", "B", "C", "D", "E"]}}},
     "outputSchema": {"type": "object", "required": ["handle"],
                      "properties": {"handle": {"type": "string"}}, "additionalProperties": False}},
    {"name": "tf_solve", "title": "Solve a challenge",
     "description": "Selesaikan tantangan dengan handle. Kembalikan answer + next_action. "
                    "Kalau status=abstain, panggil ulang dengan solver lain, jangan mengarang.",
     "inputSchema": {"type": "object", "additionalProperties": False,
                     "required": ["handle", "solver"],
                     "properties": {"handle": {"type": "string"}, "solver": {"type": "string"},
                                    "attempt": {"type": "integer", "minimum": 1, "maximum": 5}}},
     "outputSchema": OUT_SCHEMA},
]

def _ok(payload: dict) -> dict:
    return {"resultType": "complete", "structuredContent": payload,
            "content": [{"type": "text", "text": json.dumps(payload)}], "isError": False}

def _err(res: Result) -> dict:
    d = res.to_dict()
    return {"resultType": "complete", "structuredContent": d,
            "content": [{"type": "text", "text": json.dumps(d)}], "isError": True}

def _gc() -> None:
    now = time.time()
    for h, (_, t) in list(HANDLES.items()):
        if now - t > TTL:
            HANDLES.pop(h, None)

def call(name: str, args: dict) -> dict:
    if name == "tf_classes":
        return _ok({"classes": ["A", "B", "C", "D", "E"],
                    "solvers": {k: v.manifest.get("classes", "A") for k, v in SOLVERS.items()}})

    if name == "tf_challenge_open":
        p = Path(args["path"])
        if not p.exists():
            return _err(Result(Status.FAILED, "text", code=C.INPUT, trace={"path": str(p)}))
        img = p if p.suffix else p / "image.png"
        ch = Challenge(p.stem, "local", Class(args.get("class", "A")),
                       {"image": str(img)}, (p.parent / f"{p.stem}.txt").read_text().strip()
                       if (p.parent / f"{p.stem}.txt").exists() else None)
        h = str(uuid.uuid4())
        HANDLES[h] = (ch, time.time())
        return _ok({"handle": h})

    if name == "tf_solve":
        _gc()
        got = HANDLES.get(args["handle"])
        if not got:
            return _err(Result(Status.FAILED, "text", code=C.HANDLE_EXPIRED))
        ch, _ = got
        cls = SOLVERS.get(args["solver"])
        if not cls:
            return _err(Result(Status.FAILED, "text", code=C.UNSUPPORTED,
                               trace={"solver": args["solver"]}))
        t0 = time.perf_counter()
        try:
            res = cls().solve(ch)
        except FileNotFoundError:
            return _err(Result(Status.FAILED, "text", code=C.NO_MODEL))
        res.elapsed_ms = int((time.perf_counter() - t0) * 1000)
        res.attempt = int(args.get("attempt", 1))
        res.cost_usd = cls.manifest.get("usd_per_1k", 0.0) / 1000
        return (_ok(res.to_dict()) if res.status is Status.SOLVED else _err(res))

    raise KeyError(name)

def handle_msg(msg: dict) -> dict | None:
    m, mid = msg.get("method"), msg.get("id")
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTO, "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "turingfall", "version": "0.1.0a0"}}}
    if m in ("notifications/initialized", "notifications/cancelled"):
        return None
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"resultType": "complete", "tools": TOOLS}}
    if m == "tools/call":
        try:
            out = call(msg["params"]["name"], msg["params"].get("arguments") or {})
        except KeyError as e:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"Unknown tool: {e.args[0]}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": out}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found"}}

def serve() -> None:
    load_builtin()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            out = handle_msg(json.loads(line))
        except json.JSONDecodeError:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if out:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()
