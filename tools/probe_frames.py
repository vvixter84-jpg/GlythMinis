"""Draw blink stages side by side so the mid-blink frames can be judged."""
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from glythminis.eyes import eye_frame

STAGES = [(1.0, "OPEN"), (0.75, "0.75"), (0.45, "0.45"), (0.25, "0.25"), (0.0, "SHUT")]

root = tk.Tk()
root.title("GlythMinis 1.0 frames")
root.geometry("1300x1000+60+60")
root.configure(bg="#000000")
canvas = tk.Canvas(root, bg="#000000", highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)

small = tkfont.Font(family="Consolas", size=11)
font = tkfont.Font(family="Consolas", size=9)

y = 20
for openness, name in STAGES:
    art = eye_frame("ROUND", openness, (0.2, -0.1))
    canvas.create_text(20, y, text=name, font=small, fill="#8dffbb", anchor="nw")
    canvas.create_text(90, y, text="\n".join(art), font=font, fill="#8dffbb", anchor="nw", justify="left")
    y += len(art) * font.metrics("linespace") + 10

root.after(5000, root.destroy)
root.mainloop()
