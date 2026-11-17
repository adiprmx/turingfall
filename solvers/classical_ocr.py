from __future__ import annotations
import json, math
from pathlib import Path
from PIL import Image
from turingfall.core.challenge import Answer, Challenge
from turingfall.core.registry import solver

N, K, INK = 16, 3, 150

def _feat(img: Image.Image) -> list[int]:
    g = img.convert("L").point(lambda v: 0 if v < INK else 255)
    bbox = g.getbbox() or (0, 0, g.width, g.height)
    small = g.crop(bbox).resize((N, N), Image.BILINEAR).point(lambda v: 0 if v < 128 else 1)
    return list(small.getdata())

def _dist(a: list[int], b: list[int]) -> int:
    return sum(x ^ y for x, y in zip(a, b))

@solver
class ClassicalOCR:
    name = "classical_ocr"
    manifest = {"usd_per_1k": 0.0, "needs": ["pillow", "model"], "classes": "A"}

    def __init__(self, model: Path | str = "models/knn-v0.json") -> None:
        raw = json.loads(Path(model).read_text())
        self.bank = [(r["label"], r["f"]) for r in raw["glyphs"]]
        self.base = Path(raw["base"])

    def fit(self, glyphs: Path, base: Path, out: Path) -> None:
        rows = [{"label": g["label"], "f": _feat(Image.open(base / g["image"]))}
                for g in map(json.loads, glyphs.read_text().splitlines()) if g]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"base": str(base), "glyphs": rows}))

    def _split(self, img: Image.Image) -> list[Image.Image]:
        g = img.convert("L").point(lambda v: 0 if v < INK else 255)
        w, h = g.size
        px = g.load()
        ink = [sum(1 for y in range(h) if px[x, y] == 0) for x in range(w)]
        runs, cur = [], None
        for x, c in enumerate(ink + [0]):
            if c > 0 and cur is None:
                cur = x
            elif c == 0 and cur is not None:
                runs.append((cur, x))
                cur = None
        boxes, last = [], -99
        for a, b in runs:
            if b - a >= 2:
                if a - last < 4 and boxes:                 # gabung run berdekatan
                    boxes[-1] = (boxes[-1][0], b)
                else:
                    boxes.append((a, b))
                last = b
        return [g.crop((max(0, a - 1), 0, min(w, b + 1), h)) for a, b in boxes]

    def solve(self, ch: Challenge) -> Answer:
        img = Image.open(self.base / ch.payload["image"])
        out, conf = [], []
        for seg in self._split(img):
            f = _feat(seg)
            near = sorted(((_dist(f, bf), lb) for lb, bf in self.bank), key=lambda t: t[0])[:K]
            votes: dict[str, int] = {}
            for d, lb in near:
                votes[lb] = votes.get(lb, 0) + 1
            lb = max(votes, key=votes.get)
            out.append(lb)
            conf.append(1 - near[0][0] / (N * N))
        return Answer("".join(out), "text", sum(conf) / len(conf) if conf else 0.0,
                      {"segments": len(out)})
