from __future__ import annotations
from dataclasses import dataclass, asdict, field
from enum import Enum

class Status(str, Enum):
    SOLVED = "solved"
    ABSTAIN = "abstain"
    FAILED = "failed"

class Code(str, Enum):
    INPUT = "E_INPUT"
    UNSUPPORTED = "E_UNSUPPORTED_CLASS"
    NO_MODEL = "E_NO_MODEL"
    ABSTAIN = "E_ABSTAIN"
    TIMEOUT = "E_TIMEOUT"
    UPSTREAM = "E_UPSTREAM"
    RATE_LIMIT = "E_RATE_LIMIT"
    HANDLE_EXPIRED = "E_HANDLE_EXPIRED"

NEXT = {Code.INPUT: "retry", Code.UNSUPPORTED: "give_up", Code.NO_MODEL: "escalate_human",
        Code.ABSTAIN: "retry", Code.TIMEOUT: "retry", Code.UPSTREAM: "retry",
        Code.RATE_LIMIT: "retry", Code.HANDLE_EXPIRED: "retry"}

@dataclass(slots=True)
class Result:
    status: Status
    kind: str
    answer: str | None = None
    confidence: float = 0.0
    attempt: int = 1
    elapsed_ms: int = 0
    cost_usd: float = 0.0
    code: Code | None = None
    trace: dict = field(default_factory=dict)

    @property
    def next_action(self) -> str:
        if self.status is Status.SOLVED:
            return "submit"
        return NEXT.get(self.code, "give_up") if self.code else "give_up"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["code"] = self.code.value if self.code else None
        d["next_action"] = self.next_action
        d["error"] = self.code.value if self.code else None
        return d

    @classmethod
    def abstain(cls, why: str, **kw) -> "Result":
        return cls(Status.ABSTAIN, kw.pop("kind", "text"), code=Code.ABSTAIN, trace={"why": why}, **kw)
