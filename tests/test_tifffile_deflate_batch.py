import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from converter import create_sdk
from metadata import extract_metadata, extract_raw_xmp


INPUT_DIR = PROJECT_DIR / "data" / "compression_test_input"
OUTPUT_DIR = PROJECT_DIR / "data" / "compression_test_output"


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
    Copy simple top-level TIFF/EXIF tags that tifffile can write
    without nested EXIF/GPS IFD structures.

    DJI GPS/orientation is preserved through raw XMP in TIFF tag 700.
    """
    tags = []

    with Image.open(source_path) as image:
        exif = image.getexif()

        for tag_id in (271, 272, 306):  # Make, Model, DateTime
            value = exif.get(tag_id)

            if not value:
                continue

            value = str(value)

            tags.append(
                (
                    tag_id,
                    "s",
                    len(value) + 1,
                    value,
                    True,
                )
            )

    return tags


def build_description(
    temperature_matrix,
    radiometry_data,
    source_metadata,
):
    full_metadata = {
        "temperature": {
            "unit": "Celsius",
            "data_type": "float32",
            "width": int(
                temperature_matrix.shape[1]
            ),
            "height": int(
                temperature_matrix.shape[0]
            ),
            "min": float(
                temperature_matrix.min()
            ),
            "max": float(
                temperature_matrix.max()
            ),
        },
        "radiometry": radiometry_data,
        "source_metadata": source_metadata,
    }

    return json.dumps(
        make_json_safe(full_metadata),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def write_compressed_tiff(
    source_rjpeg,
    output_tiff,
    temperature_matrix,
    radiometry_data,
):
    source_metadata = extract_metadata(
        source_rjpeg
    )

    raw_xmp = extract_raw_xmp(
        source_rjpeg
    )

    description = build_description(
        temperature_matrix,
        radiometry_data,
        source_metadata,
    )

    extratags = get_basic_exif_tags(
        source_rjpeg
    )

    if raw_xmp:
        xmp_bytes = bytes(
            raw_xmp
        )

        extratags.append(
            (
                700,
                "B",
                len(xmp_bytes),
                xmp_bytes,
                True,
            )
        )

    tifffile.imwrite(
        output_tiff,
        temperature_matrix.astype(
            np.float32,
            copy=False,
        ),
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


def verify_pixels(
    original_matrix,
    output_tiff,
):
    compressed = tifffile.imread(
        output_tiff
    ).astype(
        np.float32,
        copy=False,
    )

    difference = (
        original_matrix
        - compressed
    )

    return {
        "dtype": str(
            compressed.dtype
        ),
        "max_diff": float(
            np.abs(difference).max()
        ),
        "mean_diff": float(
            np.abs(difference).mean()
        ),
        "rmse": float(
            np.sqrt(
                np.mean(
                    difference
                    * difference
                )
            )
        ),
    }


def inspect_tiff(output_tiff):
    with tifffile.TiffFile(
        output_tiff
    ) as tif:
        page = tif.pages[0]

        sample_format = (
            page.tags.get(
                "SampleFormat"
            )
        )

        bits_per_sample = (
            page.tags.get(
                "BitsPerSample"
            )
        )

        compression = (
            page.tags.get(
                "Compression"
            )
        )

        xmp_tag = page.tags.get(
            700
        )

        description_tag = (
            page.tags.get(
                "ImageDescription"
            )
        )

        return {
            "sample_format": (
                sample_format.value
                if sample_format
                else None
            ),
            "bits_per_sample": (
                bits_per_sample.value
                if bits_per_sample
                else None
            ),
            "compression": (
                compression.value
                if compression
                else None
            ),
            "xmp_present": (
                xmp_tag is not None
            ),
            "description_present": (
                description_tag is not None
            ),
        }


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(
            f"Input folder not found: {INPUT_DIR}"
        )

    images = sorted(
        [
            path
            for path in INPUT_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower()
            in {
                ".jpg",
                ".jpeg",
            }
        ]
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

    print(
        f"Found {len(images)} image(s)."
    )
    print(
        "This is a separate compression test."
    )
    print(
        "The main converter is NOT modified."
    )

    results = []

    for index, image_path in enumerate(
        images,
        start=1,
    ):
        print()
        print(
            "=" * 70
        )
        print(
            f"[{index}/{len(images)}] {image_path.name}"
        )
        print(
            "=" * 70
        )

        temperature_matrix, radiometry_data = (
            sdk.process_image_info(
                image_path
            )
        )

        output_tiff = (
            OUTPUT_DIR
            / f"{image_path.stem}_deflate.tif"
        )

        write_compressed_tiff(
            image_path,
            output_tiff,
            temperature_matrix,
            radiometry_data,
        )

        verification = verify_pixels(
            temperature_matrix,
            output_tiff,
        )

        tags = inspect_tiff(
            output_tiff
        )

        output_size = (
            output_tiff.stat().st_size
        )

        result = {
            "filename": output_tiff.name,
            "size_bytes": output_size,
            **verification,
            **tags,
        }

        results.append(
            result
        )

        print(
            f"Saved: {output_tiff}"
        )
        print(
            f"Size: {output_size} bytes"
        )
        print(
            f"dtype: {verification['dtype']}"
        )
        print(
            f"MAX DIFF: {verification['max_diff']}"
        )
        print(
            f"MEAN DIFF: {verification['mean_diff']}"
        )
        print(
            f"RMSE: {verification['rmse']}"
        )
        print(
            f"SampleFormat: {tags['sample_format']}"
        )
        print(
            f"BitsPerSample: {tags['bits_per_sample']}"
        )
        print(
            f"Compression: {tags['compression']}"
        )
        print(
            f"XMP tag 700: "
            f"{'present' if tags['xmp_present'] else 'missing'}"
        )
        print(
            f"ImageDescription: "
            f"{'present' if tags['description_present'] else 'missing'}"
        )

    print()
    print(
        "=" * 70
    )
    print(
        "BATCH SUMMARY"
    )
    print(
        "=" * 70
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

    print(
        f"Files created: {len(results)}"
    )
    print(
        f"Pixel-perfect: {'YES' if all_exact else 'NO'}"
    )
    print(
        f"Float32: {'YES' if all_float32 else 'NO'}"
    )
    print(
        f"XMP present: {'YES' if all_xmp else 'NO'}"
    )
    print(
        f"Output folder: {OUTPUT_DIR}"
    )

    print()
    print(
        "Next step:"
    )
    print(
        "Import all generated *_deflate.tif files into a new Metashape chunk"
    )
    print(
        "and verify Latitude, Longitude, Altitude, Yaw, Pitch and Roll."
    )


if __name__ == "__main__":
    main()