from __future__ import annotations
import argparse, json, time
from pathlib import Path
from turingfall.core.challenge import Challenge, Class
from turingfall.core.registry import SOLVERS, load_builtin
from turingfall.core.scoring import summarize

def _load(corpus: Path) -> list[Challenge]:
    return [Challenge(r["id"], r["family"], Class(r["cls"]), r["payload"], r.get("truth"), r.get("meta", {}))
            for r in map(json.loads, (corpus / "challenges.jsonl").read_text().splitlines()) if r]

def _md(name: str, s: dict, att: int) -> str:
    lo, hi = s["ci95"]
    return (f"| `{name}` | {s['per_challenge']:.3f} [{lo:.3f}, {hi:.3f}] | "
            f"**{s[f'per_session_at_{att}']:.3f}** | {s['n']} | {s['latency_p50']:.3f}s | "
            f"${s['usd_per_1k']:.2f} | {s['efficiency_score']:.1f} |")

def main(argv=None) -> int:
    load_builtin()
    ap = argparse.ArgumentParser(prog="tf")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("synth"); s.add_argument("--n", type=int, default=200)
    s.add_argument("--out", type=Path, required=True); s.add_argument("--seed", type=int, default=0)

    t = sub.add_parser("train"); t.add_argument("--glyphs", type=Path, required=True)
    t.add_argument("--out", type=Path, default=Path("models/knn-v0.json"))

    b = sub.add_parser("bench"); b.add_argument("--corpus", type=Path, required=True)
    b.add_argument("--solver", required=True); b.add_argument("--attempts", type=int, default=3)
    b.add_argument("--limit", type=int, default=0); b.add_argument("--md", action="store_true")
    b.add_argument("--model", type=Path, default=Path("models/knn-v0.json"))

    a = ap.parse_args(argv)

    if a.cmd == "synth":
        from turingfall.synth import build
        build(a.out, a.n, a.seed); print(f"corpus -> {a.out} ({a.n})"); return 0

    if a.cmd == "train":
        from turingfall.solvers.classical_ocr import ClassicalOCR
        ClassicalOCR().fit(a.glyphs, a.glyphs.parent, a.out); print(f"model -> {a.out}"); return 0

    if a.cmd == "bench":
        cls = SOLVERS[a.solver]
        sv = cls(a.model) if a.solver == "classical_ocr" else cls()
        items = _load(a.corpus)[: a.limit or None]
        recs = []
        for ch in items:
            for att in range(1, a.attempts + 1):
                t0 = time.perf_counter()
                ans = sv.solve(ch)
                dt = time.perf_counter() - t0
                recs.append({"challenge_id": ch.id, "family": ch.family, "cls": ch.cls.value,
                             "attempt": att, "correct": ans.value == ch.truth,
                             "latency_s": dt, "cost_usd": sv.manifest["usd_per_1k"] / 1000})
                if ans.value == ch.truth:
                    break
        s = summarize(recs, a.attempts)
        out = Path("bench/results"); out.mkdir(parents=True, exist_ok=True)
        (out / f"{a.solver}-{a.corpus.name}.json").write_text(json.dumps({"summary": s, "records": recs}, indent=1))
        if a.md:
            p = Path("RESULTS.md")
            head = ("# Results\n\nCorpus: `%s`. Metrik: `docs/METRICS.md`. Angka tanpa corpus terpin = kosong.\n\n"
                    "| solver | per-challenge [CI95] | per-session | n | p50 | $/1k | ES |\n|---|---|---|---|---|---|---|\n"
                    % a.corpus.name)
            p.write_text(head + _md(a.solver, s, a.attempts) + "\n")
        print(json.dumps(s, indent=1))
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
