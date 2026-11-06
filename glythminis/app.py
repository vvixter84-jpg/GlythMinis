"""GlythMinis - a small black box full of ASCII toys.

Boot screen -> menu with four chambers:

    01  TIME MODE   an ASCII clock with a dozen typefaces and six formats
    02  EYES MODE   procedural eyeballs that blink and follow the mouse
    03  YOUR TEXT   type anything, pick one of twelve ASCII fonts
    04  LIFE        Conway's Game of Life, drawn in blocks

Everything is text on a Tk canvas.
"""

from __future__ import annotations

import argparse
import ctypes
import math
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

from . import theme as T
from .eyes import EYE_NAMES, eye_frame, eye_metrics
from .glyphs import STYLE_NAMES, render, render_logo

APP_TITLE = f"GlythMinis {T.VERSION}"

MENU_ITEMS = (
    ("01", "TIME MODE", "ascii clock laboratory"),
    ("02", "EYES MODE", "they are watching"),
    ("03", "YOUR TEXT", "fourteen fonts, any words"),
    ("04", "LIFE", "conway's little universe"),
)

HOUR_WORDS = (
    "TWELVE", "ONE", "TWO", "THREE", "FOUR", "FIVE",
    "SIX", "SEVEN", "EIGHT", "NINE", "TEN", "ELEVEN",
)
MINUTE_WORDS = {
    0: "OCLOCK", 5: "FIVE", 10: "TEN", 15: "QUARTER", 20: "TWENTY",
    25: "TWENTY FIVE", 30: "HALF", 35: "THIRTY FIVE", 40: "FORTY",
    45: "QUARTER", 50: "FIFTY", 55: "FIFTY FIVE",
}


def _hour_words(hour):
    return HOUR_WORDS[hour % 12]


def _minute_words(minute):
    rounded = int(round(minute / 5.0)) * 5 % 60
    return MINUTE_WORDS.get(rounded, "OCLOCK")


TIME_FORMATS = (
    ("24H", lambda n: [f"{n:%H:%M:%S}"], lambda n: f"{n:%A %d %B %Y}"),
    ("24H SHORT", lambda n: [f"{n:%H:%M}"], lambda n: f"{n:%A %d %B %Y}"),
    ("12H", lambda n: [f"{n:%I:%M:%S}"], lambda n: f"{n:%p}  ·  {n:%A %d %B %Y}"),
    ("DATE", lambda n: [f"{n:%d.%m.%Y}"], lambda n: f"{n:%A}  ·  {n:%H:%M:%S}"),
    ("EPOCH", lambda n: [str(int(n.timestamp()))], lambda n: f"{n:%Y-%m-%d %H:%M:%S} local"),
    ("WORDS", lambda n: [_hour_words(n.hour), _minute_words(n.minute) or "OCLOCK"],
     lambda n: f"{n:%H:%M}  ·  {n:%A}"),
)

BOOT_LINES = (
    ("mounting ascii core", "OK"),
    ("loading 14 typefaces", "OK"),
    ("calibrating 8 eyeballs", "OK"),
    ("seeding 60 x 30 cells", "OK"),
    ("warming phosphor", "OK"),
)


