from __future__ import annotations
import json, os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
FONT_PATHS = (
    "/system/fonts/Roboto-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
)

def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.load_default(size)          # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()

def _deco(d: ImageDraw.ImageDraw, w: int, h: int, rng: random.Random, heavy: int) -> None:
    for _ in range(heavy):
        d.line(
            [(rng.randrange(w), rng.randrange(h)), (rng.randrange(w), rng.randrange(h))],
            fill=(rng.randrange(120, 200),) * 3, width=1,
        )
    for _ in range(heavy * 90):
        d.point((rng.randrange(w), rng.randrange(h)), fill=(rng.randrange(80, 210),) * 3)

def render_text(text: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    w, h = 200 + rng.randrange(40), 64 + rng.randrange(20)
    img = Image.new("L", (w, h), rng.randrange(232, 255))
    d = ImageDraw.Draw(img)
    _deco(d, w, h, rng, 2)
    x = 12
    for ch in text:
        g = Image.new("L", (56, 56), 255)
        gd = ImageDraw.Draw(g)
        gd.text((8, 4), ch, font=_font(rng.randrange(32, 44)), fill=rng.randrange(0, 60))
        g = g.rotate(rng.uniform(-24, 24), resample=Image.BILINEAR, fillcolor=255)
        img.paste(g.crop(g.getbbox() or (0, 0, 56, 56)), (x, rng.randrange(2, 12)))
        x += 28 + rng.randrange(6, 16)
    _deco(d, w, h, rng, 2)
    return img.filter(ImageFilter.SMOOTH)

def render_glyph(ch: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("L", (56, 56), 255)
    ImageDraw.Draw(img).text((8, 4), ch, font=_font(rng.randrange(28, 44)), fill=rng.randrange(0, 70))
    _deco(ImageDraw.Draw(img), 56, 56, rng, 1)
    return img.rotate(rng.uniform(-20, 20), resample=Image.BILINEAR, fillcolor=255)

def build(out: Path, n: int, seed: int = 0) -> None:
    rng = random.Random(seed)
    (out / "images").mkdir(parents=True, exist_ok=True)
    rows, glyphs = [], []
    for i in range(n):
        label = "".join(rng.choice(CHARS) for _ in range(rng.randrange(4, 7)))
        p = out / "images" / f"{i:05d}.png"
        render_text(label, seed * 100000 + i).save(p)
        rows.append({"id": f"synth-v0/{i:05d}", "family": "text-distort", "cls": "A",
                     "payload": {"image": str(p.relative_to(out))}, "truth": label,
                     "meta": {"generator": "turingfall.synth", "seed": seed}})
    for i, ch in enumerate(CHARS * 24):
        p = out / "images" / f"g{i:04d}.png"
        render_glyph(ch, seed * 7 + i).save(p)
        glyphs.append({"image": str(p.relative_to(out)), "label": ch})
    (out / "challenges.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (out / "glyphs.jsonl").write_text("\n".join(json.dumps(g) for g in glyphs) + "\n")
    (out / "manifest.json").write_text(json.dumps(
        {"corpus": "synth-v0", "version": "0.1.0", "n": n, "charset": CHARS,
         "created": "2026-11-17", "generator": "turingfall.synth", "license": "CC0-1.0"}, indent=2))
