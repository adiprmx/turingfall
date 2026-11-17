from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from turingfall.core.result import Result, Status, Code
from turingfall.core.registry import solver

N, K, INK, MIN_CONF = 16, 3, 150, 0.72

def _feat(img: Image.Image) -> list[int]:
    g = ImageOps.autocontrast(img.convert("L")).point(lambda v: 0 if v < INK else 255)
    bbox = g.getbbox() or (0, 0, g.width, g.height)
    small = g.crop(bbox).resize((N, N), Image.BILINEAR).point(lambda v: 0 if v < 128 else 1)
    return list(small.getdata())

@solver
class TextCV:
    name = "text_cv"
    manifest = {"usd_per_1k": 0.0, "needs": ["pillow", "model"], "classes": "A", "keyless": True}

    def __init__(self, model: Path | str = "models/knn-v0.json") -> None:
        raw = json.loads(Path(model).read_text())
        self.bank = [(r["label"], r["f"]) for r in raw["glyphs"]]
        self.base = Path(raw["base"])

    def _split(self, img: Image.Image) -> list[Image.Image]:
        g = ImageOps.autocontrast(img.convert("L")).point(lambda v: 0 if v < INK else 255)
        w, h, px = *g.size, g.load()
        ink = [sum(1 for y in range(h) if px[x, y] == 0) for x in range(w)]
        runs, cur = [], None
        for x, c in enumerate(ink + [0]):
            if c and cur is None:
                cur = x
            elif not c and cur is not None:
                if x - cur >= 2:
                    runs.append((cur, x))
                cur = None
        boxes = []
        for a, b in runs:
            if boxes and a - boxes[-1][1] < 4:
                boxes[-1] = (boxes[-1][0], b)
            else:
                boxes.append((a, b))
        return [g.crop((max(0, a - 1), 0, min(w, b + 1), h)) for a, b in boxes]

    def solve(self, ch) -> Result:
        segs = self._split(Image.open(self.base / ch.payload["image"]))
        if not 3 <= len(segs) <= 8:
            return Result.abstain(f"segmentasi {len(segs)} di luar 3..8")
        out, conf = [], []
        for seg in segs:
            f = _feat(seg)
            near = sorted((sum(a ^ b for a, b in zip(f, bf)), lb) for lb, bf in self.bank)[:K]
            votes: dict[str, int] = {}
            for _, lb in near:
                votes[lb] = votes.get(lb, 0) + 1
            out.append(max(votes, key=votes.get))
            conf.append(1 - near[0][0] / (N * N))
        c = sum(conf) / len(conf)
        if c < MIN_CONF:
            return Result.abstain(f"conf {c:.2f} < {MIN_CONF}", confidence=c)
        return Result(Status.SOLVED, "text", "".join(out), c, trace={"segments": len(segs)})
