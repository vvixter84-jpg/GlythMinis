"""A tiny 5x7 ASCII-art font and the renderer that turns it into big block text.

One bitmap, many "fonts": a style decides which character fills a pixel, how
many character cells wide a pixel is and whether the glyph is hollow, shaded or
shadowed.  That is how GLYTHMINIS gets twelve looks out of a single typeface.

The font covers A-Z, 0-9, punctuation, and Cyrillic uppercase (so a Russian
keyboard can be typed into YOUR TEXT).
"""

# Each glyph is seven rows of five cells, '#' is ink.  Rows are separated by
# '|' so the source stays readable and trailing spaces stay visible.
_RAW = {
    "A": "  #  | # # |#   #|#   #|#####|#   #|#   #",
    "B": "#### |#   #|#   #|#### |#   #|#   #|#### ",
    "C": " ### |#   #|#    |#    |#    |#   #| ### ",
    "D": "#### |#   #|#   #|#   #|#   #|#   #|#### ",
    "E": "#####|#    |#    |#### |#    |#    |#####",
    "F": "#####|#    |#    |#### |#    |#    |#    ",
    "G": " ### |#   #|#    |#  ##|#   #|#   #| ### ",
    "H": "#   #|#   #|#   #|#####|#   #|#   #|#   #",
    "I": " ### |  #  |  #  |  #  |  #  |  #  | ### ",
    "J": "  ###|   # |   # |   # |   # |#  # | ##  ",
    "K": "#   #|#  # |# #  |##   |# #  |#  # |#   #",
    "L": "#    |#    |#    |#    |#    |#    |#####",
    "M": "#   #|## ##|# # #|# # #|#   #|#   #|#   #",
    "N": "#   #|##  #|# # #|#  ##|#   #|#   #|#   #",
    "O": " ### |#   #|#   #|#   #|#   #|#   #| ### ",
    "P": "#### |#   #|#   #|#### |#    |#    |#    ",
    "Q": " ### |#   #|#   #|#   #|# # #|#  # | ## #",
    "R": "#### |#   #|#   #|#### |# #  |#  # |#   #",
    "S": " ####|#    |#    | ### |    #|    #|#### ",
    "T": "#####|  #  |  #  |  #  |  #  |  #  |  #  ",
    "U": "#   #|#   #|#   #|#   #|#   #|#   #| ### ",
    "V": "#   #|#   #|#   #|#   #|#   #| # # |  #  ",
    "W": "#   #|#   #|#   #|# # #|# # #|## ##|#   #",
    "X": "#   #|#   #| # # |  #  | # # |#   #|#   #",
    "Y": "#   #|#   #| # # |  #  |  #  |  #  |  #  ",
    "Z": "#####|    #|   # |  #  | #   |#    |#####",
    "0": " ### |#   #|#  ##|# # #|##  #|#   #| ### ",
    "1": "  #  | ##  |  #  |  #  |  #  |  #  | ### ",
    "2": " ### |#   #|    #|   # |  #  | #   |#####",
    "3": "#####|   # |  ## |    #|    #|#   #| ### ",
    "4": "   # |  ## | # # |#  # |#####|   # |   # ",
    "5": "#####|#    |#### |    #|    #|#   #| ### ",
    "6": "  ## | #   |#    |#### |#   #|#   #| ### ",
    "7": "#####|    #|   # |  #  | #   | #   | #   ",
    "8": " ### |#   #|#   #| ### |#   #|#   #| ### ",
    "9": " ### |#   #|#   #| ####|    #|   # | ##  ",
    " ": "     |     |     |     |     |     |     ",
    ".": "     |     |     |     |     | ##  | ##  ",
    ",": "     |     |     |     |  ## |  ## | #   ",
    ":": "     |  ## |  ## |     |  ## |  ## |     ",
    ";": "     |  ## |  ## |     |  ## |  ## | #   ",
    "!": "  #  |  #  |  #  |  #  |  #  |     |  #  ",
    "?": " ### |#   #|    #|   # |  #  |     |  #  ",
    "'": "  #  |  #  |     |     |     |     |     ",
    '"': " # # | # # |     |     |     |     |     ",
    "-": "     |     |     |#####|     |     |     ",
    "+": "     |  #  |  #  |#####|  #  |  #  |     ",
    "=": "     |     |#####|     |#####|     |     ",
    "/": "    #|    #|   # |  #  | #   |#    |#    ",
    "\\": "#    |#    | #   |  #  |   # |    #|    #",
    "(": "   # |  #  | #   | #   | #   |  #  |   # ",
    ")": " #   |  #  |   # |   # |   # |  #  | #   ",
    "[": " ### | #   | #   | #   | #   | #   | ### ",
    "]": " ### |   # |   # |   # |   # |   # | ### ",
    "<": "   # |  #  | #   |#    | #   |  #  |   # ",
    ">": " #   |  #  |   # |    #|   # |  #  | #   ",
    "*": "     | # # |  #  |#####|  #  | # # |     ",
    "#": " # # | # # |#####| # # |#####| # # | # # ",
    "@": " ### |#   #|# ###|# # #|# ###|#    | ### ",
    "%": "##   |##  #|   # |  #  | #   |#  ##|   ##",
    "&": " ##  |#  # |# #  | #   |# # #|#  # | ## #",
    "_": "     |     |     |     |     |     |#####",
    "|": "  #  |  #  |  #  |  #  |  #  |  #  |  #  ",
    "^": "  #  | # # |#   #|     |     |     |     ",
    "~": "     |     | ## #|# ## |     |     |     ",
    "$": "  #  | ####|# #  | ### |  # #|#### |  #  ",
    # Cyrillic uppercase.
    "Б": "#####|#    |#    |#### |#   #|#   #|#### ",
    "Г": "#####|#    |#    |#    |#    |#    |#    ",
    "Д": " ### | #  #| #  #| #  #| #  #|#####|#   #",
    "Ё": "#####|#    |#    |#### |#    |#    |#####",
    "Ж": "# # #|# # #|# # #| ### |# # #|# # #|# # #",
    "З": " ### |#   #|    #|  ## |    #|#   #| ### ",
    "И": "#   #|#   #|#  ##|# # #|##  #|#   #|#   #",
    "Й": "#   #|#   #|#  ##|# # #|##  #|#   #|#   #",
    "Л": "  ###|  # #|  # #| #  #| #  #| #  #|#   #",
    "П": "#####|#   #|#   #|#   #|#   #|#   #|#   #",
    "У": "#   #|#   #|#   #| ####|    #|   # | ##  ",
    "Ф": " ### |  #  | ####|# # #|# # #| ####|  #  ",
    "Ц": "#   #|#   #|#   #|#   #|#   #|#####|    #",
    "Ч": "#   #|#   #|#   #| ####|    #|    #|    #",
    "Ш": "# # #|# # #|# # #|# # #|# # #|# # #|#####",
    "Щ": "# # #|# # #|# # #|# # #|# # #|#####|    #",
    "Ъ": "##   | #   | #   | ### | #  #| #  #| ### ",
    "Ы": "#   #|#   #|#   #|### #|#  ##|#   #|### #",
    "Ь": "#    |#    |#    |###  |#  # |#  # |###  ",
    "Э": " ### |#   #|    #|  ###|    #|#   #| ### ",
    "Ю": "#  ##|# #  |# #  |###  |# #  |# #  |#  ##",
    "Я": " ####|#   #|#   #| ####|  # #| #  #|#   #",
}
_RAW["А"] = _RAW["A"]
_RAW["В"] = _RAW["B"]
_RAW["Е"] = _RAW["E"]
_RAW["К"] = _RAW["K"]
_RAW["М"] = _RAW["M"]
_RAW["Н"] = _RAW["H"]
_RAW["О"] = _RAW["O"]
_RAW["Р"] = _RAW["P"]
_RAW["С"] = _RAW["C"]
_RAW["Т"] = _RAW["T"]
_RAW["Х"] = _RAW["X"]

