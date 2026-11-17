from __future__ import annotations
import hashlib, time
from turingfall.core.result import Result, Status, Code

def _hash(prefix: str, challenge: str, nonce: int) -> bytes:
    return hashlib.sha256(f"{prefix}{challenge}{nonce}".encode()).digest()

def verify(prefix: str, challenge: str, nonce: int, bits: int) -> bool:
    return int.from_bytes(_hash(prefix, challenge, nonce), "big") < (1 << (256 - bits))

def solve(prefix: str, challenge: str, bits: int, budget_ms: int = 30_000) -> Result:
    """PoW selalu punya jawaban; satu-satunya kegagalan adalah kehabisan waktu."""
    if not 1 <= bits <= 40:
        return Result(Status.FAILED, "nonce", code=Code.INPUT, trace={"bits": bits})
    t0, n, target = time.perf_counter(), 0, 1 << (256 - bits)
    while True:
        if int.from_bytes(_hash(prefix, challenge, n), "big") < target:
            ms = int((time.perf_counter() - t0) * 1000)
            return Result(Status.SOLVED, "nonce", str(n), 1.0, elapsed_ms=ms,
                          trace={"attempts": n + 1, "bits": bits})
        n += 1
        if (n & 0xFFF) == 0 and (time.perf_counter() - t0) * 1000 > budget_ms:
            return Result(Status.FAILED, "nonce", code=Code.TIMEOUT,
                          elapsed_ms=int((time.perf_counter() - t0) * 1000),
                          trace={"tried": n, "bits": bits})
