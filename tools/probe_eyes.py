"""Console check for the procedural eyes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from glythminis.eyes import EYE_NAMES, eye_frame

for name in EYE_NAMES:
    print(f"=== {name} open ===")
    print("\n".join(eye_frame(name, 1.0, (0.0, 0.0), 0.4)))

print("=== ROUND half ===")
print("\n".join(eye_frame("ROUND", 0.45, (0.0, 0.0))))
print("=== ROUND shut ===")
print("\n".join(eye_frame("ROUND", 0.0, (0.0, 0.0))))
print("=== ROUND looking left ===")
print("\n".join(eye_frame("ROUND", 1.0, (-1.0, 0.3))))
