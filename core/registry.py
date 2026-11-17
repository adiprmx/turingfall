from __future__ import annotations

SOLVERS: dict[str, type] = {}
ADAPTERS: dict[str, type] = {}

def solver(cls):
    SOLVERS[cls.name] = cls
    return cls

def adapter(cls):
    ADAPTERS[cls.family] = cls
    return cls

def load_builtin() -> None:
    from turingfall.solvers import baseline_random, classical_ocr  # noqa: F401
    from turingfall.adapters import offline  # noqa: F401
