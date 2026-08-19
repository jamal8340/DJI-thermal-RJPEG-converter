import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

# Allow imports from project src when this script is placed in tests/
PROJECT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metadata import extract_metadata, extract_raw_xmp


INPUT_TIFF = (
    PROJECT_DIR
    / "data"
    / "test_output"
    / "DJI_20230920123005_0001_T.tif"
)

SOURCE_RJPEG = (
    PROJECT_DIR
    / "data"
    / "test_input"
    / "DJI_20230920123005_0001_T.JPG"
)

OUTPUT_TIFF = (
    PROJECT_DIR
    / "data"
    / "test_output"
    / "DJI_20230920123005_0001_T_tifffile_deflate.tif"
)


def make_json_safe(value):
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    return str(value)


def get_basic_exif_tags(source_path):
    """
    Copy only simple top-level TIFF/EXIF tags that tifffile can write
    directly without creating nested EXIF/GPS IFD structures.

    GPS/orientation used by DJI is tested primarily through the raw
    DJI XMP block stored in TIFF tag 700.
    """
    tags = []

    with Image.open(source_path) as image:
        exif = image.getexif()

        # TIFF Make
        make = exif.get(271)
        if make:
            value = str(make)
            tags.append(
                (
                    271,
                    "s",
                    len(value) + 1,
                    value,
                    True,
                )
            )

        # TIFF Model
        model = exif.get(272)
        if model:
            value = str(model)
            tags.append(
                (
                    272,
                    "s",
                    len(value) + 1,
                    value,
                    True,
                )
            )

        # TIFF DateTime
        date_time = exif.get(306)
        if date_time:
            value = str(date_time)
            tags.append(
                (
                    306,
                    "s",
                    len(value) + 1,
                    value,
                    True,
                )
            )

    return tags


def main():
    if not INPUT_TIFF.exists():
        raise FileNotFoundError(
            f"Input TIFF not found: {INPUT_TIFF}"
        )

    if not SOURCE_RJPEG.exists():
        raise FileNotFoundError(
            f"Source R-JPEG not found: {SOURCE_RJPEG}"
        )

    OUTPUT_TIFF.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Reading Float32 raster...")

    with Image.open(INPUT_TIFF) as image:
        temperature = np.array(
            image,
            dtype=np.float32,
        )

    print(
        f"Shape: {temperature.shape}"
    )
    print(
        f"dtype: {temperature.dtype}"
    )
    print(
        f"Min: {temperature.min():.6f} °C"
    )
    print(
        f"Max: {temperature.max():.6f} °C"
    )
    print(
        f"Mean: {temperature.mean():.6f} °C"
    )

    print("\nReading source metadata...")

    source_metadata = extract_metadata(
        SOURCE_RJPEG
    )

    raw_xmp = extract_raw_xmp(
        SOURCE_RJPEG
    )

    description = json.dumps(
        make_json_safe(source_metadata),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    extratags = get_basic_exif_tags(
        SOURCE_RJPEG
    )

    if raw_xmp:
        xmp_bytes = bytes(raw_xmp)

        extratags.append(
            (
                700,        # TIFF XMP tag
                "B",        # BYTE
                len(xmp_bytes),
                xmp_bytes,
                True,
            )
        )

        print(
            f"DJI XMP found: {len(xmp_bytes)} bytes"
        )
    else:
        print(
            "WARNING: raw DJI XMP was not found."
        )

    print(
        "\nWriting separate test TIFF with Deflate..."
    )

    tifffile.imwrite(
        OUTPUT_TIFF,
        temperature,
        dtype=np.float32,
        photometric="minisblack",
        compression="zlib",
        compressionargs={
            "level": 6,
        },
        metadata=None,
        description=description,
        extratags=extratags,
    )

    print(
        f"Saved: {OUTPUT_TIFF}"
    )

    print("\nChecking pixels...")

    compressed = tifffile.imread(
        OUTPUT_TIFF
    ).astype(
        np.float32,
        copy=False,
    )

    difference = (
        temperature
        - compressed
    )

    print(
        f"Output dtype: {compressed.dtype}"
    )
    print(
        f"MAX DIFF: {np.abs(difference).max()}"
    )
    print(
        f"MEAN DIFF: {np.abs(difference).mean()}"
    )
    print(
        f"RMSE: {np.sqrt(np.mean(difference * difference))}"
    )

    original_size = INPUT_TIFF.stat().st_size
    compressed_size = OUTPUT_TIFF.stat().st_size

    print("\nFile sizes:")
    print(
        f"Original:   {original_size} bytes"
    )
    print(
        f"Compressed: {compressed_size} bytes"
    )

    if original_size > 0:
        percent = (
            compressed_size
            / original_size
            * 100.0
        )

        print(
            f"Compressed size: {percent:.1f}% of original"
        )

    print("\nInspecting important TIFF tags...")

    with tifffile.TiffFile(
        OUTPUT_TIFF
    ) as tif:
        page = tif.pages[0]

        print(
            f"SampleFormat: "
            f"{page.tags.get('SampleFormat').value if page.tags.get('SampleFormat') else 'missing'}"
        )

        print(
            f"BitsPerSample: "
            f"{page.tags.get('BitsPerSample').value if page.tags.get('BitsPerSample') else 'missing'}"
        )

        print(
            f"Compression: "
            f"{page.tags.get('Compression').value if page.tags.get('Compression') else 'missing'}"
        )

        xmp_tag = page.tags.get(700)

        print(
            f"XMP tag 700: "
            f"{'present' if xmp_tag else 'missing'}"
        )

        description_tag = page.tags.get(
            "ImageDescription"
        )

        print(
            f"ImageDescription: "
            f"{'present' if description_tag else 'missing'}"
        )

    print(
        "\nTEST FILE CREATED."
    )
    print(
        "Do not replace the main converter yet."
    )
    print(
        "Next step: run validator.py and import this single TIFF into Metashape."
    )


if __name__ == "__main__":
    main()