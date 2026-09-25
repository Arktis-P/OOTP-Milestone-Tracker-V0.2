from pathlib import Path
from PIL import Image

here = Path(__file__).resolve().parent
project_root = here.parent
png_path = project_root / "card-template-html" / "assets" / "app-icon.png"
ico_path = project_root / "card-template-html" / "assets" / "app-icon.ico"

if not png_path.is_file():
    raise SystemExit(f"PNG icon not found: {png_path}")

with Image.open(png_path) as image:
    rgba = image.convert("RGBA")
    rgba.save(
        ico_path,
        format="ICO",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )

print(f"Built Windows icon: {ico_path}")
