from __future__ import annotations
import math
from collections import defaultdict

Z = 1.959963984540054

def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + Z * Z / n
    c = p + Z * Z / (2 * n)
    m = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return max(0.0, (c - m) / d), min(1.0, (c + m) / d)

def pct(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]

def summarize(records: list[dict], max_attempts: int = 3) -> dict:
    """records: {challenge_id, family, cls, attempt, correct, latency_s, cost_usd}
    per_challenge = benar pada percobaan PERTAMA (attempt == 1).
    per_session = TERUKUR langsung: tantangan yang berhasil dalam <= max_attempts.
    JANGAN turunkan per-session dari per-challenge lewat 1-(1-p)^k
    (arXiv:2609.18518: model itu "a simplified model rather than a measurement")."""
    by_ch: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_ch[r["challenge_id"]].append(r)

    hits, firsts, per_class, lat, cost = [], [], defaultdict(lambda: [0, 0]), [], []
    for cid, rs in by_ch.items():
        rs.sort(key=lambda r: r["attempt"])
        win = next((r["attempt"] for r in rs if r["correct"] and r["attempt"] <= max_attempts), None)
        hits.append(win)
        firsts.append(any(r["correct"] for r in rs if r["attempt"] == 1))
        c = rs[0]["cls"]
        per_class[c][1] += 1
        if win is not None:
            per_class[c][0] += 1
        for r in rs:
            if r["attempt"] <= max_attempts:
                lat.append(r["latency_s"])
                cost.append(r["cost_usd"])

    n = len(hits)
    k1 = sum(1 for f in firsts if f)
    ks = sum(1 for h in hits if h is not None)
    lo1, hi1 = wilson(k1, n)
    lo_s, hi_s = wilson(ks, n)
    p_ch = k1 / n if n else 0.0
    session = ks / n if n else 0.0
    c1k = sum(cost) / len(cost) * 1000 if cost else 0.0
    p95 = pct(lat, 0.95)
    # Efficiency Score v1 (dibekukan; ubah = butuh ADR)
    es = 100 * session / (1 + c1k + p95 / 2) if n else 0.0
    return {
        "n": n, "solved": ks,
        "per_challenge": p_ch, "ci95": [lo1, hi1],
        f"per_session_at_{max_attempts}": session, "ci95_session": [lo_s, hi_s],
        "per_class": {c: {"k": v[0], "n": v[1]} for c, v in sorted(per_class.items())},
        "latency_p50": pct(lat, 0.50), "latency_p95": p95,
        "usd_per_1k": c1k, "efficiency_score": es,
        "attempts_used": len(lat),
    }