class GlythMinis:
    def __init__(self, root: tk.Tk, screen: str | None = None, style: int | None = None,
                 fmt: int | None = None, eye: int | None = None, text: str | None = None):
        self.root = root
        self.W, self.H = T.WIN_W, T.WIN_H
        self.jobs: list[str] = []
        self.screen = ""
        self.key_handler = None
        self.pointer = (self.W // 2, self.H // 2)

        if style is not None:
            self.style_index = style % len(STYLE_NAMES)
            self.text_style = style % len(STYLE_NAMES)
        if fmt is not None:
            self.format_index = fmt % len(TIME_FORMATS)
        if eye is not None:
            self.eye_index = eye % len(EYE_NAMES)
        if text is not None:
            self.buffer = text[:60]

        root.title(APP_TITLE)
        root.configure(bg=T.BG)
        root.resizable(False, False)
        root.minsize(self.W, self.H)
        try:
            # One character cell must be exactly one design cell, otherwise the
            # ASCII art stops lining up on high-DPI displays.
            root.tk.call("tk", "scaling", 1.0)
        except Exception:
            pass
        self._center()

        self.canvas = tk.Canvas(root, bg=T.BG, highlightthickness=0, bd=0, takefocus=1)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.focus_set()

        self._metrics_cache: dict[int, tuple[tkfont.Font, int, int]] = {}
        self._dark_titlebar()

        root.protocol("WM_DELETE_WINDOW", self.quit)
        root.bind("<Key>", self._on_key)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Motion>", self._on_motion)

        if screen and screen in ("menu", "time", "eyes", "text", "life"):
            self.pointer = (self.W // 2, self.H // 2)
            getattr(self, f"show_{screen}")()
        else:
            self.show_boot()

    # ---------------------------------------------------------------- window
    def _center(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(self.W, sw - 60)
        h = min(self.H, sh - 100)
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - 24)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _dark_titlebar(self):
        try:
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
                )
        except Exception:
            pass

    def quit(self):
        self.clear_jobs()
        self.root.destroy()

    # ----------------------------------------------------------------- timing
    def later(self, ms, fn):
        job = self.root.after(ms, fn)
        self.jobs.append(job)
        return job

    def clear_jobs(self):
        for job in self.jobs:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        self.jobs.clear()

    def enter_screen(self, name, accent):
        self.clear_jobs()
        self.screen = name
        self.accent = accent
        self.accent_dim = T.ACCENT_DIM.get(name, T.FAINT)
        self.canvas.delete("all")
        self.canvas.configure(bg=T.BG)
        self._chrome()

    def _chrome(self):
        """Hairline frame, red corner brackets and a red tick in the corner."""
        self.canvas.create_rectangle(
            2, 2, self.W - 2, self.H - 2, outline=T.FAINT, width=1
        )
        arm, inset = 26, 2
        for x, y, sx, sy in (
            (inset, inset, 1, 1),
            (self.W - inset, inset, -1, 1),
            (inset, self.H - inset, 1, -1),
            (self.W - inset, self.H - inset, -1, -1),
        ):
            self.canvas.create_line(x, y, x + sx * arm, y, fill=T.RED_DIM, width=1)
            self.canvas.create_line(x, y, x, y + sy * arm, fill=T.RED_DIM, width=1)

    # ------------------------------------------------------------------ fonts
    def metrics(self, size):
        cached = self._metrics_cache.get(size)
        if cached is None:
            font = tkfont.Font(family=T.FONT_FAMILY, size=size)
            cached = (font, max(1, font.measure("M")), max(1, font.metrics("linespace")))
            self._metrics_cache[size] = cached
        return cached

    def fit(self, lines, max_w, max_h, lo=5, hi=96):
        cols = max(1, max((len(line) for line in lines), default=1))
        rows = max(1, len(lines))
        for size in range(hi, lo - 1, -1):
            font, cw, lh = self.metrics(size)
            if cols * cw <= max_w and rows * lh <= max_h:
                return font, cw, lh
        return self.metrics(lo)

    def art(self, lines, cx, cy, font, color, anchor="center", justify="center"):
        return self.canvas.create_text(
            cx, cy, text="\n".join(lines), font=font, fill=color,
            anchor=anchor, justify=justify,
        )

    def label(self, x, y, text, color, size=12, anchor="nw"):
        font, _, _ = self.metrics(size)
        return self.canvas.create_text(x, y, text=text, font=font, fill=color, anchor=anchor)

    def seg(self, x, y, parts, size=12, tags=()):
        """Draw a run of differently coloured strings on one baseline.

        The window uses a single monospace font, so advancing x by
        len(text)*cell keeps every segment on the same character grid.
        """
        font, cw, _ = self.metrics(size)
        for text, color in parts:
            if text:
                self.canvas.create_text(x, y, text=text, font=font, fill=color,
                                        anchor="nw", tags=tags)
            x += len(text) * cw
        return x

    def header(self, title, right=(), size=13):
        """● TITLE ─────────────── right side info."""
        font, cw, _ = self.metrics(size)
        self.seg(46, 22, [("● ", T.RED), (title, T.BRIGHT)], size)
        if right:
            total = sum(len(text) for text, _ in right)
            self.seg(self.W - 46 - total * cw, 22, list(right), size)
        self.canvas.create_line(46, 48, self.W - 46, 48, fill=T.FAINT)
        self.canvas.create_line(46, 48, 46 + (len(title) + 2) * cw, 48, fill=T.RED, width=2)

    def footer(self, parts, size=12):
        self.seg(46, self.H - 44, list(parts), size)

    def footer_right(self, parts, size=12):
        _, cw, _ = self.metrics(size)
        total = sum(len(text) for text, _ in parts)
        self.seg(self.W - 46 - total * cw, self.H - 44, list(parts), size)

    # ------------------------------------------------------------------ input
    def _on_key(self, event):
        if self.key_handler:
            self.key_handler(event)

    def _on_click(self, event):
        self.pointer = (event.x, event.y)
        if self.click_handler:
            self.click_handler(event)

    def _on_drag(self, event):
        self.pointer = (event.x, event.y)
        if self.drag_handler:
            self.drag_handler(event)

    def _on_motion(self, event):
        self.pointer = (event.x, event.y)
        self.last_motion = time.perf_counter()
        if self.motion_handler:
            self.motion_handler(event)

    click_handler = None
    drag_handler = None
    motion_handler = None

    # ================================================================ BOOT
    def show_boot(self):
        self.enter_screen("boot", T.ACCENTS["menu"])
        self.key_handler = lambda e: self.show_menu()
        self.click_handler = lambda e: self.show_menu()
        self.drag_handler = None
        self.motion_handler = None
        self.last_motion = 0.0

        logo = render_logo("GLYTH") + [""] + render_logo("MINIS")
        font, _, _ = self.fit(logo, self.W - 140, 300)
        item = self.art(logo, self.W // 2, 34, font, T.HI, anchor="n")
        logo_bottom = self.canvas.bbox(item)[3]

        self.label(self.W // 2, logo_bottom + 14, "a s c i i   t o y b o x", T.RED, 12, anchor="n")
        self.label(self.W // 2, logo_bottom + 38, f"version {T.VERSION}", T.DIM, 11, anchor="n")

        log_y = logo_bottom + 74
        self.boot_log = []
        self.boot_start = time.perf_counter()
        self.boot_stage = 0
        self.boot_text = self.label(150, log_y, "", T.SOFT, 12)
        self.boot_ok = self.label(150, log_y, "", T.RED, 12)
        self.boot_bar = self.label(self.W // 2, 524, "", T.FAINT, 13, anchor="center")
        self.boot_fill = self.label(self.W // 2, 524, "", T.RED, 13, anchor="center")
        self.boot_hint = self.label(self.W // 2, 570, "press any key", T.FAINT, 11, anchor="center")

        self.later(60, self._boot_tick)

    def _boot_tick(self):
        elapsed = time.perf_counter() - self.boot_start
        stage = min(len(BOOT_LINES), int(elapsed / 0.34) + 1)
        if stage != self.boot_stage:
            self.boot_stage = stage
        lines, marks = [], []
        for text, status in BOOT_LINES[:stage]:
            prefix = f"  > {text:<24}{'.' * 16} "
            lines.append(prefix + status)
            marks.append("  > " + " " * 41 + status)
        self.canvas.itemconfigure(self.boot_text, text="\n".join(lines))
        self.canvas.itemconfigure(self.boot_ok, text="\n".join(marks))

        progress = min(1.0, elapsed / 2.4)
        filled = int(round(progress * 34))
        bar = "[" + "░" * 34 + f"]  {int(progress * 100):3d}%"
        fill = " " + "█" * filled + " " * (34 - filled) + "     "
        self.canvas.itemconfigure(self.boot_bar, text=bar)
        self.canvas.itemconfigure(self.boot_fill, text=fill)

        if int(elapsed * 6) % 2 == 0:
            self.canvas.itemconfigure(self.boot_hint, fill=T.MID)
        else:
            self.canvas.itemconfigure(self.boot_hint, fill=T.FAINT)

        if elapsed >= 2.9:
            self.show_menu()
            return
        self.later(60, self._boot_tick)

    # ================================================================ MENU
    def show_menu(self):
        self.enter_screen("menu", T.ACCENTS["menu"])
        self.selected = getattr(self, "selected", 0)
        self.hover = -1
        self.key_handler = self._menu_key
        self.click_handler = self._menu_click
        self.motion_handler = self._menu_motion
        self.drag_handler = None

        logo = render_logo("GLYTHMINIS")
        font, _, _ = self.fit(logo, self.W - 130, 150)
        item = self.art(logo, self.W // 2, 26, font, T.HI, anchor="n")
        logo_bottom = self.canvas.bbox(item)[3]

        self.label(self.W // 2, logo_bottom + 20, "four small worlds in a black box",
                   T.MID, 12, anchor="n")
        rule_y = logo_bottom + 54
        self.canvas.create_line(46, rule_y, self.W - 46, rule_y, fill=T.FAINT)
        self.canvas.create_line(self.W // 2 - 60, rule_y, self.W // 2 + 60, rule_y,
                                fill=T.RED, width=2)

        self.buttons = []
        self._draw_buttons(rule_y + 26)

        counts = [
            ("14", T.RED_MID), (" TYPEFACES ", T.FAINT), ("·", T.DIM),
            (" 8", T.RED_MID), (" KINDS OF EYES ", T.FAINT), ("·", T.DIM),
            (" 6", T.RED_MID), (" TIME FORMATS ", T.FAINT), ("·", T.DIM),
            (" 63 x 33", T.RED_MID), (" CELLS", T.FAINT),
        ]
        total = sum(len(text) for text, _ in counts)
        self.seg((self.W - total * self.metrics(11)[1]) // 2, self.H - 94, counts, 11)
        self.canvas.create_line(46, self.H - 62, self.W - 46, self.H - 62, fill=T.FAINT)
        self.footer([("↑ ↓", T.RED), ("  choose     ", T.DIM),
                     ("ENTER", T.RED), ("  open     ", T.DIM),
                     ("1-4", T.RED), ("  direct     ", T.DIM),
                     ("Q", T.RED), ("  quit", T.DIM)])
        self.footer_right([("v" + T.VERSION, T.FAINT)])

    def _button_lines(self, index):
        num, label, subtitle = MENU_ITEMS[index]
        inner = 84
        left = f"{num}   {label}"
        right = subtitle
        gap = max(2, inner - len(left) - len(right))
        mid = "│ " + left + " " * gap + right + " │"
        width = len(mid)
        top = "┌" + "─" * (width - 2) + "┐"
        bottom = "└" + "─" * (width - 2) + "┘"
        return (top, mid, bottom), width

    def _draw_buttons(self, top=None):
        if top is not None:
            self.buttons_top = top
        top = getattr(self, "buttons_top", 240)
        self.canvas.delete("btn")
        font, cw, lh = self.metrics(15)
        total_h = 3 * lh
        gap = 14
        lines0, width = self._button_lines(0)
        box_w = width * cw
        x = (self.W - box_w) / 2
        block_h = 4 * total_h + 3 * gap
        free_bottom = self.H - 112
        start = top + max(0, (free_bottom - top - block_h) // 2)
        self.buttons = []

        for index in range(len(MENU_ITEMS)):
            y = start + index * (total_h + gap)
            selected = index == self.selected
            hovered = index == self.hover
            num, label, subtitle = MENU_ITEMS[index]

            if selected:
                self.canvas.create_rectangle(
                    x - 12, y - 6, x + box_w + 12, y + total_h + 6,
                    fill=T.RED_FAINT, outline="", tags=("btn",),
                )
                self.canvas.create_rectangle(
                    x - 12, y - 6, x - 9, y + total_h + 6,
                    fill=T.RED, outline="", tags=("btn",),
                )

            border = T.RED if selected else (T.RED_MID if hovered else T.FAINT)
            label_color = T.HI if (selected or hovered) else T.SOFT
            sub_color = T.MID if (selected or hovered) else T.DIM
            num_color = T.RED if (selected or hovered) else T.RED_DIM
            lines, _ = self._button_lines(index)

            self.canvas.create_text(
                x, y, text=lines[0], font=font, fill=border, anchor="nw", tags=("btn",))
            self.canvas.create_text(
                x, y + 2 * lh, text=lines[2], font=font, fill=border, anchor="nw", tags=("btn",))

            gap_chars = max(2, 84 - len(f"{num}   {label}") - len(subtitle))
            self.seg(x, y + lh, [
                ("│ ", border), (num, num_color), ("   ", label_color),
                (label, label_color), (" " * gap_chars, label_color),
                (subtitle, sub_color), (" │", border),
            ], 15)

            self.buttons.append((x - 12, y - 6, x + box_w + 12, y + total_h + 6))

    def _menu_key(self, event):
        key = event.keysym
        if key in ("Up", "w", "W"):
            self.selected = (self.selected - 1) % len(MENU_ITEMS)
            self._draw_buttons()
        elif key in ("Down", "s", "S"):
            self.selected = (self.selected + 1) % len(MENU_ITEMS)
            self._draw_buttons()
        elif key in ("Return", "KP_Enter", "space"):
            self._open(self.selected)
        elif key in "1234" and len(key) == 1:
            self._open(int(key) - 1)
        elif key in ("q", "Q", "Escape"):
            self.quit()

    def _menu_click(self, event):
        for index, (x0, y0, x1, y1) in enumerate(self.buttons):
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self.selected = index
                self._draw_buttons()
                self._open(index)
                return

    def _menu_motion(self, event):
        hovered = -1
        for index, (x0, y0, x1, y1) in enumerate(self.buttons):
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                hovered = index
                break
        if hovered != self.hover:
            self.hover = hovered
            self._draw_buttons()

    def _open(self, index):
        if index == 0:
            self.show_time()
        elif index == 1:
            self.show_eyes()
        elif index == 2:
            self.show_text()
        else:
            self.show_life()

    # ================================================================ TIME
    def show_time(self):
        self.enter_screen("time", T.ACCENTS["time"])
        self.style_index = getattr(self, "style_index", 0)
        self.format_index = getattr(self, "format_index", 0)
        self.frozen = False
        self.frozen_at = datetime.now()
        self.key_handler = self._time_key
        self.click_handler = None
        self.motion_handler = None
        self.drag_handler = None

        self.header("TIME MODE")
        self.time_item = self.canvas.create_text(
            self.W // 2, 292, text="", font=self.metrics(20)[0],
            fill=T.HI, anchor="center", justify="center",
        )
        self.time_caption = self.label(self.W // 2, 486, "", T.MID, 13, anchor="center")
        self.footer([("← →", T.RED), ("  typeface      ", T.DIM),
                     ("↑ ↓", T.RED), ("  format      ", T.DIM),
                     ("SPACE", T.RED), ("  freeze", T.DIM)])
        self.footer_right([("ESC", T.RED), ("  back", T.DIM)])

        self._time_layout()
        self._time_tick()

    def _time_layout(self):
        now = self.frozen_at if self.frozen else datetime.now()
        style = STYLE_NAMES[self.style_index]
        fmt = TIME_FORMATS[self.format_index]
        lines = render("\n".join(fmt[1](now)), style)
        font, cw, lh = self.fit(lines, self.W - 120, 330)
        self.canvas.itemconfigure(self.time_item, font=font, text="\n".join(lines))

        parts = [("FONT ", T.DIM), (f"{self.style_index + 1:02d}", T.RED),
                 (f"/{len(STYLE_NAMES)}  {style}      ", T.SOFT),
                 ("FORMAT ", T.DIM), (f"{self.format_index + 1}", T.RED),
                 (f"/{len(TIME_FORMATS)}  {fmt[0]}", T.SOFT)]
        total = sum(len(text) for text, _ in parts)
        self.canvas.delete("tinfo")
        self.seg(self.W - 46 - total * self.metrics(13)[1], 22, parts, 13, tags=("tinfo",))
        self._time_caption()

    def _time_render(self):
        now = self.frozen_at if self.frozen else datetime.now()
        fmt = TIME_FORMATS[self.format_index]
        style = STYLE_NAMES[self.style_index]
        lines = render("\n".join(fmt[1](now)), style)
        self.canvas.itemconfigure(self.time_item, text="\n".join(lines))

    def _time_caption(self):
        now = self.frozen_at if self.frozen else datetime.now()
        text = TIME_FORMATS[self.format_index][2](now)
        if self.frozen:
            text += "   ·   FROZEN"
        self.canvas.itemconfigure(self.time_caption, text=text)

    def _time_tick(self):
        if not self.frozen:
            self._time_render()
            self._time_caption()
        self.later(120, self._time_tick)

    def _time_key(self, event):
        key = event.keysym
        if key == "Escape":
            self.show_menu()
        elif key in ("Right", "d", "D"):
            self.style_index = (self.style_index + 1) % len(STYLE_NAMES)
            self._time_layout()
        elif key in ("Left", "a", "A"):
            self.style_index = (self.style_index - 1) % len(STYLE_NAMES)
            self._time_layout()
        elif key in ("Down", "s", "S"):
            self.format_index = (self.format_index + 1) % len(TIME_FORMATS)
            self._time_layout()
        elif key in ("Up", "w", "W"):
            self.format_index = (self.format_index - 1) % len(TIME_FORMATS)
            self._time_layout()
        elif key == "space":
            self.frozen = not self.frozen
            self.frozen_at = datetime.now()
            self._time_layout()

    # ================================================================ EYES
    def show_eyes(self):
        self.enter_screen("eyes", T.ACCENTS["eyes"])
        self.eye_index = getattr(self, "eye_index", 0)
        self.key_handler = self._eyes_key
        self.click_handler = None
        self.drag_handler = None
        self.motion_handler = None
        self.last_motion = 0.0

        self.header("EYES MODE")
        self.eyes_info = self.label(self.W - 46, 22, "", T.DIM, 13, anchor="ne")

        outline, core = eye_frame(EYE_NAMES[self.eye_index], 1.0, (0.0, 0.0))
        font, cw, lh = self.fit(outline, self.W - 110, 430)
        self.eye_font = font
        self.eye_core = self.canvas.create_text(
            self.W // 2, 292, text="\n".join(core), font=font,
            fill=T.RED, anchor="center", justify="center",
        )
        self.eye_item = self.canvas.create_text(
            self.W // 2, 292, text="\n".join(outline), font=font,
            fill=T.HI, anchor="center", justify="center",
        )
        self.eye_caption = self.label(self.W // 2, 528, "", T.SOFT, 13, anchor="center")
        self.footer([("← →", T.RED), ("  species      ", T.DIM),
                     ("SPACE", T.RED), ("  blink      ", T.DIM),
                     ("mouse", T.RED), ("  look around", T.DIM)])
        self.footer_right([("ESC", T.RED), ("  back", T.DIM)])

        self.look = [0.0, 0.0]
        self.look_target = [0.0, 0.0]
        self.next_wander = 0.0
        self.blink_start = None
        self.next_blink = time.perf_counter() + random.uniform(1.2, 3.0)
        self.blink_count = 0
        self.eyes_started = time.perf_counter()
        self._eyes_tick()

    def _eyes_tick(self):
        now = time.perf_counter()
        st = EYE_NAMES[self.eye_index]

        # Pupils follow the pointer, and wander when the pointer sleeps.
        idle = now - self.last_motion > 2.2
        if idle and now >= self.next_wander:
            self.look_target = [random.uniform(-0.9, 0.9), random.uniform(-0.75, 0.75)]
            self.next_wander = now + random.uniform(0.8, 2.2)
        elif not idle:
            dx = (self.pointer[0] - self.W / 2) / (self.W * 0.30)
            dy = (self.pointer[1] - 292) / (self.H * 0.30)
            self.look_target = [max(-1.0, min(1.0, dx)), max(-1.0, min(1.0, dy))]

        for index in (0, 1):
            self.look[index] += (self.look_target[index] - self.look[index]) * 0.28

        # Blink state machine.
        if self.blink_start is None and now >= self.next_blink:
            self.blink_start = now
        openness = 1.0
        if self.blink_start is not None:
            phase = (now - self.blink_start) / 0.24
            if phase >= 1.0:
                self.blink_start = None
                self.blink_count += 1
                delay = random.uniform(1.6, 5.2)
                if random.random() < 0.22:
                    delay = 0.28  # occasional double blink
                self.next_blink = now + delay
            else:
                openness = 1.0 - 0.97 * math.sin(math.pi * phase)

        outline, core = eye_frame(st, openness, self.look, now - self.eyes_started)
        self.canvas.itemconfigure(self.eye_item, text="\n".join(outline))
        self.canvas.itemconfigure(self.eye_core, text="\n".join(core))
        info_key = (self.eye_index, self.blink_count)
        if getattr(self, "_eye_info_key", None) != info_key:
            self._eye_info_key = info_key
            info = [("SPECIES ", T.DIM), (f"{self.eye_index + 1:02d}", T.RED),
                    (f"/{len(EYE_NAMES)}  {st}", T.SOFT), ("      BLINKS ", T.DIM),
                    (f"{self.blink_count:03d}", T.RED)]
            total = sum(len(text) for text, _ in info)
            self.canvas.delete("einfo")
            self.seg(self.W - 46 - total * self.metrics(13)[1], 22, info, 13, tags=("einfo",))
        self.canvas.itemconfigure(
            self.eye_caption,
            text=f"{'BLINK' if openness < 0.75 else 'WATCHING'}  ·  pupils on x {self.look[0]:+.2f}  y {self.look[1]:+.2f}",
        )
        self.later(50, self._eyes_tick)

    def _eyes_key(self, event):
        key = event.keysym
        if key == "Escape":
            self.show_menu()
        elif key in ("Right", "d", "D"):
            self.eye_index = (self.eye_index + 1) % len(EYE_NAMES)
            self._reload_eyes()
        elif key in ("Left", "a", "A"):
            self.eye_index = (self.eye_index - 1) % len(EYE_NAMES)
            self._reload_eyes()
        elif key == "space":
            self.blink_start = time.perf_counter() - 0.24 * 0.5

    def _reload_eyes(self):
        metrics = eye_metrics(EYE_NAMES[self.eye_index])
        dummy = [" " * metrics[0]] * metrics[1]
        font, _, _ = self.fit(dummy, self.W - 110, 430)
        self.eye_font = font
        self.canvas.itemconfigure(self.eye_item, font=font)
        self.canvas.itemconfigure(self.eye_core, font=font)
        self.blink_start = None
        self.next_blink = time.perf_counter() + 0.6

    # ================================================================ TEXT
    def show_text(self):
        self.enter_screen("text", T.ACCENTS["text"])
        self.text_style = getattr(self, "text_style", 0)
        self.buffer = getattr(self, "buffer", "")
        self.caret_on = True
        self.key_handler = self._text_key
        self.click_handler = None
        self.motion_handler = None
        self.drag_handler = None

        self.header("YOUR TEXT")
        self.text_item = self.canvas.create_text(
            self.W // 2, 268, text="", font=self.metrics(20)[0],
            fill=T.HI, anchor="center", justify="center",
        )
        self.text_caption = self.label(self.W // 2, 506, "", T.MID, 13, anchor="center")
        self.text_prompt = self.label(46, self.H - 96, ">", T.RED, 13)
        self.text_entry = self.label(46 + 2 * self.metrics(13)[1], self.H - 96, "", T.HI, 13)
        self.text_caret = self.label(46 + 2 * self.metrics(13)[1], self.H - 96, "", T.RED, 13)
        self.footer([("type", T.RED), ("  anything   ·   ", T.DIM),
                     ("BACKSPACE", T.RED), ("  delete   ·   ", T.DIM),
                     ("← →", T.RED), ("  or  ", T.DIM), ("TAB", T.RED), ("  change font", T.DIM)])
        self.footer_right([("ESC", T.RED), ("  back", T.DIM)])

        self._text_refresh()
        self.later(520, self._caret_tick)

    def _caret_tick(self):
        self.caret_on = not self.caret_on
        self._text_echo()
        self.later(520, self._caret_tick)

    def _text_echo(self):
        shown = self.buffer or ""
        cw = self.metrics(13)[1]
        x = 46 + 2 * cw + len(shown) * cw
        self.canvas.itemconfigure(self.text_entry, text=shown)
        self.canvas.coords(self.text_caret, x, self.H - 96)
        self.canvas.itemconfigure(self.text_caret, text="▌" if self.caret_on else " ")

    def _wrap(self, text, count):
        words = text.split(" ")
        if count <= 1 or len(words) <= 1:
            return [text]
        target = max(1, math.ceil(len(text) / count))
        lines, current = [], ""
        for word in words:
            candidate = (current + " " + word) if current else word
            if len(candidate) > target and current and len(lines) < count - 1:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def _text_refresh(self):
        style = STYLE_NAMES[self.text_style]
        body = self.buffer if self.buffer.strip() else "YOUR TEXT"
        placeholder = not self.buffer.strip()

        best = None
        for count in (1, 2, 3, 4):
            wrapped = self._wrap(body, count)
            lines = render("\n".join(wrapped), style)
            font, cw, lh = self.fit(lines, self.W - 110, 372)
            score = font.actual("size")
            if best is None or score > best[0]:
                best = (score, lines, font)
        _, lines, font = best

        self.canvas.itemconfigure(
            self.text_item, text="\n".join(lines), font=font,
            fill=T.FAINT if placeholder else T.HI,
        )
        parts = [("FONT ", T.DIM), (f"{self.text_style + 1:02d}", T.RED),
                 (f"/{len(STYLE_NAMES)}  {style}", T.SOFT)]
        total = sum(len(text) for text, _ in parts)
        self.canvas.delete("tinfo")
        self.seg(self.W - 46 - total * self.metrics(13)[1], 22, parts, 13, tags=("tinfo",))
        self.canvas.itemconfigure(
            self.text_caption,
            text=f"{style.lower()}   ·   {len(self.buffer)} / 60 characters",
        )
        self._text_echo()

    def _text_key(self, event):
        key = event.keysym
        if key == "Escape":
            self.show_menu()
            return
        if key == "BackSpace":
            self.buffer = self.buffer[:-1]
        elif key == "Left":
            self.text_style = (self.text_style - 1) % len(STYLE_NAMES)
        elif key in ("Right", "Tab"):
            self.text_style = (self.text_style + 1) % len(STYLE_NAMES)
        elif key == "Prior":
            self.text_style = (self.text_style - 1) % len(STYLE_NAMES)
        elif key == "Next":
            self.text_style = (self.text_style + 1) % len(STYLE_NAMES)
        else:
            char = event.char
            if char and char.isprintable() and len(self.buffer) < 60:
                self.buffer += char
        self._text_refresh()

    # ================================================================ LIFE
    def show_life(self):
        self.enter_screen("life", T.ACCENTS["life"])
        self.key_handler = self._life_key
        self.click_handler = self._life_click
        self.drag_handler = self._life_click
        self.motion_handler = None

        font, cw, lh = self.metrics(12)
        self.cell_w = cw * 2
        self.cell_h = lh
        self.cols = max(20, (self.W - 96) // self.cell_w)
        self.rows = max(12, (self.H - 200) // self.cell_h)
        self.grid_x = (self.W - self.cols * self.cell_w) // 2
        self.grid_y = 76

        self.alive: set[tuple[int, int]] = set()
        self.age: dict[tuple[int, int], int] = {}
        self.generation = 0
        self.paused = False
        self.life_layers = []
        for color in (T.RED, T.HI, T.MID, T.DIM):
            self.life_layers.append(self.canvas.create_text(
                self.grid_x, self.grid_y, text="", font=font, fill=color,
                anchor="nw", justify="left",
            ))
        self.header("LIFE")
        self.life_caption = self.label(46, self.H - 118, "", T.DIM, 12)
        self.life_status = self.label(46, self.H - 88, "", T.RED, 13)
        self.life_info = self.label(230, self.H - 88, "", T.MID, 13)
        self.footer([("click", T.RED), ("  draw   ·   ", T.DIM),
                     ("SPACE", T.RED), ("  pause   ·   ", T.DIM),
                     ("R", T.RED), ("  seed   ·   ", T.DIM),
                     ("C", T.RED), ("  clear   ·   ", T.DIM),
                     ("S", T.RED), ("  step", T.DIM)])
        self.footer_right([("ESC", T.RED), ("  back", T.DIM)])

        self._life_seed()
        self._life_paint()
        self.later(int(1000 / T.LIFE_FPS), self._life_tick)

    def _life_seed(self):
        self.alive = set()
        self.age = {}
        for _ in range(int(self.cols * self.rows * 0.26)):
            cell = (random.randrange(self.cols), random.randrange(self.rows))
            self.alive.add(cell)
            self.age[cell] = random.randint(0, 6)
        self.generation = 0

    def _life_step(self):
        counts: dict[tuple[int, int], int] = {}
        cols, rows = self.cols, self.rows
        for (x, y) in self.alive:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    key = ((x + dx) % cols, (y + dy) % rows)
                    counts[key] = counts.get(key, 0) + 1

        born = {cell for cell, n in counts.items() if n == 3 and cell not in self.alive}
        survive = {cell for cell in self.alive if counts.get(cell, 0) in (2, 3)}
        new_alive = born | survive

        age = {}
        for cell in new_alive:
            age[cell] = 0 if cell in born else min(99, self.age.get(cell, 0) + 1)
        self.alive = new_alive
        self.age = age
        self.generation += 1

    def _life_paint(self):
        # Four age bands, each its own colour layer: newborn cells glow red.
        bands = (("█", 2), ("▓", 6), ("▒", 14), ("░", 99))
        frames = []
        for y in range(self.rows):
            rows = [[" "] * self.cols for _ in range(4)]
            for x in range(self.cols):
                if (x, y) not in self.alive:
                    continue
                age = self.age.get((x, y), 0)
                band = 0
                for index, (_, limit) in enumerate(bands):
                    if age < limit:
                        band = index
                        break
                rows[band][x] = bands[band][0] * 2
            frames.append(["".join(row) for row in rows])

        for band in range(4):
            text_lines = [frames[y][band] for y in range(self.rows)]
            self.canvas.itemconfigure(self.life_layers[band], text="\n".join(text_lines))

        running = not self.paused
        self.canvas.itemconfigure(
            self.life_status, text="● RUNNING" if running else "○ PAUSED",
            fill=T.RED if running else T.MID,
        )
        self.canvas.itemconfigure(
            self.life_info,
            text=f"GEN {self.generation:04d}     POP {len(self.alive):04d}     GRID {self.cols} x {self.rows}",
        )
        self.canvas.itemconfigure(
            self.life_caption,
            text=f"cell density = age   ·   {T.LIFE_FPS} generations per second",
        )

    def _life_tick(self):
        if not self.paused:
            self._life_step()
            self._life_paint()
        self.later(int(1000 / T.LIFE_FPS), self._life_tick)

    def _life_cell(self, event):
        x = (event.x - self.grid_x) // self.cell_w
        y = (event.y - self.grid_y) // self.cell_h
        return int(x), int(y)

    def _life_click(self, event):
        x, y = self._life_cell(event)
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell = ((x + dx) % self.cols, (y + dy) % self.rows)
                if cell in self.alive:
                    self.alive.discard(cell)
                    self.age.pop(cell, None)
                else:
                    self.alive.add(cell)
                    self.age[cell] = 0
        self._life_paint()

    def _life_key(self, event):
        key = event.keysym
        if key == "Escape":
            self.show_menu()
        elif key == "space":
            self.paused = not self.paused
            self._life_paint()
        elif key in ("r", "R"):
            self._life_seed()
            self._life_paint()
        elif key in ("c", "C"):
            self.alive.clear()
            self.age.clear()
            self.generation = 0
            self._life_paint()
        elif key in ("s", "S"):
            self._life_step()
            self._life_paint()


def main(argv=None):
    parser = argparse.ArgumentParser(description="GlythMinis - ASCII toybox")
    parser.add_argument("--screen", choices=("menu", "time", "eyes", "text", "life"),
                        help="skip the boot animation and open a screen directly")
    parser.add_argument("--style", type=int, help="typeface index 1..12 for TIME/TEXT")
    parser.add_argument("--format", type=int, help="time format index 1..6")
    parser.add_argument("--eye", type=int, help="eye species index 1..8")
    parser.add_argument("--text", type=str, help="prefill the YOUR TEXT buffer")
    args = parser.parse_args(argv)

    root = tk.Tk()
    GlythMinis(
        root,
        screen=args.screen,
        style=(args.style - 1) if args.style else None,
        fmt=(args.format - 1) if args.format else None,
        eye=(args.eye - 1) if args.eye else None,
        text=args.text,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
