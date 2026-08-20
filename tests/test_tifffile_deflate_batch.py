import sys
from pathlib import Path

import numpy as np
import tifffile


PROJECT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from converter import (
    build_full_metadata,
    save_temperature_tiff,
    create_sdk,
)
from metadata import extract_metadata


INPUT_DIR = PROJECT_DIR / "data" / "compression_test_input"
OUTPUT_DIR = PROJECT_DIR / "data" / "compression_test_output"


def inspect_tiff(output_tiff):
    """Return the key TIFF properties used by this compression test."""
    with tifffile.TiffFile(output_tiff) as tif:
        page = tif.pages[0]

        sample_format = page.tags.get("SampleFormat")
        bits_per_sample = page.tags.get("BitsPerSample")
        compression = page.tags.get("Compression")
        xmp_tag = page.tags.get(700)
        description_tag = page.tags.get("ImageDescription")

        return {
            "sample_format": (
                sample_format.value if sample_format else None
            ),
            "bits_per_sample": (
                bits_per_sample.value if bits_per_sample else None
            ),
            "compression": (
                compression.value if compression else None
            ),
            "xmp_present": xmp_tag is not None,
            "description_present": description_tag is not None,
        }


def verify_pixels(original_matrix, output_tiff):
    """Compare a saved TIFF raster against the source temperature matrix."""
    compressed = tifffile.imread(output_tiff).astype(
        np.float32,
        copy=False,
    )

    difference = original_matrix - compressed

    return {
        "dtype": str(compressed.dtype),
        "max_diff": float(np.abs(difference).max()),
        "mean_diff": float(np.abs(difference).mean()),
        "rmse": float(
            np.sqrt(
                np.mean(
                    difference * difference
                )
            )
        ),
    }


def main():
    """Run a batch regression test for lossless Deflate TIFF output."""
    if not INPUT_DIR.exists():
        raise FileNotFoundError(
            f"Input folder not found: {INPUT_DIR}"
        )

    images = sorted(
        path
        for path in INPUT_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".jpg", ".jpeg"}
    )

    if not images:
        raise ValueError(
            f"No JPG/JPEG files found in: {INPUT_DIR}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sdk = create_sdk()
    results = []

    print(f"Found {len(images)} image(s).")
    print("Running batch Deflate compression test.")

    for index, image_path in enumerate(
        images,
        start=1,
    ):
        print()
        print("=" * 70)
        print(f"[{index}/{len(images)}] {image_path.name}")
        print("=" * 70)

        temperature_matrix, radiometry_data = sdk.process_image_info(
            image_path
        )

        source_metadata = extract_metadata(image_path)

        full_metadata = build_full_metadata(
            temperature_matrix,
            radiometry_data,
            source_metadata,
        )

        import json

        metadata_str = json.dumps(
            full_metadata,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        output_tiff = (
            OUTPUT_DIR
            / f"{image_path.stem}_deflate.tif"
        )

        save_temperature_tiff(
            output_path=output_tiff,
            temperature_matrix=temperature_matrix,
            source_image=image_path,
            metadata_str=metadata_str,
        )

        verification = verify_pixels(
            temperature_matrix,
            output_tiff,
        )

        tags = inspect_tiff(output_tiff)

        result = {
            "filename": output_tiff.name,
            "size_bytes": output_tiff.stat().st_size,
            **verification,
            **tags,
        }

        results.append(result)

        print(f"Saved: {output_tiff}")
        print(f"Size: {result['size_bytes']} bytes")
        print(f"dtype: {verification['dtype']}")
        print(f"MAX DIFF: {verification['max_diff']}")
        print(f"MEAN DIFF: {verification['mean_diff']}")
        print(f"RMSE: {verification['rmse']}")
        print(f"SampleFormat: {tags['sample_format']}")
        print(f"BitsPerSample: {tags['bits_per_sample']}")
        print(f"Compression: {tags['compression']}")
        print(
            "XMP tag 700: "
            f"{'present' if tags['xmp_present'] else 'missing'}"
        )
        print(
            "ImageDescription: "
            f"{'present' if tags['description_present'] else 'missing'}"
        )

    all_exact = all(
        item["max_diff"] == 0.0
        and item["mean_diff"] == 0.0
        and item["rmse"] == 0.0
        for item in results
    )

    all_float32 = all(
        item["dtype"] == "float32"
        and item["bits_per_sample"] == 32
        and item["sample_format"] == 3
        for item in results
    )

    all_xmp = all(
        item["xmp_present"]
        for item in results
    )

    all_descriptions = all(
        item["description_present"]
        for item in results
    )

    print()
    print("=" * 70)
    print("BATCH SUMMARY")
    print("=" * 70)
    print(f"Files created: {len(results)}")
    print(f"Pixel-perfect: {'YES' if all_exact else 'NO'}")
    print(f"Float32: {'YES' if all_float32 else 'NO'}")
    print(f"XMP present: {'YES' if all_xmp else 'NO'}")
    print(
        "ImageDescription present: "
        f"{'YES' if all_descriptions else 'NO'}"
    )
    print(f"Output folder: {OUTPUT_DIR}")

    if not all_exact:
        raise AssertionError(
            "At least one compressed TIFF changed raster values."
        )

    if not all_float32:
        raise AssertionError(
            "At least one output TIFF is not valid Float32."
        )

    if not all_xmp:
        raise AssertionError(
            "At least one output TIFF is missing XMP tag 700."
        )

    if not all_descriptions:
        raise AssertionError(
            "At least one output TIFF is missing ImageDescription."
        )

    print("\nPASS: all batch compression checks passed.")


if __name__ == "__main__":
    main()