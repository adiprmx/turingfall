from __future__ import annotations
from typing import Protocol, runtime_checkable
from .challenge import Answer, Challenge

@runtime_checkable
class Solver(Protocol):
    name: str
    manifest: dict          # {"usd_per_1k": float, "needs": [...], "classes": "A"}
    def solve(self, ch: Challenge) -> Answer: ...

@runtime_checkable
class Adapter(Protocol):
    family: str
    cls: str
    def fetch(self) -> Challenge: ...
    def submit(self, ch: Challenge, ans: Answer) -> bool: ...
