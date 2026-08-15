import re
from pathlib import Path

import exifread


base_dir = Path(__file__).resolve().parent.parent
image_path = base_dir / "data" / "input" / "DJI_20230920123005_0001_T.JPG"


with image_path.open("rb") as image_file:
    tags = exifread.process_file(image_file, details=True)

print("\n=== EXIF ===")
print(f"File: {image_path.name}")
print(f"EXIF tags found: {len(tags)}")
print("=" * 80)

for name, value in sorted(tags.items()):
    if name != "JPEGThumbnail":
        print(f"{name}: {value}")


file_data = image_path.read_bytes()
text = file_data.decode("utf-8", errors="ignore")

pattern = r'drone-dji:([A-Za-z0-9_]+)\s*=\s*["\']([^"\']*)["\']'
dji_xmp = re.findall(pattern, text)

print("\n=== DJI XMP ===")
print("=" * 80)

if dji_xmp:
    print(f"DJI XMP fields found: {len(dji_xmp)}\n")

    for name, value in dji_xmp:
        print(f"{name}: {value}")
else:
    print("No DJI XMP fields found.")