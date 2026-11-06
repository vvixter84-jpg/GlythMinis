"""Palette and typography for GlythMinis.

Black glass, white ink, red only for accents: the active item, the numbers, the
live dot, the newborn cells.  Everything is drawn on one canvas with one
monospace font, so every colour is chosen per text item (or per layer).
"""

FONT_FAMILY = "Consolas"

# The user asked for a black background - keep it absolute.
BG = "#000000"

# White-to-grey ramp: index 0 means "nothing is drawn".
GHOST = "#0e0e0e"
FAINT = "#1f1f1f"
DIM = "#4a4a4a"
MID = "#7d7d7d"
SOFT = "#bdbdbd"
BRIGHT = "#f2f2f2"
HI = "#ffffff"

# Red accent ramp.
RED = "#ff2b3d"
RED_MID = "#c01020"
RED_DIM = "#6b0c16"
RED_FAINT = "#26060a"

# Every chamber shares the same accent now; the dict keeps the call sites tidy.
ACCENTS = {
    "menu": RED,
    "time": RED,
    "eyes": RED,
    "text": RED,
    "life": RED,
}

ACCENT_DIM = {
    "menu": RED_DIM,
    "time": RED_DIM,
    "eyes": RED_DIM,
    "text": RED_DIM,
    "life": RED_DIM,
}

VERSION = "1.1"

# Window: deliberately small and rectangular.
WIN_W = 980
WIN_H = 640

# Animation rates.
EYE_FPS = 20
LIFE_FPS = 11
