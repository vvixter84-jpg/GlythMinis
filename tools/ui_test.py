"""Headless-ish wiring test: drives the app with synthetic key/click events."""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from glythminis.app import GlythMinis

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}")


class Ev:
    def __init__(self, keysym="", char="", x=0, y=0):
        self.keysym = keysym
        self.char = char
        self.x = x
        self.y = y


root = tk.Tk()
app = GlythMinis(root, screen="menu")
root.update()
check("menu starts", app.screen == "menu")
check("four buttons", len(app.buttons) == 4, str(app.buttons))

app._menu_key(Ev("Down"))
check("down moves selection", app.selected == 1)
app._menu_key(Ev("Up"))
check("up moves selection back", app.selected == 0)

# mouse click on the third button
x0, y0, x1, y1 = app.buttons[2]
app._menu_click(Ev(x=(x0 + x1) // 2, y=(y0 + y1) // 2))
root.update()
check("click opens text mode", app.screen == "text")

for ch in "hi 42":
    app._text_key(Ev(ch, ch))
root.update()
check("typing appends", app.buffer == "hi 42", repr(app.buffer))
app._text_key(Ev("BackSpace"))
check("backspace deletes", app.buffer == "hi 4", repr(app.buffer))
before = app.text_style
app._text_key(Ev("Right"))
check("right cycles font", app.text_style == (before + 1) % 12)
app._text_key(Ev("Escape"))
root.update()
check("escape returns to menu", app.screen == "menu")

app._menu_key(Ev("1"))
root.update()
check("number key opens time", app.screen == "time")
before_fmt = app.format_index
app._time_key(Ev("Down"))
check("time format cycles", app.format_index != before_fmt)
before_style = app.style_index
app._time_key(Ev("Right"))
check("time font cycles", app.style_index != before_style)
app._time_key(Ev("space"))
check("time freezes", app.frozen is True)
app._time_key(Ev("Escape"))
root.update()
check("time escape -> menu", app.screen == "menu")

app._menu_key(Ev("2"))
root.update()
check("open eyes", app.screen == "eyes")
before_eye = app.eye_index
app._eyes_key(Ev("Right"))
check("eye species cycles", app.eye_index != before_eye)
app._eyes_key(Ev("Escape"))
root.update()
check("eyes escape -> menu", app.screen == "menu")

app._menu_key(Ev("4"))
root.update()
check("open life", app.screen == "life")
pop = len(app.alive)
app._life_step()
check("life steps", app.generation == 1, f"pop {pop} -> {len(app.alive)}")
app._life_key(Ev("space"))
check("life pauses", app.paused is True)
app._life_key(Ev("r"))
check("life reseeds", app.generation == 0 and len(app.alive) > 0)
app._life_key(Ev("Escape"))
root.update()
check("life escape -> menu", app.screen == "menu")

# every typeface must render the clock without blowing up
from glythminis.glyphs import STYLE_NAMES, render
for style in STYLE_NAMES:
    art = render("23:59:59", style)
    widths = {len(line) for line in art}
    check(f"font {style}", len(widths) == 1, f"{len(art)}x{max(widths)}")

# every eye species at several blink stages, and both colour layers aligned
from glythminis.eyes import EYE_NAMES, eye_frame
for name in EYE_NAMES:
    for openness in (1.0, 0.5, 0.25, 0.0):
        outline, core = eye_frame(name, openness, (0.4, -0.4))
        widths = {len(line) for line in outline} | {len(line) for line in core}
        check(f"eye {name}@{openness}", len(widths) == 1,
              f"{len(outline)}x{max(widths)}")

# real Tk events must reach the same handlers (binding sanity, not just logic)
app.show_menu()
root.update()
app.selected = 0
root.event_generate("<Key>", keysym="Down", when="now")
root.update()
check("real <Key> binding", app.selected == 1, f"selected={app.selected}")

bx0, by0, bx1, by1 = app.buttons[1]
app.canvas.event_generate("<Button-1>", x=(bx0 + bx1) // 2, y=(by0 + by1) // 2, when="now")
root.update()
check("real <Button-1> binding", app.screen == "eyes", app.screen)

root.destroy()
failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
