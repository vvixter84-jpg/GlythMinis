"""Console sanity check for the glyph engine - no GUI needed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from glythminis import glyphs

print("glyphs:", len(glyphs.FONT))

art = glyphs.render("ABC 019", "SOLID")
print("\n".join(art))

for style in glyphs.STYLE_NAMES:
    a = glyphs.render("GLYTH 12:30", style)
    w = {len(line) for line in a}
    print(f"{style:9s} rows={len(a):3d} widths={w}")

print("\n--- cyrillic ---")
print("\n".join(glyphs.render("ПРИВЕТ МИР", "OUTLINE")))

print("\n--- logo ---")
print("\n".join(glyphs.render("GLYTHMINIS", "SOLID", logo=True)))
