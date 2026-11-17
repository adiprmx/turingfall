from __future__ import annotations
from PIL import Image, ImageFilter, ImageChops
from turingfall.core.result import Result, Status, Code

def _profile(img: Image.Image, box: tuple[int, int, int, int]) -> list[float]:
    g = img.convert("L").crop(box).filter(ImageFilter.FIND_EDGES)
    w, h = g.size
    px = g.load()
    return [sum(px[x, y] for y in range(h)) / h for x in range(w)]

def _ncc(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 4:
        return -1.0
    a, b = a[:n], b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else -1.0

def solve(bg: Image.Image, piece: Image.Image, y0: int, y1: int,
          search_from: int, search_to: int, min_conf: float = 0.35) -> Result:
    if search_to - search_from < 8 or y1 - y0 < 8:
        return Result(Status.FAILED, "offset_px", code=Code.INPUT)
    pw = piece.width
    tpl = _profile(piece, (0, 0, pw, piece.height))
    best, best_s = -1, -9.9
    for x in range(search_from, max(search_from + 1, search_to - pw)):
        s = _ncc(tpl, _profile(bg, (x, y0, x + pw, y1)))
        if s > best_s:
            best, best_s = x, s
    if best_s < min_conf:
        return Result.abstain(f"ncc {best_s:.2f} < {min_conf}", kind="offset_px",
                              confidence=max(0.0, best_s))
    return Result(Status.SOLVED, "offset_px", str(best), min(1.0, best_s),
                  trace={"ncc": round(best_s, 3)})
