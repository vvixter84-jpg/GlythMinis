"""Procedural ASCII eyeballs.

An eye is not a pile of hand-drawn frames: it is an ellipse traced into a
character grid, clipped by an eyelid at a given openness, with a pupil drawn
inside it.  One function therefore produces every blink stage, every pupil
position and several eye "species" without any art files.
"""

import math


class Grid:
    """Character grid with two layers: the eye itself and its coloured core."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.cells = [[" "] * w for _ in range(h)]
        self.core = [[" "] * w for _ in range(h)]

    def set(self, x, y, ch, core=False):
        x = int(round(x))
        y = int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = ch
            if core:
                self.core[y][x] = ch

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.cells[y][x]
        return " "

    def outline_lines(self):
        return [
            "".join(" " if self.core[y][x] != " " else ch for x, ch in enumerate(row))
            for y, row in enumerate(self.cells)
        ]

    def core_lines(self):
        return ["".join(row) for row in self.core]


def _inside(x, y, cx, cy, rx, ry):
    if rx <= 0 or ry <= 0:
        return False
    dx = (x - cx) / rx
    dy = (y - cy) / ry
    return dx * dx + dy * dy <= 1.0


def _ellipse_outline(g, cx, cy, rx, ry, y_min=None, y_max=None):
    """Trace an ellipse and pick each glyph from the step to the next cell.

    One sample per cell along the perimeter, and the character comes from the
    direction of travel instead of the tangent - that is what keeps the stroke
    connected instead of turning it into a dotted line.
    """
    perimeter = 2.0 * math.pi * math.sqrt((rx * rx + ry * ry) / 2.0)
    steps = max(48, int(perimeter))
    cells = []
    for i in range(steps + 1):
        a = 2.0 * math.pi * i / steps
        fy = cy + ry * math.sin(a)
        if y_min is not None and fy < y_min - 0.55:
            continue
        if y_max is not None and fy > y_max + 0.55:
            continue
        cells.append((int(round(cx + rx * math.cos(a))), int(round(fy))))
    for (x, y), (nx, ny) in zip(cells, cells[1:] + cells[:1]):
        dx = nx - x
        dy = ny - y
        if dx == 0 and dy == 0:
            continue
        if abs(dx) > 1 or abs(dy) > 1:
            span = max(abs(dx), abs(dy))
            ch = "─" if abs(dx) > abs(dy) else "│"
            for k in range(1, span):
                g.set(x + round(dx * k / span), y + round(dy * k / span), ch)
        elif dx and dy:
            ch = "╲" if dx * dy > 0 else "╱"
        elif dx:
            ch = "─"
        else:
            ch = "│"
        g.set(x, y, ch)


def _rect_outline(g, x0, y0, x1, y1):
    for x in range(int(x0) + 1, int(x1)):
        g.set(x, y0, "─")
        g.set(x, y1, "─")
    for y in range(int(y0) + 1, int(y1)):
        g.set(x0, y, "│")
        g.set(x1, y, "│")
    g.set(x0, y0, "┌")
    g.set(x1, y0, "┐")
    g.set(x0, y1, "└")
    g.set(x1, y1, "┘")


def _fill_ellipse(g, cx, cy, rx, ry, ch, clip=None, aperture=None, core=False):
    for y in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
        if aperture is not None and not (aperture[0] <= y <= aperture[1]):
            continue
        for x in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
            if not _inside(x, y, cx, cy, rx, ry):
                continue
            if clip is not None and not _inside(x, y, *clip):
                continue
            g.set(x, y, ch, core=core)


def _line(g, x0, y0, x1, y1):
    """Draw a connected line, one cell per column (or per row when steep).

    A character cell is ~2x taller than wide, so a visually 45-degree line is
    two cells right for one row down; stepping per column keeps the stair-step
    pattern regular instead of producing stray '|' pixels.
    """
    x0, y0 = int(round(x0)), int(round(y0))
    x1, y1 = int(round(x1)), int(round(y1))
    if abs(x1 - x0) >= abs(y1 - y0):
        step = 1 if x1 >= x0 else -1
        span = abs(x1 - x0)
        prev_y = y0
        for i in range(span + 1):
            x = x0 + i * step
            y = y0 if span == 0 else int(round(y0 + (y1 - y0) * i / span))
            if y == prev_y:
                g.set(x, y, "-")
            else:
                g.set(x, y, "\\" if (y - prev_y) * step > 0 else "/")
            prev_y = y
    else:
        step = 1 if y1 >= y0 else -1
        span = abs(y1 - y0)
        prev_x = x0
        for i in range(span + 1):
            y = y0 + i * step
            x = x0 if span == 0 else int(round(x0 + (x1 - x0) * i / span))
            if x == prev_x:
                g.set(x, y, "|")
            else:
                g.set(x, y, "\\" if (x - prev_x) * step > 0 else "/")
            prev_x = x


def _cross(g, cx, cy):
    g.set(cx - 1, cy - 1, "\\", core=True)
    g.set(cx + 1, cy - 1, "/", core=True)
    g.set(cx, cy, "x", core=True)
    g.set(cx - 1, cy + 1, "/", core=True)
    g.set(cx + 1, cy + 1, "\\", core=True)


EYE_STYLES = {
    # prx/pry are in cells; a cell is ~2x taller than wide, so pry ~ prx / 2.
    "ROUND": dict(rx=15.0, ry=7.4, prx=4.4, pry=2.3, pupil="round"),
    "WIDE": dict(rx=16.5, ry=8.6, prx=3.8, pry=2.0, pupil="round", brow="raised"),
    "SLEEPY": dict(rx=15.0, ry=7.4, prx=4.4, pry=2.3, pupil="round", lid=0.55),
    "ANGRY": dict(rx=15.0, ry=7.2, prx=3.6, pry=1.9, pupil="round", brow="angry"),
    "CAT": dict(rx=15.0, ry=7.4, prx=1.1, pry=3.6, pupil="slit"),
    "ROBOT": dict(rx=14.0, ry=6.6, prx=2.0, pry=2.0, pupil="scan", square=True),
    "LOVE": dict(rx=15.0, ry=7.4, prx=2.0, pry=2.0, pupil="heart"),
    "DIZZY": dict(rx=15.0, ry=7.4, prx=2.0, pry=2.0, pupil="cross"),
}

EYE_NAMES = tuple(EYE_STYLES)


def eye_metrics(style_name):
    st = EYE_STYLES.get(style_name, EYE_STYLES["ROUND"])
    rx, ry = st["rx"], st["ry"]
    gap = int(rx * 0.75)
    return int(round(4 * rx)) + gap + 4, int(round(2 * ry)) + 8


def eye_frame(style_name, openness, look, t=0.0):
    """Return the pair of eyes as a list of equal-width strings.

    openness: 1.0 = wide open, 0.0 = shut.
    look: (dx, dy) in -1..1 - where the pupils are pointing.
    t: seconds, used by the scanning robot eye.
    """
    st = EYE_STYLES.get(style_name, EYE_STYLES["ROUND"])
    rx, ry = st["rx"], st["ry"]
    prx, pry = st["prx"], st["pry"]
    kind = st["pupil"]
    square = st.get("square", False)
    lid_max = st.get("lid", 1.0)

    gap = int(rx * 0.75)
    pad_top = 5
    width = int(round(4 * rx)) + gap + 4
    height = int(round(2 * ry)) + pad_top + 3
    cy = pad_top + ry

    g = Grid(width, height)

    left_cx = 2 + rx
    right_cx = left_cx + 2 * rx + gap
    centers = (left_cx, right_cx)

    openness = max(0.0, min(1.0, openness)) * lid_max
    half = ry * openness
    top, bottom = cy - half, cy + half
    aperture = None
    if openness > 0.18:
        aperture = (int(math.ceil(top)), int(math.floor(bottom)))

    for index, cx in enumerate(centers):
        mirror = index == 1

        brow = st.get("brow")
        if brow == "raised" and not square:
            _line(g, cx - rx + 2, cy - ry - 2, cx + rx - 2, cy - ry - 2)
            g.set(cx - rx + 1, cy - ry - 3, "/")
            g.set(cx + rx - 1, cy - ry - 3, "\\")
        elif brow == "angry" and not square:
            if mirror:
                _line(g, cx - rx + 2, cy - ry - 1.4, cx + rx - 1, cy - ry - 3.4)
            else:
                _line(g, cx - rx + 1, cy - ry - 3.4, cx + rx - 2, cy - ry - 1.4)

        if openness <= 0.18:
            # Shut: one soft lash line.
            y = int(round(cy))
            for x in range(int(cx - rx) + 3, int(cx + rx) - 2):
                g.set(x, y, "_")
            g.set(int(cx - rx) + 2, y - 1, "/")
            g.set(int(cx + rx) - 2, y - 1, "\\")
            continue

        if square:
            _rect_outline(g, int(cx - rx), int(cy - half), int(cx + rx), int(cy + half))
        elif openness >= 0.4:
            # Below that the ellipse degenerates into a scratchy "H" shape, so
            # a nearly shut eye is just its two lids.
            _ellipse_outline(g, cx, cy, rx, ry, top, bottom)

        if kind == "scan":
            sweep = math.sin(t * 1.9) * max(0.0, rx - 2.4)
            bx = int(round(cx + sweep))
            for y in range(int(math.ceil(top)) + 1, int(math.floor(bottom))):
                g.set(bx, y, "█", core=True)
                g.set(bx - 1, y, "░", core=True)
            continue

        pupil_cx = cx + look[0] * max(0.0, rx - prx - 3.0)
        pupil_cy = cy + look[1] * max(0.0, ry - pry - 1.8)

        if kind == "heart":
            g.set(int(round(pupil_cx)) - 1, int(round(pupil_cy)), "<", core=True)
            g.set(int(round(pupil_cx)), int(round(pupil_cy)), "3", core=True)
            continue

        if kind == "cross":
            _cross(g, int(round(cx)), int(round(cy)))
            continue

        if kind == "slit":
            prx = 1.1
            pupil_cx = cx

        clip = (cx, cy, rx - 1.6, ry - 1.3)
        if kind != "slit":
            # Iris: a thin dithered ring around the pupil gives the eye depth
            # without swallowing the white.
            _fill_ellipse(g, pupil_cx, pupil_cy, prx + 1.3, pry + 1.0, "░",
                          clip=clip, aperture=aperture, core=True)
        _fill_ellipse(g, pupil_cx, pupil_cy, prx, pry, "█",
                      clip=clip, aperture=aperture, core=True)

        if kind != "slit":
            # Catch-light: one blank cell inside the pupil.
            hx = int(round(pupil_cx - prx * 0.5))
            hy = int(round(pupil_cy - pry * 0.4))
            if all(g.get(hx + dx, hy + dy) == "█"
                   for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, 1), (0, -1))):
                g.set(hx, hy, " ", core=True)

        # Eyelid: the line the lid closes along.
        if openness < 0.97:
            for y in (int(math.ceil(top)), int(math.floor(bottom))):
                dy = (y - cy) / ry
                chord = rx * math.sqrt(max(0.0, 1 - dy * dy))
                for x in range(int(round(cx - chord)) + 1, int(round(cx + chord))):
                    g.set(x, y, "─")

    return g.outline_lines(), g.core_lines()
