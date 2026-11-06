"""Build res/glythminis.ico from the project's own 5x7 'G' bitmap.

Run with a Python that has Pillow:
    python tools/make_icon.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from glythminis.glyphs import FONT  # noqa: E402

BG = (0, 0, 0, 255)
INK = (242, 242, 242, 255)
FRAME = (255, 43, 61, 255)

SIZE = 256
MARGIN = 26
GLYPH = FONT["G"]
COLS, ROWS = len(GLYPH[0]), len(GLYPH)


def build():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    # hairline frame, like the app's own window chrome
    draw.rectangle([6, 6, SIZE - 7, SIZE - 7], outline=FRAME, width=3)

    cell = min((SIZE - 2 * MARGIN) // COLS, (SIZE - 2 * MARGIN) // ROWS)
    w, h = cell * COLS, cell * ROWS
    x0 = (SIZE - w) // 2
    y0 = (SIZE - h) // 2

    for y, row in enumerate(GLYPH):
        for x, ch in enumerate(row):
            if ch == "#":
                draw.rectangle(
                    [x0 + x * cell, y0 + y * cell,
                     x0 + (x + 1) * cell - 1, y0 + (y + 1) * cell - 1],
                    fill=INK,
                )
    return img


def main():
    out = ROOT / "res" / "glythminis.ico"
    out.parent.mkdir(exist_ok=True)
    img = build()
    img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.save(ROOT / "res" / "glythminis.png")
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
