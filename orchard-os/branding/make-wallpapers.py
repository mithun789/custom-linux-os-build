#!/usr/bin/env python3
"""Generate Orchard OS wallpapers (original artwork) with Pillow.

Usage: make-wallpapers.py OUTDIR
Writes orchard-light.png, orchard-dark.png, orchard-dawn.png at 2560x1440.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 2560, 1440

PALETTES = {
    "orchard-light": {
        "bg": [(214, 240, 231), (190, 222, 245)],
        "waves": [(161, 226, 180, 170), (110, 200, 190, 150), (90, 160, 230, 130), (255, 255, 255, 90)],
    },
    "orchard-dark": {
        "bg": [(14, 22, 38), (22, 34, 58)],
        "waves": [(30, 120, 110, 170), (40, 90, 160, 150), (110, 70, 170, 120), (20, 30, 52, 200)],
        "glow": (90, 200, 170, 40),
    },
    "orchard-dawn": {
        "bg": [(255, 222, 200), (220, 200, 245)],
        "waves": [(255, 170, 140, 160), (240, 130, 170, 140), (150, 140, 230, 130), (255, 255, 255, 80)],
    },
}


def vertical_gradient(c1, c2):
    img = Image.new("RGB", (W, H), c1)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=col)
    return img


def wave_layer(color, base, amp, freq, phase):
    layer = Image.new("RGBA", (W, H), color[:3] + (0,))
    draw = ImageDraw.Draw(layer)
    pts = []
    for x in range(0, W + 8, 8):
        y = base + amp * math.sin(freq * x / W * 2 * math.pi + phase) \
            + amp * 0.35 * math.sin(freq * 2.3 * x / W * 2 * math.pi + phase * 1.7)
        pts.append((x, y))
    pts += [(W, H), (0, H)]
    draw.polygon(pts, fill=color)
    return layer.filter(ImageFilter.GaussianBlur(18))


def render(name, pal):
    img = vertical_gradient(*pal["bg"]).convert("RGBA")
    for i, col in enumerate(pal["waves"]):
        base = H * (0.42 + i * 0.12)
        layer = wave_layer(col, base, H * (0.10 - i * 0.012), 1.1 + i * 0.35, i * 1.3)
        img = Image.alpha_composite(img, layer)
    gcol = pal.get("glow", (255, 255, 255, 60))
    glow = Image.new("RGBA", (W, H), gcol[:3] + (0,))
    ImageDraw.Draw(glow).ellipse([W * 0.50, -H * 0.45, W * 1.20, H * 0.45], fill=gcol)
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(260)))
    return img.convert("RGB")


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    for name, pal in PALETTES.items():
        render(name, pal).save(out / f"{name}.png", optimize=True)
        print("wrote", out / f"{name}.png")


if __name__ == "__main__":
    main()
