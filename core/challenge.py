from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Class(str, Enum):
    A = "A"  # persepsi statis: OCR, klasifikasi grid, gap slider
    B = "B"  # persepsi dinamis: multi-step, reveal bertahap
    C = "C"  # komputasi: proof-of-work
    D = "D"  # protokol: endpoint audio, mint token, TLS/JA4
    E = "E"  # interaksi: jejak pointer, dwell, sesi

@dataclass(frozen=True, slots=True)
class Challenge:
    id: str
    family: str
    cls: Class
    payload: dict[str, Any]
    truth: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class Answer:
    value: str
    kind: str            # text | indices | offset_px | token | sequence
    confidence: float = 0.0
    trace: dict[str, Any] = field(default_factory=dict)
