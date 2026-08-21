from pathlib import Path
from metadata import extract_dji_xmp, extract_exif


def main():
    """Print EXIF and DJI XMP metadata from a development test image."""
    base_dir = Path(__file__).resolve().parent.parent
    image_path = (
        base_dir
        / "data"
        / "input"
        / "DJI_20230920123005_0001_T.JPG"
    )

    if not image_path.exists():
        raise FileNotFoundError(f"Test image not found: {image_path}")

    exif_data = extract_exif(image_path)
    dji_xmp = extract_dji_xmp(image_path)

    print("\n=== EXIF ===")
    print(f"File: {image_path.name}")
    print(f"EXIF fields found: {len(exif_data)}")
    print("=" * 80)

    for name, value in sorted(exif_data.items()):
        print(f"{name}: {value}")

    print("\n=== DJI XMP ===")
    print("=" * 80)

    if not dji_xmp:
        print("No DJI XMP fields found.")
        return

    print(f"DJI XMP fields found: {len(dji_xmp)}\n")

    for name, value in sorted(dji_xmp.items()):
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()