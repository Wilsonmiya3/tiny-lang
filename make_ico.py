"""Builds assets/tiny.ico (used for the .exe and the installer)."""
import os, struct
from icon_gen import make_png

png = make_png(128)
os.makedirs("assets", exist_ok=True)
with open(os.path.join("assets", "tiny.ico"), "wb") as f:
    f.write(struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 128, 128, 0, 0, 1, 32, len(png), 22) + png)
print("icon written: assets/tiny.ico")