W, H = 5, 7
GAP = 1  # blank bitmap columns between letters


def _parse(raw):
    glyphs = {}
    for char, spec in raw.items():
        rows = spec.split("|")
        if len(rows) != H:
            raise ValueError(f"glyph {char!r}: {len(rows)} rows, expected {H}")
        fixed = []
        for row in rows:
            if len(row) > W:
                raise ValueError(f"glyph {char!r}: row {row!r} is wider than {W}")
            fixed.append(row.ljust(W))
        glyphs[char] = tuple(fixed)
    return glyphs


FONT = _parse(_RAW)
FALLBACK = FONT["?"]


def glyph_for(char):
    """Look a character up, case-insensitively, with a safe fallback."""
    return FONT.get(char) or FONT.get(char.upper()) or FALLBACK


# --------------------------------------------------------------------------
# Styles: one bitmap, twelve looks.
# --------------------------------------------------------------------------
STYLES = (
    # name,      fill,  h-scale, options
    ("SOLID",    "█", 2, {}),
    ("FAT",      "█", 3, {}),
    ("SCAN",     "▀", 2, {}),
    ("OUTLINE",  "█", 2, {"outline": True}),
    ("SHADOW",   "█", 2, {"shadow": True}),
    ("GRADIENT", None, 2, {"grad": "██▓▓▒▒░"}),
    ("HATCH",    "#", 2, {}),
    ("AT",       "@", 2, {}),
    ("STAR",     "*", 2, {}),
    ("SHADE",    "▒", 2, {}),
    ("DOTS",     "░", 2, {}),
    ("CIRCLES",  "●", 2, {"cell": "● "}),
    ("RINGS",    "○", 2, {"cell": "○ "}),
    ("PLUS",     "+", 2, {}),
)

STYLE_NAMES = tuple(s[0] for s in STYLES)
_BY_NAME = {s[0]: s for s in STYLES}

# Used for the logo / boot banner: same block look, double height for weight.
_LOGO = ("LOGO", "█", 2, {"v": 2})


