from pathlib import Path
from PIL import Image

here = Path(__file__).resolve().parent
project_root = here.parent
png_path = project_root / "card-template-html" / "assets" / "app-icon.png"
ico_path = project_root / "card-template-html" / "assets" / "app-icon.ico"

if not png_path.is_file():
    raise FileNotFoundError(f"Icon source not found: {png_path}")

with Image.open(png_path) as source:
    source.verify()

with Image.open(png_path) as source:
    rgba = source.convert("RGBA")
    square = rgba.resize((128, 128), Image.Resampling.LANCZOS)
    indexed = square.quantize(
        colors=256,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.FLOYDSTEINBERG,
    )
    indexed.convert("RGBA").save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)],
    )

with Image.open(ico_path) as icon:
    sizes = sorted(icon.ico.sizes())

expected = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
if sizes != expected:
    raise RuntimeError(f"Unexpected ICO sizes: {sizes}")

print(f"Source PNG: {png_path}")
print(f"Windows ICO: {ico_path}")
print(f"ICO sizes: {sizes}")
