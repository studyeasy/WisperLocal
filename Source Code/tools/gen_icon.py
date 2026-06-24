"""Generate assets/icon.ico (multi-resolution) for the app/installer."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "icon.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

m = int(S * 0.03)
d.ellipse([m, m, S - m, S - m], fill="#3B82F6")

# microphone capsule
cw, ch = S * 0.23, S * 0.34
cx0, cy0 = S * 0.385, S * 0.22
d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=S * 0.115, fill="white")

w = max(2, int(S * 0.05))
# guard arc (opens downward, cradling the capsule)
d.arc([S * 0.30, S * 0.26, S * 0.70, S * 0.66], start=15, end=165, fill="white", width=w)
# stem + base
d.line([S * 0.5, S * 0.655, S * 0.5, S * 0.77], fill="white", width=w)
d.line([S * 0.40, S * 0.79, S * 0.60, S * 0.79], fill="white", width=w)

img.save(OUT, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", OUT)