def _bitmap_line(text):
    """Return (width, height, set-of-ink-cells) for one line at 1:1 scale."""
    cells = set()
    x0 = 0
    for char in text:
        rows = glyph_for(char)
        for y in range(H):
            for x in range(W):
                if rows[y][x] == "#":
                    cells.add((x0 + x, y))
        x0 += W + GAP
    width = max(1, x0 - GAP)
    return width, H, cells


def _outline(cells, w, h):
    edge = set()
    for (x, y) in cells:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in cells:
                edge.add((x, y))
                break
    return edge


def _render_line(text, style):
    name, fill, hscale, opts = style
    vscale = opts.get("v", 1)
    grad = opts.get("grad")
    cell_ink = opts.get("cell")  # replace "fill * hscale" with a literal cell

    width, height, cells = _bitmap_line(text)
    if opts.get("outline"):
        cells = _outline(cells, width, height)

    shadow = set()
    if opts.get("shadow"):
        shadow = {(x + 1, y + 1) for (x, y) in cells}

    rows = []
    for y in range(height):
        line = []
        for x in range(width):
            if (x, y) in cells:
                if cell_ink is not None:
                    line.append(cell_ink)
                else:
                    ch = fill
                    if grad is not None:
                        ch = grad[min(len(grad) - 1, int(y * len(grad) / height))]
                    line.append(ch * hscale)
            elif (x, y) in shadow:
                line.append("░" * hscale)
            else:
                line.append(" " * hscale)
        rendered = "".join(line)
        for _ in range(vscale):
            rows.append(rendered)
    return rows


def render(text, style_name, logo=False):
    """Render text into a list of equal-width strings of ASCII-art."""
    style = _LOGO if logo else _BY_NAME.get(style_name, _BY_NAME["SOLID"])
    lines = str(text).split("\n")
    out = []
    for index, line in enumerate(lines):
        if index:
            out.append(" ")
        if not line:
            out.append(" ")
            continue
        out.extend(_render_line(line, style))
    out = out or [" "]
    width = max(len(line) for line in out)
    return [line.ljust(width) for line in out]


def measure(text, style_name, logo=False):
    art = render(text, style_name, logo=logo)
    return max(len(line) for line in art), len(art)


# --------------------------------------------------------------------------
# Display face for the wordmark.
#
# The 5x7 face is a text face: stretched to banner size its letters turn into
# narrow stencils (the G, S and M in particular).  The wordmark therefore gets
# its own wide 12x7 alphabet - one cell of ink, real bowls and a symmetric M -
# which reads as a proper logotype when it is blown up to 800 px.
# --------------------------------------------------------------------------
LOGO_W, LOGO_H, LOGO_GAP = 12, 7, 2

LOGO_FONT = {
    "G": (
        "  ████████  ",
        " ██      ██ ",
        "██          ",
        "██          ",
        "██      ████",
        " ██      ██ ",
        "  ████████  ",
    ),
    "L": (
        "██          ",
        "██          ",
        "██          ",
        "██          ",
        "██          ",
        "██          ",
        "██████████  ",
    ),
    "Y": (
        "██        ██",
        "██        ██",
        " ██      ██ ",
        "  ██    ██  ",
        "   ██████   ",
        "     ██     ",
        "     ██     ",
    ),
    "T": (
        "████████████",
        "     ██     ",
        "     ██     ",
        "     ██     ",
        "     ██     ",
        "     ██     ",
        "     ██     ",
    ),
    "H": (
        "██        ██",
        "██        ██",
        "██        ██",
        "████████████",
        "██        ██",
        "██        ██",
        "██        ██",
    ),
    "M": (
        "██        ██",
        "███      ███",
        "████    ████",
        "██ ██  ██ ██",
        "██  ████  ██",
        "██        ██",
        "██        ██",
    ),
    "I": (
        "  ████████  ",
        "     ██     ",
        "     ██     ",
        "     ██     ",
        "     ██     ",
        "     ██     ",
        "  ████████  ",
    ),
    "N": (
        "██        ██",
        "███       ██",
        "████      ██",
        "██ ██     ██",
        "██  ███   ██",
        "██    ███ ██",
        "██        ██",
    ),
    "S": (
        "  ████████  ",
        " ██      ██ ",
        " ██         ",
        "  ████████  ",
        "         ██ ",
        " ██      ██ ",
        "  ████████  ",
    ),
    " ": (
        "            ",
        "            ",
        "            ",
        "            ",
        "            ",
        "            ",
        "            ",
    ),
}


def render_logo(text):
    """Lay the wide display face out; returns LOGO_H equal-width strings."""
    rows = ["" for _ in range(LOGO_H)]
    text = str(text).upper()
    for index, char in enumerate(text):
        glyph = LOGO_FONT.get(char)
        if glyph is None:
            continue
        gap = " " * LOGO_GAP if index < len(text) - 1 else ""
        for y in range(LOGO_H):
            rows[y] += glyph[y] + gap
    width = max(len(row) for row in rows)
    return [row.ljust(width) for row in rows]

