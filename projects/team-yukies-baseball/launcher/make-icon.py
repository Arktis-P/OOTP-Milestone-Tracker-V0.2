from pathlib import Path
import base64
from PIL import Image

here = Path(__file__).resolve().parent
project_root = here.parent
source_path = here / "app-icon.source.b64"
png_path = project_root / "card-template-html" / "assets" / "app-icon.png"
ico_path = project_root / "card-template-html" / "assets" / "app-icon.ico"

encoded = "".join(source_path.read_text(encoding="ascii").split())
png_path.write_bytes(base64.b64decode(encoded, validate=True))

with Image.open(png_path) as image:
    image.load()
    rgba = image.convert("RGBA")
    rgba.save(
        ico_path,
        format="ICO",
        sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
    )

print(f"Restored PNG: {png_path}")
print(f"Built Windows icon: {ico_path}")
