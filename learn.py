from __future__ import annotations
import json, time
from pathlib import Path
from turingfall.core.registry import SOLVERS
from turingfall.core.challenge import Challenge, Class
from turingfall.solvers import pow as P

CHECKS = {"pow_valid": lambda spec, a: P.verify(spec["input"]["prefix"], spec["input"]["challenge"],
                                               int(a), spec["input"]["bits"])}

def verify(task_dir: Path, solver: str) -> dict:
    spec = json.loads((task_dir / "spec.json").read_text())
    ch = Challenge(spec["id"], spec["id"], Class(spec["class"]), spec["input"])
    t0 = time.perf_counter()
    res = SOLVERS[solver]().solve(ch)
    ms = int((time.perf_counter() - t0) * 1000)
    ok = res.status.value == "solved" and CHECKS[spec["check"]["type"]](spec, res.answer)
    return {"task": spec["id"], "solver": solver, "pass": ok, "elapsed_ms": ms,
            "budget_ms": spec["time_budget_ms"], "within_budget": ms <= spec["time_budget_ms"],
            "answer": res.answer}
