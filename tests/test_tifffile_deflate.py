import json
import sys
from pathlib import Path

import numpy as np
import tifffile


PROJECT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from converter import save_temperature_tiff
from metadata import extract_metadata


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


def main():
    """Verify lossless Deflate compression and required TIFF metadata tags."""
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

    temperature = tifffile.imread(INPUT_TIFF).astype(
        np.float32,
        copy=False,
    )

    source_metadata = extract_metadata(SOURCE_RJPEG)
    description = json.dumps(
        source_metadata,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    save_temperature_tiff(
        output_path=OUTPUT_TIFF,
        temperature_matrix=temperature,
        source_image=SOURCE_RJPEG,
        metadata_str=description,
    )

    compressed = tifffile.imread(OUTPUT_TIFF).astype(
        np.float32,
        copy=False,
    )

    difference = temperature - compressed
    max_diff = float(np.abs(difference).max())
    mean_diff = float(np.abs(difference).mean())
    rmse = float(np.sqrt(np.mean(difference * difference)))

    print("DEFLATE COMPRESSION CHECK")
    print("=" * 50)
    print(f"Shape:      {compressed.shape}")
    print(f"Dtype:      {compressed.dtype}")
    print(f"Max diff:   {max_diff}")
    print(f"Mean diff:  {mean_diff}")
    print(f"RMSE:       {rmse}")

    if not np.array_equal(temperature, compressed):
        raise AssertionError(
            "Deflate-compressed TIFF changed raster values."
        )

    original_size = INPUT_TIFF.stat().st_size
    compressed_size = OUTPUT_TIFF.stat().st_size

    print()
    print(f"Original size:   {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")

    if original_size > 0:
        print(
            "Compressed size: "
            f"{compressed_size / original_size * 100.0:.1f}% "
            "of original"
        )

    with tifffile.TiffFile(OUTPUT_TIFF) as tif:
        page = tif.pages[0]

        sample_format = page.tags.get("SampleFormat")
        bits_per_sample = page.tags.get("BitsPerSample")
        compression = page.tags.get("Compression")
        xmp_tag = page.tags.get(700)
        description_tag = page.tags.get("ImageDescription")

        print()
        print(
            "SampleFormat: "
            f"{sample_format.value if sample_format else 'missing'}"
        )
        print(
            "BitsPerSample: "
            f"{bits_per_sample.value if bits_per_sample else 'missing'}"
        )
        print(
            "Compression: "
            f"{compression.value if compression else 'missing'}"
        )
        print(
            f"XMP tag 700: {'present' if xmp_tag else 'missing'}"
        )
        print(
            "ImageDescription: "
            f"{'present' if description_tag else 'missing'}"
        )

        if xmp_tag is None:
            raise AssertionError("TIFF XMP tag 700 is missing.")

        if description_tag is None:
            raise AssertionError(
                "TIFF ImageDescription is missing."
            )

    print("\nPASS: Deflate compression is lossless and metadata is present.")


if __name__ == "__main__":
    main()